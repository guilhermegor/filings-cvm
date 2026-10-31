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
import inspect
import io
from pathlib import Path
import zipfile

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

# A real-shaped NUP (17 digits) and text with accents and a literal quote, as the source carries.
NUP = "19957000056202631"
TEXT = 'Infração ao inciso I c/c inciso II, letra "b" ação'


def _row_for(cls: type[IngestionReader]) -> str:
	"""Build one valid CSV row for ``cls``'s member from its contract + date columns."""
	list_vals = []
	for str_col in cls._CONTRACT.tuple_required:  # type: ignore[attr-defined]
		if str_col == "NUP":
			list_vals.append(NUP)
		elif str_col in cls._DATE_COLS:  # type: ignore[attr-defined]
			list_vals.append("2020-01-15")
		else:
			list_vals.append(TEXT)
	return ";".join(list_vals)


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
		for str_name, str_text in dict_members.items():
			cls_zip.writestr(str_name, str_text.encode("ISO-8859-1"))
	return buffer.getvalue()


def _patch_download(monkeypatch: pytest.MonkeyPatch, payload: bytes) -> None:
	"""Patch the shared base reader's download_file boundary to drop ``payload``."""

	def _fake_download(
		str_url: str, path_dest: Path, int_timeout_s: int = 60, retry_policy: object = None
	) -> Path:
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		path_dest.write_bytes(payload)
		return path_dest

	monkeypatch.setattr(
		"filings_cvm.ingestion.processo.sancionador._base_processo_sancionador_reader."
		"download_file",
		_fake_download,
	)


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
def test_read_selects_its_own_member_with_all_columns(
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

	df_ = cls().read()

	assert len(df_) == 1
	assert list(df_.columns) == list(cls._CONTRACT.output_columns)  # type: ignore[attr-defined]


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_read_coerces_date_columns(
	cls: type[IngestionReader], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Every declared date column becomes a pure ``date`` object.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))

	df_ = cls().read()

	for str_col in cls._DATE_COLS:  # type: ignore[attr-defined]
		assert df_[str_col].iloc[0] == date(2020, 1, 15)


def test_date_columns_are_exactly_the_data_columns_of_each_member() -> None:
	"""The date columns are the ``Data_*`` fields — the META's three ``date`` fields, no more."""
	for cls in ALL_READERS:
		set_data = {c for c in cls._CONTRACT.tuple_required if c.startswith("Data_")}  # type: ignore[attr-defined]
		assert set(cls._DATE_COLS) == set_data  # type: ignore[attr-defined]


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_reader_takes_no_reference_month(cls: type[IngestionReader]) -> None:
	"""The dataset is a snapshot, so no reader exposes ``date_ref``.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	"""
	assert "date_ref" not in set(inspect.signature(cls.__init__).parameters)
	with pytest.raises(TypeError):
		cls(date_ref=date(2025, 4, 1))  # type: ignore[call-arg]


def test_neither_member_declares_a_cnpj_column() -> None:
	"""No column of either member holds a CNPJ/CPF, so ``tuple_cnpj_cols`` is empty by measurement.

	``Nome_Acusado`` names people but the source publishes no document number; declaring a CNPJ
	column here would make the contract check reject a legitimate file.
	"""
	assert PROCESSO_SANCIONADOR.tuple_cnpj_cols == ()
	assert PROCESSO_SANCIONADOR_ACUSADO.tuple_cnpj_cols == ()


def test_meta_url_is_the_zip_and_labels_are_asymmetric() -> None:
	"""The META is a two-member ``.zip`` whose ``section`` labels are asymmetric by design.

	``meta_processo_sancionador.txt`` carries the bare stem (no ``<stem>_`` suffix to strip) so
	the base labels it by the whole stem; its sibling reduces to ``acusado`` — as in INTERMED /
	COORD_OFERTA. Pinned so it stays a recorded source fact.
	"""
	assert MetaProcessoSancionadorReader._META_URL.endswith(
		"/PROCESSO/SANCIONADOR/META/meta_processo_sancionador.zip"
	)
	cls_reader = MetaProcessoSancionadorReader()
	assert cls_reader._section_of("meta_processo_sancionador.txt") == "processo_sancionador"
	assert cls_reader._section_of("meta_processo_sancionador_acusado.txt") == "acusado"


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


def test_read_persists_whole_archive_when_path_raw_is_given(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""With ``path_raw`` set, the ZIP and both members survive a single reader's read.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided scratch directory standing in for the bronze layer.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))
	path_raw = tmp_path / "bronze"

	ProcessoSancionadorReader(path_raw=path_raw).read()

	assert (path_raw / "processo_sancionador.zip").is_file()
	assert {p.name for p in path_raw.glob("*.csv")} == set(_all_members())


def test_read_keeps_source_text_verbatim_including_quotes_accents_and_nup(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Quotes are literal data, ISO-8859-1 accents decode, and ``NUP`` stays exact text.

	The source never uses ``"`` as a field delimiter (``letra "b"`` appears inside ``Ementa``), so
	the reader must read under ``QUOTE_NONE``; ``NUP`` is a 17-digit identifier that a numeric
	dtype would turn into an integer.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))

	df_ = ProcessoSancionadorReader().read()

	assert df_["Ementa"].iloc[0] == TEXT
	assert df_["NUP"].iloc[0] == NUP
	assert isinstance(df_["NUP"].iloc[0], str)


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
