"""Unit tests for the two OFERTA/DISTRIB register readers (`oferta_distribuicao.zip`).

One parameterized module covers both members: a single in-memory fixture ZIP holds the
`oferta_distribuicao` and `oferta_resolucao_160` CSVs, and each reader is asserted to select **its
own** member, coerce its date columns, and honour the shared base behaviour (no ``date_ref``,
``path_raw`` persistence, contract validation). The one non-tautological assertion is
``test_contract_matches_the_published_header``: it compares each contract against the verbatim
header bytes CVM publishes, committed under ``tests/fixtures/oferta_distribuicao/`` — the pinned
oracle. Mock the single I/O boundary (``download_file``); no network.
"""

from datetime import date
import io
from pathlib import Path
import zipfile

import pytest

from filings_cvm._internal.config.contracts import OFERTA_DISTRIBUICAO, OFERTA_RESOLUCAO_160
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.tabular_reader import ContractError, FileContract
from filings_cvm.ingestion import OfertaDistribuicaoReader, OfertaResolucao160Reader


# CNPJ valid under the repo's ASCII-48 mod-11 routine; every contract's CNPJ check accepts it.
VALID_CNPJ = "11.222.333/0001-81"

# Verbatim published headers — the oracle the contracts are pinned to.
PATH_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "oferta_distribuicao"

# The whole family. Introspection off the class attributes keeps this list from re-stating the
# members/contracts/date-columns the readers already declare.
ALL_READERS: tuple[type[IngestionReader], ...] = (
	OfertaDistribuicaoReader,
	OfertaResolucao160Reader,
)

# (fixture section, reader, contract) for the anti-tautology header check.
SECTIONS: tuple[tuple[str, type[IngestionReader], FileContract], ...] = (
	("oferta_distribuicao", OfertaDistribuicaoReader, OFERTA_DISTRIBUICAO),
	("oferta_resolucao_160", OfertaResolucao160Reader, OFERTA_RESOLUCAO_160),
)


def _value_for(cls: type[IngestionReader], str_col: str) -> str:
	"""Return a plausible source value for one column of ``cls``'s member, by name."""
	if str_col in cls._CONTRACT.tuple_cnpj_cols:  # type: ignore[attr-defined]
		return VALID_CNPJ
	if str_col in cls._DATE_COLS:  # type: ignore[attr-defined]
		return "2023-01-15"
	return "x"


def _row_for(cls: type[IngestionReader]) -> str:
	"""Build one valid CSV row for ``cls``'s member from its contract + date/cnpj columns."""
	return ";".join(_value_for(cls, c) for c in cls._CONTRACT.tuple_required)  # type: ignore[attr-defined]


def _member_csv(cls: type[IngestionReader]) -> str:
	"""Header + one valid row for ``cls``'s member."""
	str_header = ";".join(cls._CONTRACT.tuple_required)  # type: ignore[attr-defined]
	return f"{str_header}\n{_row_for(cls)}\n"


def _all_members() -> dict[str, str]:
	"""Build the full two-member fixture archive, one valid row each."""
	return {cls._MEMBER: _member_csv(cls) for cls in ALL_READERS}  # type: ignore[attr-defined]


def _zip_bytes(dict_members: dict[str, str]) -> bytes:
	"""Build an in-memory ZIP holding each ``name → csv text`` member."""
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
		"filings_cvm.ingestion.oferta.distrib._base_oferta_reader.download_file",
		_fake_download,
	)


@pytest.mark.parametrize(("str_section", "cls", "contract"), SECTIONS, ids=lambda v: str(v))
def test_contract_matches_the_published_header(
	str_section: str, cls: type[IngestionReader], contract: FileContract
) -> None:
	"""Each contract equals the verbatim header CVM publishes — the one non-tautological check.

	Parameters
	----------
	str_section : str
		The member section (``oferta_distribuicao`` / ``oferta_resolucao_160``).
	cls : type[IngestionReader]
		The reader whose contract is pinned (kept for symmetry with ``ids``).
	contract : FileContract
		The contract under test.
	"""
	str_line = (PATH_FIXTURES / f"{str_section}_header.csv").read_text("utf-8").strip()
	assert contract.tuple_required == tuple(str_line.split(";"))


def test_the_two_regimes_have_distinct_columns() -> None:
	"""The two members are different-regime tables, not a duplicated layout.

	The RCVM 160 register is keyed on requirement/status fields the historical one lacks, and the
	historical one carries offer/asset columns absent from RCVM 160. Copying one onto the other
	would ship the wrong contract, all tests green.
	"""
	set_distrib = set(OFERTA_DISTRIBUICAO.tuple_required)
	set_res160 = set(OFERTA_RESOLUCAO_160.tuple_required)

	assert "Numero_Requerimento" in set_res160 and "Numero_Requerimento" not in set_distrib
	assert "Numero_Registro_Oferta" in set_distrib and "Numero_Registro_Oferta" not in set_res160


def test_br_format_date_is_kept_as_text_not_a_date_column() -> None:
	"""``Data_deliberacao_aprovou_oferta`` is a ``DD/MM/YYYY`` date kept as ``str``, not coerced.

	The shared coercion is ISO-only (``pd.to_datetime`` with no ``dayfirst``), so treating this
	column as a date would silently swap day and month. It is required by the contract but
	deliberately **absent** from the reader's ``_DATE_COLS`` — pinned so a future change cannot
	quietly add it and corrupt the values.
	"""
	assert "Data_deliberacao_aprovou_oferta" in OFERTA_RESOLUCAO_160.tuple_required
	assert "Data_deliberacao_aprovou_oferta" not in OfertaResolucao160Reader._DATE_COLS


def test_br_format_date_survives_read_as_exact_text(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A ``DD/MM/YYYY`` value in ``Data_deliberacao_aprovou_oferta`` is returned verbatim.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	cls = OfertaResolucao160Reader
	list_cols = list(cls._CONTRACT.tuple_required)
	list_vals = [
		"02/01/2023" if c == "Data_deliberacao_aprovou_oferta" else _value_for(cls, c)
		for c in list_cols
	]
	dict_members = _all_members()
	dict_members[cls._MEMBER] = ";".join(list_cols) + "\n" + ";".join(list_vals) + "\n"
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	df_ = cls().read()

	assert df_["Data_deliberacao_aprovou_oferta"].iloc[0] == "02/01/2023"
	assert isinstance(df_["Data_deliberacao_aprovou_oferta"].iloc[0], str)


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_read_selects_its_own_member_with_all_columns(
	cls: type[IngestionReader], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Each reader returns exactly its member's columns from the shared archive.

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
	"""Every declared ISO date column becomes a pure ``date`` object.

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
		assert df_[str_col].iloc[0] == date(2023, 1, 15)


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_dtype_map_and_date_cols_partition_the_contract(cls: type[IngestionReader]) -> None:
	"""The base reader's derived dtype map and the date columns partition the contract.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	"""
	set_required = set(cls._CONTRACT.tuple_required)  # type: ignore[attr-defined]
	set_dates = set(cls._DATE_COLS)  # type: ignore[attr-defined]

	assert set_dates <= set_required
	set_text = set_required - set_dates
	assert set_text and not (set_text & set_dates)


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_reader_takes_no_reference_month(cls: type[IngestionReader]) -> None:
	"""The register is a snapshot, so no reader exposes ``date_ref``.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	"""
	import inspect

	assert "date_ref" not in set(inspect.signature(cls.__init__).parameters)
	with pytest.raises(TypeError):
		cls(date_ref=date(2025, 4, 1))  # type: ignore[call-arg]


@pytest.mark.parametrize(
	("cls", "tuple_cnpj"),
	(
		(OfertaDistribuicaoReader, ("CNPJ_Emissor", "CNPJ_Lider", "CNPJ_Ofertante")),
		(OfertaResolucao160Reader, ("CNPJ_Emissor", "CNPJ_Lider")),
	),
	ids=lambda v: str(v),
)
def test_reader_declares_its_cnpj_columns(
	cls: type[IngestionReader], tuple_cnpj: tuple[str, ...]
) -> None:
	"""Each member validates every CNPJ column the source populates.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	tuple_cnpj : tuple of str
		The CNPJ columns the member is expected to validate.
	"""
	assert cls._CONTRACT.tuple_cnpj_cols == tuple_cnpj  # type: ignore[attr-defined]


def test_meta_url_is_the_zip_not_a_txt() -> None:
	"""The META lives at a ``.zip`` — the sibling-shaped ``.txt`` guess 404s on this dataset."""
	from filings_cvm.ingestion.oferta.distrib.meta import MetaOfertaReader

	assert MetaOfertaReader._META_URL.endswith("/META/meta_oferta_distribuicao.zip")


def test_meta_section_labels_are_symmetric() -> None:
	"""Both META members share the ``oferta_`` prefix, so the sections are clean and symmetric.

	Unlike the INTERMED / COORD_OFERTA metas (whose bare-stem member forces an asymmetric
	fallback), ``_MEMBER_STEM = "oferta"`` strips the shared prefix from both, leaving
	``distribuicao`` and ``resolucao_160``.
	"""
	from filings_cvm.ingestion.oferta.distrib.meta import MetaOfertaReader

	cls_reader = MetaOfertaReader()
	assert cls_reader._section_of("meta_oferta_distribuicao.txt") == "distribuicao"
	assert cls_reader._section_of("meta_oferta_resolucao_160.txt") == "resolucao_160"


def test_read_raises_contract_error_on_missing_required_column(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Dropping a declared column from the historical member violates its contract.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	cls = OfertaDistribuicaoReader
	dict_members = _all_members()
	list_cols = [c for c in cls._CONTRACT.tuple_required if c != "Nome_Emissor"]
	dict_members[cls._MEMBER] = (
		";".join(list_cols) + "\n" + ";".join("x" for _ in list_cols) + "\n"
	)
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ContractError):
		cls().read()


def test_read_raises_value_error_when_member_absent(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A reader whose member is missing from the archive raises a clear ValueError.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _all_members()
	del dict_members[OfertaResolucao160Reader._MEMBER]
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ValueError, match="oferta_resolucao_160.csv"):
		OfertaResolucao160Reader().read()


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

	OfertaDistribuicaoReader(path_raw=path_raw).read()

	assert (path_raw / "oferta_distribuicao.zip").is_file()
	assert {p.name for p in path_raw.glob("*.csv")} == set(_all_members())


def test_read_keeps_monetary_field_as_exact_source_text(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``Valor_Total`` keeps CVM's exact decimal text — no float precision is lost on the way in.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	cls = OfertaDistribuicaoReader
	list_cols = list(cls._CONTRACT.tuple_required)
	list_vals = ["123456789.01" if c == "Valor_Total" else _value_for(cls, c) for c in list_cols]
	dict_members = _all_members()
	dict_members[cls._MEMBER] = ";".join(list_cols) + "\n" + ";".join(list_vals) + "\n"
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	df_ = cls().read()

	assert df_["Valor_Total"].iloc[0] == "123456789.01"
	assert isinstance(df_["Valor_Total"].iloc[0], str)


def test_read_rejects_wrong_argument_type(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The inherited ABCTypeCheckerMeta rejects a mistyped argument at call time.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))

	with pytest.raises(TypeError):
		OfertaDistribuicaoReader().read(int_timeout_s="nope")
