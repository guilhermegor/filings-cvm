"""Unit tests for the two CIA_ABERTA/DOC/CGVN readers (`cia_aberta/doc/cgvn/`).

`CgvnCiaAbertaReader` reads the **index** member (12 cols) and `CgvnCiaAbertaPraticasReader` the
**content** member (11 cols) of the same yearly ZIP — the VLMO shape.

Two behaviours carry the weight and both are pinned below:

1. **`Codigo_CVM` arrives zero-padded** (`001023`), so text typing is load-bearing here — an int
   cast would silently yield `1023`. `ID_Item` is hierarchical (`1.1.1`) and likewise stays text.
2. **The index uses the CamelCase convention**, unlike the sibling FCA's uppercase `CNPJ_CIA` /
   `DT_REFER` index — so this dataset must not be generalised from that one.

Every test except one builds its input from each contract's `tuple_required`, so it is a tautology.
The exception is :func:`test_contracts_match_the_published_headers`, which compares both contracts
against the **verbatim header bytes CVM publishes**.

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
	CGVN_CIA_ABERTA,
	CGVN_CIA_ABERTA_PRATICAS,
	FCA_CIA_ABERTA,
	FileContract,
)
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.tabular_reader import ContractError
from filings_cvm.ingestion.cia_aberta import (
	CgvnCiaAbertaPraticasReader,
	CgvnCiaAbertaReader,
	FcaCiaAbertaReader,
	MetaCgvnCiaAbertaReader,
)


VALID_CNPJ = "11.222.333/0001-81"
DATE_REF = date(2025, 6, 15)
URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/CGVN/DADOS/cgvn_cia_aberta_2025.zip"
MODULE = "filings_cvm.ingestion.cia_aberta.doc.cgvn._base_cgvn_reader"
PATH_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "cgvn_cia_aberta"

# Real 2025 shapes whose leading zero / hierarchy a numeric cast would destroy.
CODIGO_CVM_PADDED = "001023"
ID_ITEM_HIERARCHICAL = "1.1.1"
# The index's link is plain http and a different path from IPE/VLMO's https .../ENET/...
LINK = "http://www.rad.cvm.gov.br/ENETCONSULTA/frmDownloadDocumento.aspx?Tela=ext"


@dataclass(frozen=True)
class CgvnCase:
	"""One reader's spec: how to build it, which member it reads, and its date columns."""

	cls_reader: type[IngestionReader]
	cls_contract: FileContract
	str_stem: str


CASES: tuple[CgvnCase, ...] = (
	CgvnCase(CgvnCiaAbertaReader, CGVN_CIA_ABERTA, "cgvn_cia_aberta"),
	CgvnCase(CgvnCiaAbertaPraticasReader, CGVN_CIA_ABERTA_PRATICAS, "cgvn_cia_aberta_praticas"),
)
IDS = [case.cls_reader.__name__ for case in CASES]


def _value_for(str_col: str) -> str:
	"""Return a plausible source value for one column, by name."""
	if str_col == "CNPJ_Companhia":
		return VALID_CNPJ
	if str_col.startswith("Data_"):
		return "2025-08-25"
	if str_col == "Codigo_CVM":
		return CODIGO_CVM_PADDED
	if str_col == "ID_Item":
		return ID_ITEM_HIERARCHICAL
	if str_col == "Link_Download":
		return LINK
	if str_col == "Versao":
		return "1"
	return "x"


def _row(cls_contract: FileContract) -> list[str]:
	"""One valid row in the contract's column order."""
	return [_value_for(c) for c in cls_contract.tuple_required]


def _csv_text(list_cols: list[str], list_rows: list[list[str]]) -> str:
	"""Serialise a header + rows into the CVM ``;``-separated CSV shape."""
	return "\n".join([";".join(list_cols), *[";".join(r) for r in list_rows]]) + "\n"


def _both_members(dict_override: dict[str, str] | None = None) -> bytes:
	"""Build the two-member archive, one valid row per member unless overridden."""
	dict_members = {
		f"{case.str_stem}_2025.csv": _csv_text(
			list(case.cls_contract.tuple_required), [_row(case.cls_contract)]
		)
		for case in CASES
	}
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
	"""Both contracts equal the verbatim headers CVM publishes — the non-tautological oracle."""
	for case in CASES:
		str_line = (PATH_FIXTURES / f"{case.str_stem}_header.csv").read_text(encoding="iso-8859-1")
		assert case.cls_contract.tuple_required == tuple(str_line.strip().split(";")), (
			case.str_stem
		)
	assert len(CGVN_CIA_ABERTA.tuple_required) == 12
	assert len(CGVN_CIA_ABERTA_PRATICAS.tuple_required) == 11


def test_the_cgvn_index_uses_camelcase_unlike_the_fca_index() -> None:
	"""CGVN's index is CamelCase; FCA's is uppercase-abbreviated — FCA was the exception.

	This guards against generalising one sibling's shape onto another. Both contracts are compared
	directly so the divergence is asserted, not assumed.
	"""
	assert {"CNPJ_Companhia", "Data_Referencia", "Nome_Empresarial", "ID_Documento"} <= set(
		CGVN_CIA_ABERTA.tuple_required
	)
	assert "CNPJ_CIA" not in CGVN_CIA_ABERTA.tuple_required
	assert "DT_REFER" not in CGVN_CIA_ABERTA.tuple_required
	# ...and the sibling FCA index really does use the other convention.
	assert "CNPJ_CIA" in FCA_CIA_ABERTA.tuple_required
	assert "CNPJ_Companhia" not in FCA_CIA_ABERTA.tuple_required
	assert FcaCiaAbertaReader._DATE_COLS == ("DT_REFER", "DT_RECEB")
	assert CgvnCiaAbertaReader._DATE_COLS[0] == "Data_Referencia"


def test_read_preserves_zero_padded_codigo_cvm(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``Codigo_CVM`` keeps its leading zeros — the first place in this root where it matters.

	IPE's ``Codigo_CVM`` had no leading zeros, so text typing was merely conventional there. Here
	the real file carries ``001023``, and an int cast would silently yield ``1023``.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _both_members())

	df_ = CgvnCiaAbertaReader(date_ref=DATE_REF).read()

	assert df_["Codigo_CVM"].iloc[0] == CODIGO_CVM_PADDED
	assert isinstance(df_["Codigo_CVM"].iloc[0], str)
	assert df_["Codigo_CVM"].iloc[0].startswith("00")


def test_read_preserves_the_hierarchical_id_item(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``ID_Item`` is a hierarchical identifier (``1.1.1``), never a number.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _both_members())

	df_ = CgvnCiaAbertaPraticasReader(date_ref=DATE_REF).read()

	assert df_["ID_Item"].iloc[0] == ID_ITEM_HIERARCHICAL
	assert isinstance(df_["ID_Item"].iloc[0], str)


def test_read_returns_link_download_as_published(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The link comes back byte-for-byte, including its plain ``http`` scheme.

	CGVN's links use ``http://…/ENETCONSULTA/…`` while IPE/VLMO use ``https://…/ENET/…``. The
	reader normalises nothing and never follows the link.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_urls = _patch(monkeypatch, _both_members())

	df_ = CgvnCiaAbertaReader(date_ref=DATE_REF).read()

	assert df_["Link_Download"].iloc[0] == LINK
	assert df_["Link_Download"].iloc[0].startswith("http://")
	assert list_urls == [URL]
	assert not any("rad.cvm.gov.br" in str_url for str_url in list_urls)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_returns_all_contract_columns(
	case: CgvnCase, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Each reader's frame carries exactly its contract's columns, plus provenance.

	Parameters
	----------
	case : CgvnCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _both_members())

	df_ = case.cls_reader(date_ref=DATE_REF).read()

	assert len(df_) == 1
	assert list(df_.columns) == list(case.cls_contract.output_columns)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_coerces_its_own_date_columns(
	case: CgvnCase, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""The index has four date columns, the content member only one.

	Parameters
	----------
	case : CgvnCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _both_members())

	df_ = case.cls_reader(date_ref=DATE_REF).read()

	for str_col in case.cls_reader._DATE_COLS:
		assert isinstance(df_[str_col].iloc[0], date), f"{case.str_stem}.{str_col}"
	assert len(CgvnCiaAbertaReader._DATE_COLS) == 4
	assert len(CgvnCiaAbertaPraticasReader._DATE_COLS) == 1


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_requests_the_shared_yearly_url(
	case: CgvnCase, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Both readers fetch the same yearly archive, selected by ``date_ref.year`` alone.

	Parameters
	----------
	case : CgvnCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_urls = _patch(monkeypatch, _both_members())

	case.cls_reader(date_ref=date(2025, 1, 1)).read()

	assert list_urls == [URL]


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_stamps_provenance(case: CgvnCase, monkeypatch: pytest.MonkeyPatch) -> None:
	"""Each frame carries its own source key and the shared archive URL.

	Parameters
	----------
	case : CgvnCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _both_members())

	df_ = case.cls_reader(date_ref=DATE_REF).read()

	assert df_["source_key"].iloc[0] == case.cls_contract.str_source_key
	assert df_["url"].iloc[0] == URL
	assert pd.notna(df_["content_hash"].iloc[0])


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_raises_contract_error_on_a_missing_column(
	case: CgvnCase, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""A member missing a required column fails before any typing is applied.

	Parameters
	----------
	case : CgvnCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = list(case.cls_contract.tuple_required)[:-1]
	str_csv = _csv_text(list_cols, [[_value_for(c) for c in list_cols]])
	_patch(monkeypatch, _both_members({f"{case.str_stem}_2025.csv": str_csv}))

	with pytest.raises(ContractError):
		case.cls_reader(date_ref=DATE_REF).read()


def test_read_persists_the_shared_raw_zip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
	"""``path_raw`` keeps the one archive both readers share.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided throwaway directory standing in for the bronze landing zone.
	"""
	_patch(monkeypatch, _both_members())
	path_raw = tmp_path / "bronze"

	CgvnCiaAbertaPraticasReader(date_ref=DATE_REF, path_raw=path_raw).read()

	assert (path_raw / "cgvn_cia_aberta_2025.zip").exists()


def test_meta_url_is_the_standard_prefixed_zip() -> None:
	"""CGVN's META is the ordinary `meta_<ds>.zip`; the other three candidates 404.

	Measured: the loose `.txt`, the no-prefix `cgvn_cia_aberta.zip` (which *is* the correct
	form for the sibling FCA) and the `_txt`-infixed variant all return 404. Five datasets
	into this sub-root, five different measurements — pinned per dataset, never derived.
	"""
	assert MetaCgvnCiaAbertaReader._META_URL == (
		"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/CGVN/META/meta_cgvn_cia_aberta.zip"
	)
	assert MetaCgvnCiaAbertaReader._CONTRACT.str_source_key == "meta_cgvn_cia_aberta"
