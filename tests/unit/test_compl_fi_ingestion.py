"""Unit tests for the FI/DOC/COMPL readers.

``compl_fi_AAAAMM.zip`` is a 4-member ZIP partitioned by month, a closed series (``201801`` to
``201904``). The header of every member is identical in all 16 months (measured), so there is one
contract per member and no regime cut.

The oracle is the verbatim header bytes CVM publishes (``tests/fixtures/compl_fi``); every other
test builds input from the contract and is a tautology by construction.
"""

from datetime import date
from pathlib import Path
import zipfile

import pytest

from filings_cvm._internal.config.contracts import (
	COMPL_FI,
	COMPL_FI_INF,
	COMPL_FI_INF_COTST,
	COMPL_FI_PREST,
)
from filings_cvm._internal.utils.tabular_reader import ContractError, FileContract
from filings_cvm.ingestion.fi import (
	ComplFiInfCotstReader,
	ComplFiInfReader,
	ComplFiPrestReader,
	ComplFiReader,
	MetaComplFiReader,
)


VALID_CNPJ = "11.222.333/0001-81"
REF = date(2018, 6, 15)
URL = "https://dados.cvm.gov.br/dados/FI/DOC/COMPL/DADOS/compl_fi_201806.zip"
PATH_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "compl_fi"

LIST_READERS = [
	(ComplFiReader, COMPL_FI, "compl_fi", 20),
	(ComplFiInfReader, COMPL_FI_INF, "compl_fi_inf", 6),
	(ComplFiInfCotstReader, COMPL_FI_INF_COTST, "compl_fi_inf_cotst", 7),
	(ComplFiPrestReader, COMPL_FI_PREST, "compl_fi_prest", 5),
]


def _row(tuple_cols: tuple[str, ...]) -> list[str]:
	"""Build one plausible row; text columns carry accents and a leading, unbalanced quote."""
	dict_over = {
		"TP_FUNDO": "FI",
		"CNPJ_FUNDO": VALID_CNPJ,
		"CNPJ_AG_RISCO": VALID_CNPJ,
		"DT_COMPTC": "2018-06-30",
		"NM_PREST_SERV": '"ABC Administração "S.A.',
	}
	return [dict_over.get(str_col, "") for str_col in tuple_cols]


def _csv(tuple_cols: tuple[str, ...], list_rows: list[list[str]]) -> str:
	"""Serialise header + rows in CVM's ``;`` / CRLF shape."""
	return "\r\n".join([";".join(tuple_cols), *(";".join(r) for r in list_rows)]) + "\r\n"


def _patch_download(monkeypatch: pytest.MonkeyPatch, dict_members: dict[str, str]) -> list[str]:
	"""Patch the base's download boundary to write a real ZIP holding ``dict_members``."""
	list_urls: list[str] = []

	def _fake(
		str_url: str, path_dest: Path, int_timeout_s: int = 60, retry_policy: object = None
	) -> Path:
		list_urls.append(str_url)
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		with zipfile.ZipFile(path_dest, "w") as zf:
			for str_name, str_text in dict_members.items():
				zf.writestr(str_name, str_text.encode("ISO-8859-1"))
		return path_dest

	monkeypatch.setattr(
		"filings_cvm.ingestion.fi.doc.compl._base_compl_reader.download_file", _fake
	)
	return list_urls


def _all_members(str_ym: str = "201806") -> dict[str, str]:
	"""Build a full 4-member archive, one valid row per member."""
	return {
		f"{str_stem}_{str_ym}.csv": _csv(contract.tuple_required, [_row(contract.tuple_required)])
		for _, contract, str_stem, _ in LIST_READERS
	}


# ---- the pinned oracle ---------------------------------------------------------------------


@pytest.mark.parametrize(("cls_reader", "contract", "str_stem", "int_cols"), LIST_READERS)
def test_contract_matches_the_published_header(
	cls_reader: type, contract: FileContract, str_stem: str, int_cols: int
) -> None:
	"""Each contract equals the verbatim header CVM publishes for its member."""
	str_line = (PATH_FIXTURES / f"{str_stem}_header.csv").read_text(encoding="iso-8859-1")

	assert contract.tuple_required == tuple(str_line.strip().split(";"))
	assert len(contract.tuple_required) == int_cols
	assert cls_reader._CONTRACT is contract
	assert str_stem == cls_reader._MEMBER_STEM


def test_cnpj_columns_are_only_the_pure_cnpj_ones() -> None:
	"""Only ``CNPJ_FUNDO`` is a CNPJ column; ``CNPJ_AG_RISCO`` is placeholder-only (#317).

	Measured over 201801-201904, ``CNPJ_AG_RISCO`` holds one valid CNPJ in 16 months.
	"""
	for contract in (COMPL_FI, COMPL_FI_INF, COMPL_FI_INF_COTST, COMPL_FI_PREST):
		assert contract.tuple_cnpj_cols == ("CNPJ_FUNDO",)


def test_a_placeholder_only_rating_agency_cnpj_partition_reads(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""The 2019-04 shape (every ``CNPJ_AG_RISCO`` a placeholder) reads, returned as published."""
	list_cols = COMPL_FI.tuple_required
	row_full = _row(list_cols)
	list_rows = [
		[(str_ph if c == "CNPJ_AG_RISCO" else v) for c, v in zip(list_cols, row_full, strict=True)]
		for str_ph in ("00.000.000/0000-00", "11.111.111/1111-11")
	]
	dict_members = _all_members()
	dict_members["compl_fi_201806.csv"] = _csv(list_cols, list_rows)
	_patch_download(monkeypatch, dict_members)

	df_ = ComplFiReader(REF).read()

	assert df_["CNPJ_AG_RISCO"].tolist() == ["00.000.000/0000-00", "11.111.111/1111-11"]


# ---- month window --------------------------------------------------------------------------


@pytest.mark.parametrize("date_bad", [date(2017, 12, 31), date(2019, 5, 1), date(2025, 6, 1)])
def test_a_month_outside_the_series_is_refused_before_download(date_bad: date) -> None:
	"""The series is closed: any other month fails fast, naming the window."""
	with pytest.raises(ValueError, match="201801-201904"):
		ComplFiReader(date_bad)


@pytest.mark.parametrize("date_ok", [date(2018, 1, 1), date(2019, 4, 30)])
def test_the_boundary_months_are_inclusive(date_ok: date) -> None:
	"""``201801`` and ``201904`` are the first and last published months."""
	assert ComplFiReader(date_ok) is not None


def test_the_default_date_ref_is_the_last_published_month() -> None:
	"""No-argument construction must not raise on a closed series."""
	assert ComplFiPrestReader()._date_ref == date(2019, 4, 1)


# ---- read path -----------------------------------------------------------------------------


@pytest.mark.parametrize(("cls_reader", "contract", "str_stem", "int_cols"), LIST_READERS)
def test_each_reader_selects_its_own_member(
	monkeypatch: pytest.MonkeyPatch,
	cls_reader: type,
	contract: FileContract,
	str_stem: str,
	int_cols: int,
) -> None:
	"""The exact-name lookup keeps ``compl_fi`` from matching its longer siblings."""
	list_urls = _patch_download(monkeypatch, _all_members())

	df_ = cls_reader(REF).read()

	assert list_urls == [URL]
	assert list(df_.columns[:int_cols]) == list(contract.tuple_required)
	assert df_["DT_COMPTC"].iloc[0] == date(2018, 6, 30)
	assert df_["source_key"].iloc[0] == str_stem
	assert df_["url"].iloc[0] == URL


def test_text_keeps_accents_literal_quotes_and_empty_cells(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""ISO-8859-1 decodes, quotes are literal under QUOTE_NONE, empty stays empty."""
	_patch_download(monkeypatch, _all_members())

	df_ = ComplFiPrestReader(REF).read()

	assert df_["NM_PREST_SERV"].iloc[0] == '"ABC Administração "S.A.'
	assert df_["DS_SERV_PREST"].isna().iloc[0]


def test_a_member_with_a_foreign_header_raises_contract_error(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Serving the prest header under the inf member name violates the inf contract."""
	dict_members = _all_members()
	dict_members["compl_fi_inf_201806.csv"] = dict_members["compl_fi_prest_201806.csv"]
	_patch_download(monkeypatch, dict_members)

	with pytest.raises(ContractError):
		ComplFiInfReader(REF).read()


def test_path_raw_keeps_the_zip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
	"""``path_raw`` persists the untouched ZIP."""
	_patch_download(monkeypatch, _all_members())

	ComplFiReader(REF, path_raw=tmp_path).read()

	assert (tmp_path / "compl_fi_201806.zip").exists()


def test_a_missing_member_raises(monkeypatch: pytest.MonkeyPatch) -> None:
	"""An archive without the reader's member is refused."""
	dict_members = _all_members()
	del dict_members["compl_fi_prest_201806.csv"]
	_patch_download(monkeypatch, dict_members)

	with pytest.raises(ValueError):
		ComplFiPrestReader(REF).read()


# ---- META ----------------------------------------------------------------------------------


def test_the_meta_url_is_the_txt_infixed_zip() -> None:
	"""The META is ``meta_compl_fi_txt.zip``, pinned and never derived."""
	assert MetaComplFiReader._META_URL.endswith("/COMPL/META/meta_compl_fi_txt.zip")
	assert MetaComplFiReader._CONTRACT.str_source_key == "meta_compl_fi"
	assert MetaComplFiReader._MEMBER_STEM == "compl_fi"


def test_section_labels_are_asymmetric_by_design() -> None:
	"""The META's four ``section`` labels are ``compl_fi``/``inf``/``inf_cotst``/``prest``.

	``meta_compl_fi.txt`` is the bare ``_MEMBER_STEM`` so it keeps the whole stem; the other three
	reduce to their suffix. Measured from ``_section_of``, pinned so it is not silently "tidied".
	"""
	cls_reader = MetaComplFiReader()
	list_names = [
		"meta_compl_fi.txt",
		"meta_compl_fi_inf.txt",
		"meta_compl_fi_inf_cotst.txt",
		"meta_compl_fi_prest.txt",
	]

	assert [cls_reader._section_of(n) for n in list_names] == [
		"compl_fi",
		"inf",
		"inf_cotst",
		"prest",
	]


def test_a_mix_of_empty_and_valid_rating_agency_cnpj_passes(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""``CNPJ_AG_RISCO`` is partly empty in the source; empty rows must not fail the contract."""
	list_cols = COMPL_FI.tuple_required
	row_full = _row(list_cols)
	row_empty = [
		("" if c == "CNPJ_AG_RISCO" else v) for c, v in zip(list_cols, row_full, strict=True)
	]
	dict_members = _all_members()
	dict_members["compl_fi_201806.csv"] = _csv(list_cols, [row_full, row_empty])
	_patch_download(monkeypatch, dict_members)

	df_ = ComplFiReader(REF).read()

	assert df_["CNPJ_AG_RISCO"].tolist()[0] == VALID_CNPJ
	assert df_["CNPJ_AG_RISCO"].isna().tolist() == [False, True]
