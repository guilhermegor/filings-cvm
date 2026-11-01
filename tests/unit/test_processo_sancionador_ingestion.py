"""Unit tests for the two PROCESSO/SANCIONADOR readers (`processo_sancionador.zip`).

One parameterized module covers both members: a single in-memory fixture ZIP holds the
`processo_sancionador` and `acusado` CSVs, and each reader is asserted to select **its own**
member, coerce its date columns, and honour the shared base behaviour (no ``date_ref``,
``path_raw`` persistence, contract validation). The one non-tautological assertion is
``test_contract_matches_the_published_header``: it compares each contract against the verbatim
header bytes CVM publishes, committed under ``tests/fixtures/processo_sancionador/`` — the pinned
oracle. Mock the single I/O boundary (``download_file``); no network.
"""

from datetime import date
from functools import partial
import inspect
import io
from pathlib import Path
import zipfile

import pandas as pd
import pytest

from filings_cvm._internal.config.contracts import (
	PROCESSO_SANCIONADOR,
	PROCESSO_SANCIONADOR_ACUSADO,
)
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.tabular_reader import ContractError, FileContract
from filings_cvm.ingestion.processo import (
	MetaProcessoSancionadorReader,
	ProcessoSancionadorAcusadoReader,
	ProcessoSancionadorReader,
)


# Verbatim published headers — the oracle the contracts are pinned to.
PATH_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "processo_sancionador"

ALL_READERS: tuple[type[IngestionReader], ...] = (
	ProcessoSancionadorReader,
	ProcessoSancionadorAcusadoReader,
)

# (fixture file, reader, contract) for the anti-tautology header check.
SECTIONS: tuple[tuple[str, type[IngestionReader], FileContract], ...] = (
	("processo_sancionador", ProcessoSancionadorReader, PROCESSO_SANCIONADOR),
	(
		"processo_sancionador_acusado",
		ProcessoSancionadorAcusadoReader,
		PROCESSO_SANCIONADOR_ACUSADO,
	),
)

# (reader, date column) pairs, one test case each.
PAIRS_DATE_COLS = tuple((cls, c) for cls in ALL_READERS for c in cls._DATE_COLS)  # type: ignore[attr-defined]

# A real-shaped NUP (17 digits) and text with accents and a literal quote, as the source carries.
NUP = "19957000056202631"
TEXT = 'Infração ao inciso I c/c inciso II, letra "b" ação'


def _row_for(cls: type[IngestionReader]) -> str:
	"""Build one valid CSV row for ``cls``'s member from its contract + date columns."""
	dict_vals = {"NUP": NUP, **{c: "2020-01-15" for c in cls._DATE_COLS}}  # type: ignore[attr-defined]
	return ";".join(dict_vals.get(c, TEXT) for c in cls._CONTRACT.tuple_required)  # type: ignore[attr-defined]


def _member_csv(cls: type[IngestionReader]) -> str:
	"""Header + one valid row for ``cls``'s member."""
	str_header = ";".join(cls._CONTRACT.tuple_required)  # type: ignore[attr-defined]
	return f"{str_header}\r\n{_row_for(cls)}\r\n"


def _all_members() -> dict[str, str]:
	"""Build the full two-member fixture archive, one valid row each."""
	return {cls._MEMBER: _member_csv(cls) for cls in ALL_READERS}  # type: ignore[attr-defined]


def _zip_bytes(dict_members: dict[str, str]) -> bytes:
	"""Build an in-memory ZIP holding each ``name -> csv text`` member (ISO-8859-1, like CVM)."""
	buffer = io.BytesIO()
	with zipfile.ZipFile(buffer, "w") as cls_zip:
		tuple(cls_zip.writestr(n, t.encode("ISO-8859-1")) for n, t in dict_members.items())
	return buffer.getvalue()


def _fake_download(
	payload: bytes,
	str_url: str,
	path_dest: Path,
	int_timeout_s: int = 60,
	retry_policy: object = None,
) -> Path:
	"""Drop ``payload`` at ``path_dest`` in place of the network download."""
	path_dest.parent.mkdir(parents=True, exist_ok=True)
	path_dest.write_bytes(payload)
	return path_dest


def _patch_download(monkeypatch: pytest.MonkeyPatch, payload: bytes) -> None:
	"""Patch the shared base reader's download_file boundary to drop ``payload``."""
	monkeypatch.setattr(
		"filings_cvm.ingestion.processo.sancionador._base_processo_sancionador_reader."
		"download_file",
		partial(_fake_download, payload),
	)


@pytest.fixture
def df_proc(monkeypatch: pytest.MonkeyPatch) -> pd.DataFrame:
	"""Read the proceedings member from the in-memory archive."""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))
	return ProcessoSancionadorReader().read()


@pytest.mark.parametrize(("str_file", "cls", "contract"), SECTIONS, ids=lambda v: str(v))
def test_contract_matches_the_published_header(
	str_file: str, cls: type[IngestionReader], contract: FileContract
) -> None:
	"""Each contract equals the verbatim header CVM publishes — the one non-tautological check.

	Parameters
	----------
	str_file : str
		The fixture stem (``processo_sancionador`` / ``processo_sancionador_acusado``).
	cls : type[IngestionReader]
		The reader whose contract is pinned (kept for symmetry with ``ids``).
	contract : FileContract
		The contract under test.
	"""
	str_line = (PATH_FIXTURES / f"{str_file}_header.csv").read_text("utf-8").strip()
	assert contract.tuple_required == tuple(str_line.split(";"))


def test_the_two_members_have_distinct_columns_sharing_only_the_nup() -> None:
	"""The proceedings and the accused are different layouts joined only by ``NUP``.

	Copying one member's contract for the other would ship wrong columns, all tests green.
	"""
	set_proc = set(PROCESSO_SANCIONADOR.tuple_required)
	set_acus = set(PROCESSO_SANCIONADOR_ACUSADO.tuple_required)
	assert set_proc & set_acus == {"NUP"}


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_read_selects_its_own_member_columns(
	cls: type[IngestionReader], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Each reader returns exactly its member's columns from the shared archive.

	This also proves ``find_member`` selects by exact name: ``processo_sancionador.csv`` must not
	match the longer ``processo_sancionador_acusado.csv``.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))

	assert list(cls().read().columns) == list(cls._CONTRACT.output_columns)  # type: ignore[attr-defined]


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_read_returns_the_single_fixture_row(
	cls: type[IngestionReader], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Each reader returns the one row of its own member.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))

	assert len(cls().read()) == 1


@pytest.mark.parametrize(("cls", "str_col"), PAIRS_DATE_COLS, ids=lambda v: str(v))
def test_read_coerces_date_columns(
	cls: type[IngestionReader], str_col: str, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Every declared date column becomes a pure ``date`` object.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	str_col : str
		A date column of that reader.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))

	assert cls().read()[str_col].iloc[0] == date(2020, 1, 15)


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_date_columns_are_exactly_the_data_columns_of_each_member(
	cls: type[IngestionReader],
) -> None:
	"""The date columns are the ``Data_*`` fields — the META's three ``date`` fields, no more.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	"""
	set_data = {c for c in cls._CONTRACT.tuple_required if c.startswith("Data_")}  # type: ignore[attr-defined]

	assert set(cls._DATE_COLS) == set_data  # type: ignore[attr-defined]


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_reader_signature_has_no_date_ref(cls: type[IngestionReader]) -> None:
	"""The dataset is a snapshot, so no reader exposes ``date_ref``.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	"""
	assert "date_ref" not in set(inspect.signature(cls.__init__).parameters)


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_reader_rejects_a_reference_month(cls: type[IngestionReader]) -> None:
	"""Passing ``date_ref`` to a snapshot reader is a ``TypeError``.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	"""
	with pytest.raises(TypeError):
		cls(date_ref=date(2025, 4, 1))  # type: ignore[call-arg]


@pytest.mark.parametrize(
	"contract",
	(PROCESSO_SANCIONADOR, PROCESSO_SANCIONADOR_ACUSADO),
	ids=lambda c: c.str_source_key,
)
def test_member_declares_no_cnpj_column(contract: FileContract) -> None:
	"""No column holds a CNPJ/CPF, so ``tuple_cnpj_cols`` is empty by measurement.

	``Nome_Acusado`` names people but the source publishes no document number; declaring a CNPJ
	column here would make the contract check reject a legitimate file.

	Parameters
	----------
	contract : FileContract
		The contract under test.
	"""
	assert contract.tuple_cnpj_cols == ()


def test_meta_url_is_the_two_member_zip() -> None:
	"""The META is a two-member ``.zip`` (the ``.txt`` spelling is a 404)."""
	assert MetaProcessoSancionadorReader._META_URL.endswith(
		"/PROCESSO/SANCIONADOR/META/meta_processo_sancionador.zip"
	)


@pytest.mark.parametrize(
	("str_member", "str_section"),
	(
		("meta_processo_sancionador.txt", "processo_sancionador"),
		("meta_processo_sancionador_acusado.txt", "acusado"),
	),
)
def test_meta_section_labels_are_asymmetric(str_member: str, str_section: str) -> None:
	"""The bare stem has no ``<stem>_`` suffix to strip, so it is labelled by the whole stem.

	Its sibling reduces to ``acusado`` — as in INTERMED / COORD_OFERTA. Pinned so it stays a
	recorded source fact.

	Parameters
	----------
	str_member : str
		The META member name.
	str_section : str
		The expected ``section`` label.
	"""
	assert MetaProcessoSancionadorReader()._section_of(str_member) == str_section


def test_read_raises_contract_error_on_missing_required_column(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Dropping a declared column from the proceedings member violates its contract.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _all_members()
	list_cols = [c for c in PROCESSO_SANCIONADOR.tuple_required if c != "Ementa"]
	dict_members[ProcessoSancionadorReader._MEMBER] = (
		";".join(list_cols) + "\r\n" + ";".join("x" for _ in list_cols) + "\r\n"
	)
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ContractError):
		ProcessoSancionadorReader().read()


def test_read_raises_value_error_when_member_absent(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A reader whose member is missing from the archive raises a clear ValueError.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _all_members()
	del dict_members[ProcessoSancionadorAcusadoReader._MEMBER]
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ValueError, match="processo_sancionador_acusado.csv"):
		ProcessoSancionadorAcusadoReader().read()


@pytest.fixture
def path_bronze(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
	"""Read the proceedings member with ``path_raw`` set; return the bronze directory."""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))
	path_raw = tmp_path / "bronze"
	ProcessoSancionadorReader(path_raw=path_raw).read()
	return path_raw


def test_read_persists_the_zip_when_path_raw_is_given(path_bronze: Path) -> None:
	"""With ``path_raw`` set, the untouched ZIP survives the read.

	Parameters
	----------
	path_bronze : pathlib.Path
		The bronze directory populated by the read.
	"""
	assert (path_bronze / "processo_sancionador.zip").is_file()


def test_read_persists_both_members_when_path_raw_is_given(path_bronze: Path) -> None:
	"""With ``path_raw`` set, both members survive a single reader's read.

	Parameters
	----------
	path_bronze : pathlib.Path
		The bronze directory populated by the read.
	"""
	assert {p.name for p in path_bronze.glob("*.csv")} == set(_all_members())


def test_read_keeps_quotes_and_accents_verbatim(df_proc: pd.DataFrame) -> None:
	"""Quotes are literal data and ISO-8859-1 accents decode.

	The source never uses ``"`` as a field delimiter (``letra "b"`` appears inside ``Ementa``), so
	the reader must read under ``QUOTE_NONE``.

	Parameters
	----------
	df_proc : pd.DataFrame
		The proceedings frame.
	"""
	assert df_proc["Ementa"].iloc[0] == TEXT


def test_read_keeps_nup_as_exact_text(df_proc: pd.DataFrame) -> None:
	"""``NUP`` is a 17-digit identifier that a numeric dtype would turn into an integer.

	Parameters
	----------
	df_proc : pd.DataFrame
		The proceedings frame.
	"""
	assert df_proc["NUP"].iloc[0] == NUP


def test_read_rejects_wrong_argument_type(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The inherited ABCTypeCheckerMeta rejects a mistyped argument at call time.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))

	with pytest.raises(TypeError):
		ProcessoSancionadorReader().read(int_timeout_s="nope")
