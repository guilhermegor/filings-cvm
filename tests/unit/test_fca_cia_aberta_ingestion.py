"""Unit tests for the ten CIA_ABERTA/DOC/FCA readers (`cia_aberta/doc/fca/`).

`fca_cia_aberta_AAAA.zip` ships an index plus nine detail tables. A config table drives the shared
assertions across all ten, with dedicated tests for the three traps this dataset carries:

1. the **index member uses a different naming convention** from its own nine satellites, so a
   one-template implementation would silently break it;
2. **`departamento_acionistas` is header-only** in 2025, so it must read as an empty frame rather
   than raising — its contract declares no CNPJ column for exactly that reason;
3. the **CPF columns** (`dri.CPF_Responsavel`, `auditor.CPF_Responsavel_Tecnico`, and the mixed
   `auditor.CPF_CNPJ_Auditor`) are required columns but **never** CNPJ columns.

Every test except one builds its input from each contract's `tuple_required`, so it is a tautology.
The exception is :func:`test_contracts_match_the_published_headers`, which compares all ten
contracts against the **verbatim header bytes CVM publishes** — the only assertions here whose
expected values we did not author. The fixtures are **header-only** because two members carry CPFs.

Mock the single I/O boundary (``download_file``); no network.
"""

from dataclasses import dataclass
from datetime import date
import io
from pathlib import Path
import zipfile

import pandas as pd
import pytest

from filings_cvm._internal.config.contracts import (
	FCA_CIA_ABERTA,
	FCA_CIA_ABERTA_AUDITOR,
	FCA_CIA_ABERTA_CANAL_DIVULGACAO,
	FCA_CIA_ABERTA_DEPARTAMENTO_ACIONISTAS,
	FCA_CIA_ABERTA_DRI,
	FCA_CIA_ABERTA_ENDERECO,
	FCA_CIA_ABERTA_ESCRITURADOR,
	FCA_CIA_ABERTA_GERAL,
	FCA_CIA_ABERTA_PAIS_ESTRANGEIRO_NEGOCIACAO,
	FCA_CIA_ABERTA_VALOR_MOBILIARIO,
	FileContract,
)
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.tabular_reader import ContractError
from filings_cvm.ingestion.cia_aberta import (
	FcaCiaAbertaAuditorReader,
	FcaCiaAbertaCanalDivulgacaoReader,
	FcaCiaAbertaDepartamentoAcionistasReader,
	FcaCiaAbertaDriReader,
	FcaCiaAbertaEnderecoReader,
	FcaCiaAbertaEscrituradorReader,
	FcaCiaAbertaGeralReader,
	FcaCiaAbertaPaisEstrangeiroNegociacaoReader,
	FcaCiaAbertaReader,
	FcaCiaAbertaValorMobiliarioReader,
	MetaFcaCiaAbertaReader,
)


VALID_CNPJ = "11.222.333/0001-81"
VALID_CPF = "111.444.777-35"
DATE_REF = date(2025, 6, 15)
URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_2025.zip"
MODULE = "filings_cvm.ingestion.cia_aberta.doc.fca._base_fca_reader"
PATH_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "fca_cia_aberta"

# The member that ships with a header and no rows.
STEM_EMPTY = "fca_cia_aberta_departamento_acionistas"


@dataclass(frozen=True)
class FcaCase:
	"""One reader's spec: how to build it, which member it reads, and its date columns."""

	cls_reader: type[IngestionReader]
	cls_contract: FileContract
	str_stem: str


CASES: tuple[FcaCase, ...] = (
	FcaCase(FcaCiaAbertaReader, FCA_CIA_ABERTA, "fca_cia_aberta"),
	FcaCase(FcaCiaAbertaAuditorReader, FCA_CIA_ABERTA_AUDITOR, "fca_cia_aberta_auditor"),
	FcaCase(
		FcaCiaAbertaCanalDivulgacaoReader,
		FCA_CIA_ABERTA_CANAL_DIVULGACAO,
		"fca_cia_aberta_canal_divulgacao",
	),
	FcaCase(
		FcaCiaAbertaDepartamentoAcionistasReader,
		FCA_CIA_ABERTA_DEPARTAMENTO_ACIONISTAS,
		STEM_EMPTY,
	),
	FcaCase(FcaCiaAbertaDriReader, FCA_CIA_ABERTA_DRI, "fca_cia_aberta_dri"),
	FcaCase(FcaCiaAbertaEnderecoReader, FCA_CIA_ABERTA_ENDERECO, "fca_cia_aberta_endereco"),
	FcaCase(
		FcaCiaAbertaEscrituradorReader, FCA_CIA_ABERTA_ESCRITURADOR, "fca_cia_aberta_escriturador"
	),
	FcaCase(FcaCiaAbertaGeralReader, FCA_CIA_ABERTA_GERAL, "fca_cia_aberta_geral"),
	FcaCase(
		FcaCiaAbertaPaisEstrangeiroNegociacaoReader,
		FCA_CIA_ABERTA_PAIS_ESTRANGEIRO_NEGOCIACAO,
		"fca_cia_aberta_pais_estrangeiro_negociacao",
	),
	FcaCase(
		FcaCiaAbertaValorMobiliarioReader,
		FCA_CIA_ABERTA_VALOR_MOBILIARIO,
		"fca_cia_aberta_valor_mobiliario",
	),
)
IDS = [case.cls_reader.__name__ for case in CASES]


def _value_for(str_col: str) -> str:
	"""Return a plausible source value for one column, by name."""
	if "CPF" in str_col.upper() and "CNPJ" not in str_col.upper():
		return VALID_CPF
	if "CNPJ" in str_col.upper():
		return VALID_CNPJ
	if str_col.startswith("Data_") or str_col in ("DT_REFER", "DT_RECEB"):
		return "2025-08-25"
	return "x"


def _row(cls_contract: FileContract) -> list[str]:
	"""One valid row in the contract's column order."""
	return [_value_for(c) for c in cls_contract.tuple_required]


def _csv_text(list_cols: list[str], list_rows: list[list[str]]) -> str:
	"""Serialise a header + rows into the CVM ``;``-separated CSV shape."""
	return "\n".join([";".join(list_cols), *[";".join(r) for r in list_rows]]) + "\n"


def _all_members(dict_override: dict[str, str] | None = None) -> bytes:
	"""Build the ten-member archive, one valid row each except the header-only member."""
	dict_members: dict[str, str] = {}
	for case in CASES:
		list_cols = list(case.cls_contract.tuple_required)
		# Mirror the real artifact — departamento_acionistas ships a header and no rows.
		list_rows = [] if case.str_stem == STEM_EMPTY else [_row(case.cls_contract)]
		dict_members[f"{case.str_stem}_2025.csv"] = _csv_text(list_cols, list_rows)
	dict_members.update(dict_override or {})
	buffer = io.BytesIO()
	with zipfile.ZipFile(buffer, "w") as cls_zip:
		for str_name, str_csv in dict_members.items():
			cls_zip.writestr(str_name, str_csv.encode("ISO-8859-1"))
	return buffer.getvalue()


def _patch(monkeypatch: pytest.MonkeyPatch, bytes_payload: bytes) -> list[str]:
	"""Patch the shared base's download_file to drop ``bytes_payload``; capture requested URLs."""
	list_urls: list[str] = []

	def _fake_download(
		str_url: str, path_dest: Path, int_timeout_s: int = 60, retry_policy: object = None
	) -> Path:
		list_urls.append(str_url)
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		path_dest.write_bytes(bytes_payload)
		return path_dest

	monkeypatch.setattr(f"{MODULE}.download_file", _fake_download)
	return list_urls


def test_contracts_match_the_published_headers() -> None:
	"""All ten contracts equal the verbatim headers CVM publishes — the oracle.

	These are the only assertions in this file whose expected values we did not author.
	"""
	for case in CASES:
		str_line = (PATH_FIXTURES / f"{case.str_stem}_header.csv").read_text(encoding="iso-8859-1")
		assert case.cls_contract.tuple_required == tuple(str_line.strip().split(";")), (
			case.str_stem
		)
	# The measured shapes, pinned so a silently reshaped member is caught.
	assert [len(c.cls_contract.tuple_required) for c in CASES] == [
		9,
		15,
		7,
		23,
		26,
		21,
		24,
		26,
		7,
		18,
	]


def test_the_index_member_does_not_share_the_satellite_naming_convention() -> None:
	"""The index uses `CNPJ_CIA`/`DT_REFER`; satellites use `CNPJ_Companhia`/`Data_Referencia`.

	This is the anti-copy guard for this dataset's sharpest trap: generating all ten members from
	one template would silently produce a wrong index contract, with every other test still green.
	"""
	set_index = set(FCA_CIA_ABERTA.tuple_required)

	assert {"CNPJ_CIA", "DT_REFER", "DT_RECEB", "DENOM_CIA", "ID_DOC", "LINK_DOC"} <= set_index
	assert "CNPJ_Companhia" not in set_index
	assert "Data_Referencia" not in set_index
	# ...and the inverse holds for all nine satellites.
	for case in CASES[1:]:
		set_sat = set(case.cls_contract.tuple_required)
		assert {"CNPJ_Companhia", "Data_Referencia", "Versao", "ID_Documento"} <= set_sat, (
			case.str_stem
		)
		assert "CNPJ_CIA" not in set_sat, case.str_stem
		assert "DT_REFER" not in set_sat, case.str_stem


def test_cpf_columns_are_required_but_never_declared_as_cnpj_columns() -> None:
	"""CPF is personal data and a CPF cannot satisfy a CNPJ check — so it stays out.

	`auditor.CPF_CNPJ_Auditor` is all-CNPJ in 2025 but mixed **by name**; declaring it a CNPJ
	column would break in any year that carries a CPF. Same reasoning as CRA/CRI's
	`cedente_devedor.CNPJ`.
	"""
	assert "CPF_Responsavel" in FCA_CIA_ABERTA_DRI.tuple_required
	assert "CPF_Responsavel" not in FCA_CIA_ABERTA_DRI.tuple_cnpj_cols
	assert FCA_CIA_ABERTA_DRI.tuple_cnpj_cols == ("CNPJ_Companhia",)

	for str_col in ("CPF_CNPJ_Auditor", "CPF_Responsavel_Tecnico"):
		assert str_col in FCA_CIA_ABERTA_AUDITOR.tuple_required
		assert str_col not in FCA_CIA_ABERTA_AUDITOR.tuple_cnpj_cols
	assert FCA_CIA_ABERTA_AUDITOR.tuple_cnpj_cols == ("CNPJ_Companhia",)


def test_the_header_only_member_declares_no_cnpj_column() -> None:
	"""`departamento_acionistas` ships 0 rows, so a value-presence CNPJ check cannot hold.

	The CNPJ check requires at least one **present** valid value; on an empty frame it would fail.
	Declaring no CNPJ column is what lets a legitimately empty artifact read cleanly.
	"""
	assert FCA_CIA_ABERTA_DEPARTAMENTO_ACIONISTAS.tuple_cnpj_cols == ()
	assert "CNPJ_Companhia" in FCA_CIA_ABERTA_DEPARTAMENTO_ACIONISTAS.tuple_required
	# Every other member does declare one.
	for case in CASES:
		if case.str_stem != STEM_EMPTY:
			assert case.cls_contract.tuple_cnpj_cols, case.str_stem


def test_escriturador_declares_both_of_its_cnpj_columns() -> None:
	"""The only member with two CNPJ columns, both 100% valid in the real file."""
	assert FCA_CIA_ABERTA_ESCRITURADOR.tuple_cnpj_cols == ("CNPJ_Companhia", "CNPJ_Escriturador")


def test_reading_the_header_only_member_returns_an_empty_frame(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""The empty member reads as 0 rows with full columns — it must not raise.

	This is the test that would catch the production break: a value-presence CNPJ check on an
	empty artifact raises `ContractError`, which is why that contract declares none.
	"""
	_patch(monkeypatch, _all_members())

	df_ = FcaCiaAbertaDepartamentoAcionistasReader(date_ref=DATE_REF).read()

	assert len(df_) == 0
	assert list(df_.columns) == list(FCA_CIA_ABERTA_DEPARTAMENTO_ACIONISTAS.output_columns)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_returns_all_contract_columns(case: FcaCase, monkeypatch: pytest.MonkeyPatch) -> None:
	"""Each reader's frame carries exactly its contract's columns, plus provenance.

	Parameters
	----------
	case : FcaCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _all_members())

	df_ = case.cls_reader(date_ref=DATE_REF).read()

	assert list(df_.columns) == list(case.cls_contract.output_columns)
	assert len(df_) == (0 if case.str_stem == STEM_EMPTY else 1)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_coerces_every_declared_date_column(
	case: FcaCase, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Each reader coerces its own date columns — they differ per member (1 to 9 of them).

	Parameters
	----------
	case : FcaCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	if case.str_stem == STEM_EMPTY:
		pytest.skip("header-only member has no rows to coerce")
	_patch(monkeypatch, _all_members())

	df_ = case.cls_reader(date_ref=DATE_REF).read()

	assert case.cls_reader._DATE_COLS
	for str_col in case.cls_reader._DATE_COLS:
		assert isinstance(df_[str_col].iloc[0], date), f"{case.str_stem}.{str_col}"


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_accepts_blank_date_cells(case: FcaCase, monkeypatch: pytest.MonkeyPatch) -> None:
	"""Blank dates become ``NaT`` — several members are largely blank in the real file.

	``auditor.Data_Fim_Atuacao_Responsavel_Tecnico`` is 100% blank and ``geral`` has nine date
	columns, most partly blank; a raising coercion would break a real read.

	Parameters
	----------
	case : FcaCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	if case.str_stem == STEM_EMPTY:
		pytest.skip("header-only member has no rows to coerce")
	tuple_dates = case.cls_reader._DATE_COLS
	list_cols = list(case.cls_contract.tuple_required)
	# Blank every date column except the reference one, mirroring the real artifact.
	list_blank = ["" if c in tuple_dates[1:] else _value_for(c) for c in list_cols]
	str_csv = _csv_text(list_cols, [list_blank])
	_patch(monkeypatch, _all_members({f"{case.str_stem}_2025.csv": str_csv}))

	df_ = case.cls_reader(date_ref=DATE_REF).read()

	assert len(df_) == 1
	for str_col in tuple_dates[1:]:
		assert pd.isna(df_[str_col].iloc[0]), f"{case.str_stem}.{str_col}"


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_requests_the_shared_yearly_url(
	case: FcaCase, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""All ten readers fetch the same yearly archive, selected by ``date_ref.year`` alone.

	Parameters
	----------
	case : FcaCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_urls = _patch(monkeypatch, _all_members())

	case.cls_reader(date_ref=date(2025, 1, 1)).read()

	assert list_urls == [URL]


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_stamps_provenance(case: FcaCase, monkeypatch: pytest.MonkeyPatch) -> None:
	"""Each frame carries its own source key and the shared archive URL.

	Parameters
	----------
	case : FcaCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	if case.str_stem == STEM_EMPTY:
		pytest.skip("no rows to stamp on the header-only member")
	_patch(monkeypatch, _all_members())

	df_ = case.cls_reader(date_ref=DATE_REF).read()

	assert df_["source_key"].iloc[0] == case.cls_contract.str_source_key
	assert df_["url"].iloc[0] == URL


def test_read_raises_contract_error_on_a_missing_column(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""A member missing a required column fails before any typing is applied.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = list(FCA_CIA_ABERTA_GERAL.tuple_required)[:-1]
	str_csv = _csv_text(list_cols, [[_value_for(c) for c in list_cols]])
	_patch(monkeypatch, _all_members({"fca_cia_aberta_geral_2025.csv": str_csv}))

	with pytest.raises(ContractError):
		FcaCiaAbertaGeralReader(date_ref=DATE_REF).read()


def test_read_persists_the_shared_raw_zip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
	"""``path_raw`` keeps the one archive all ten readers share.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided throwaway directory standing in for the bronze landing zone.
	"""
	_patch(monkeypatch, _all_members())
	path_raw = tmp_path / "bronze"

	FcaCiaAbertaGeralReader(date_ref=DATE_REF, path_raw=path_raw).read()

	assert (path_raw / "fca_cia_aberta_2025.zip").exists()


def test_meta_url_has_no_meta_prefix() -> None:
	"""FCA's META archive is `fca_cia_aberta.zip` — both `meta_`-prefixed forms 404.

	Measured: `meta_fca_cia_aberta.zip` and `meta_fca_cia_aberta.txt` both return 404, while the
	sibling `CIA_ABERTA/CAD` *does* serve `meta_cad_cia_aberta.txt`. The prefix is not portal
	policy, so every Meta reader pins its own literal URL rather than deriving one.
	"""
	assert MetaFcaCiaAbertaReader._META_URL == (
		"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/META/fca_cia_aberta.zip"
	)
	assert "meta_fca" not in MetaFcaCiaAbertaReader._META_URL
	assert MetaFcaCiaAbertaReader._CONTRACT.str_source_key == "meta_fca_cia_aberta"
