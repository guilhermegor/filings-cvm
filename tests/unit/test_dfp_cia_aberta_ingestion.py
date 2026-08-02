"""Unit tests for the CIA_ABERTA/DOC/DFP readers — all 19 members.

`dfp_cia_aberta_AAAA.zip` holds the *Demonstrações Financeiras Padronizadas*: the filing index,
eight statement types in a *consolidado* and an *individual* variant each, the share composition
and the auditor's opinion — ~1,17 million rows in 2025.

Four things carry the weight here:

1. every contract is compared against the **verbatim header bytes CVM publishes** — every other
   test builds its input from ``tuple_required`` and is therefore a tautology;
2. ⚠️ **this dataset inverts the hazard of every earlier one.** Elsewhere same-width members had
   *different* columns and copying a sibling was the bug; here sixteen statement members really do
   collapse into three column lists. The grouping is asserted **from the pinned fixtures**, because
   presuming members are identical and presuming they differ are the same mistake — neither is
   measurement;
3. ``VL_CONTA`` is money with ten decimal places and stays exact text — and ⚠️ its **scale lives in
   another column** (``ESCALA_MOEDA``), which the reader deliberately does not apply;
4. ``CD_CVM`` carries a **leading zero**, so text is load-bearing.

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
	DFP_CIA_ABERTA,
	DFP_CIA_ABERTA_BPA_CON,
	DFP_CIA_ABERTA_BPA_IND,
	DFP_CIA_ABERTA_BPP_CON,
	DFP_CIA_ABERTA_BPP_IND,
	DFP_CIA_ABERTA_COMPOSICAO_CAPITAL,
	DFP_CIA_ABERTA_DFC_MD_CON,
	DFP_CIA_ABERTA_DFC_MD_IND,
	DFP_CIA_ABERTA_DFC_MI_CON,
	DFP_CIA_ABERTA_DFC_MI_IND,
	DFP_CIA_ABERTA_DMPL_CON,
	DFP_CIA_ABERTA_DMPL_IND,
	DFP_CIA_ABERTA_DRA_CON,
	DFP_CIA_ABERTA_DRA_IND,
	DFP_CIA_ABERTA_DRE_CON,
	DFP_CIA_ABERTA_DRE_IND,
	DFP_CIA_ABERTA_DVA_CON,
	DFP_CIA_ABERTA_DVA_IND,
	DFP_CIA_ABERTA_PARECER,
	FRE_CIA_ABERTA_AUDITOR,
	FileContract,
)
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.tabular_reader import ContractError
from filings_cvm.ingestion.cia_aberta import (
	DfpCiaAbertaBpaConReader,
	DfpCiaAbertaBpaIndReader,
	DfpCiaAbertaBppConReader,
	DfpCiaAbertaBppIndReader,
	DfpCiaAbertaComposicaoCapitalReader,
	DfpCiaAbertaDfcMdConReader,
	DfpCiaAbertaDfcMdIndReader,
	DfpCiaAbertaDfcMiConReader,
	DfpCiaAbertaDfcMiIndReader,
	DfpCiaAbertaDmplConReader,
	DfpCiaAbertaDmplIndReader,
	DfpCiaAbertaDraConReader,
	DfpCiaAbertaDraIndReader,
	DfpCiaAbertaDreConReader,
	DfpCiaAbertaDreIndReader,
	DfpCiaAbertaDvaConReader,
	DfpCiaAbertaDvaIndReader,
	DfpCiaAbertaParecerReader,
	DfpCiaAbertaReader,
	MetaDfpCiaAbertaReader,
)


VALID_CNPJ = "11.222.333/0001-81"
DATE_REF = date(2025, 6, 15)
URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_2025.zip"
MODULE = "filings_cvm.ingestion.cia_aberta.doc.dfp._base_dfp_reader"
PATH_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "dfp_cia_aberta"

# A value whose scale a binary float would not survive intact — as CVM publishes it.
VL_CONTA = "2398719197.0000000000"
# CVM zero-pads the registration code; an integer type would drop the zeros.
CD_CVM = "001023"


@dataclass(frozen=True)
class DfpCase:
	"""One reader's spec: how to build it and which member it reads."""

	cls_reader: type[IngestionReader]
	cls_contract: FileContract
	str_stem: str


CASES: tuple[DfpCase, ...] = (
	DfpCase(DfpCiaAbertaReader, DFP_CIA_ABERTA, "dfp_cia_aberta"),
	DfpCase(DfpCiaAbertaBpaConReader, DFP_CIA_ABERTA_BPA_CON, "dfp_cia_aberta_BPA_con"),
	DfpCase(DfpCiaAbertaBpaIndReader, DFP_CIA_ABERTA_BPA_IND, "dfp_cia_aberta_BPA_ind"),
	DfpCase(DfpCiaAbertaBppConReader, DFP_CIA_ABERTA_BPP_CON, "dfp_cia_aberta_BPP_con"),
	DfpCase(DfpCiaAbertaBppIndReader, DFP_CIA_ABERTA_BPP_IND, "dfp_cia_aberta_BPP_ind"),
	DfpCase(DfpCiaAbertaDfcMdConReader, DFP_CIA_ABERTA_DFC_MD_CON, "dfp_cia_aberta_DFC_MD_con"),
	DfpCase(DfpCiaAbertaDfcMdIndReader, DFP_CIA_ABERTA_DFC_MD_IND, "dfp_cia_aberta_DFC_MD_ind"),
	DfpCase(DfpCiaAbertaDfcMiConReader, DFP_CIA_ABERTA_DFC_MI_CON, "dfp_cia_aberta_DFC_MI_con"),
	DfpCase(DfpCiaAbertaDfcMiIndReader, DFP_CIA_ABERTA_DFC_MI_IND, "dfp_cia_aberta_DFC_MI_ind"),
	DfpCase(DfpCiaAbertaDmplConReader, DFP_CIA_ABERTA_DMPL_CON, "dfp_cia_aberta_DMPL_con"),
	DfpCase(DfpCiaAbertaDmplIndReader, DFP_CIA_ABERTA_DMPL_IND, "dfp_cia_aberta_DMPL_ind"),
	DfpCase(DfpCiaAbertaDraConReader, DFP_CIA_ABERTA_DRA_CON, "dfp_cia_aberta_DRA_con"),
	DfpCase(DfpCiaAbertaDraIndReader, DFP_CIA_ABERTA_DRA_IND, "dfp_cia_aberta_DRA_ind"),
	DfpCase(DfpCiaAbertaDreConReader, DFP_CIA_ABERTA_DRE_CON, "dfp_cia_aberta_DRE_con"),
	DfpCase(DfpCiaAbertaDreIndReader, DFP_CIA_ABERTA_DRE_IND, "dfp_cia_aberta_DRE_ind"),
	DfpCase(DfpCiaAbertaDvaConReader, DFP_CIA_ABERTA_DVA_CON, "dfp_cia_aberta_DVA_con"),
	DfpCase(DfpCiaAbertaDvaIndReader, DFP_CIA_ABERTA_DVA_IND, "dfp_cia_aberta_DVA_ind"),
	DfpCase(
		DfpCiaAbertaComposicaoCapitalReader,
		DFP_CIA_ABERTA_COMPOSICAO_CAPITAL,
		"dfp_cia_aberta_composicao_capital",
	),
	DfpCase(DfpCiaAbertaParecerReader, DFP_CIA_ABERTA_PARECER, "dfp_cia_aberta_parecer"),
)
IDS = [case.cls_reader.__name__ for case in CASES]

# The three genuinely-shared column lists, as measured on the 2025 artifact. Stated here as the
# EXPECTED grouping so a member silently changing shape breaks a named assertion, not a count.
SHARED_SHAPES: dict[int, tuple[str, ...]] = {
	14: ("BPA_con", "BPA_ind", "BPP_con", "BPP_ind"),
	15: (
		"DFC_MD_con",
		"DFC_MD_ind",
		"DFC_MI_con",
		"DFC_MI_ind",
		"DRA_con",
		"DRA_ind",
		"DRE_con",
		"DRE_ind",
		"DVA_con",
		"DVA_ind",
	),
	16: ("DMPL_con", "DMPL_ind"),
}


def _value_for(str_col: str) -> str:
	"""Return a plausible source value for one column, by name."""
	if str_col == "CNPJ_CIA":
		return VALID_CNPJ
	if str_col == "CD_CVM":
		return CD_CVM
	if str_col.startswith("DT_"):
		return "2025-12-31"
	if str_col == "VL_CONTA":
		return VL_CONTA
	if str_col.startswith("QT_"):
		return "5730834040"
	if str_col == "ESCALA_MOEDA":
		return "MIL"
	if str_col == "ORDEM_EXERC":
		return "ÚLTIMO"
	return "x"


def _row(cls_contract: FileContract) -> list[str]:
	"""One valid row in the contract's column order."""
	return [_value_for(c) for c in cls_contract.tuple_required]


def _csv_text(list_cols: list[str], list_rows: list[list[str]]) -> str:
	"""Serialise a header + rows into the CVM ``;``-separated CSV shape."""
	return "\n".join([";".join(list_cols), *[";".join(r) for r in list_rows]]) + "\n"


def _member_row(case: DfpCase) -> list[str]:
	"""Build a valid row that **identifies its own member** through ``DENOM_CIA``.

	Sixteen of the nineteen members share only three column lists, so a reader pointed at the wrong
	member — the ``_con``/``_ind`` swap the naming invites — produces a perfectly valid frame that
	no column-based assertion can distinguish. Stamping the member stem into a column every member
	has makes that mistake visible.
	"""
	return [
		case.str_stem if str_col == "DENOM_CIA" else _value_for(str_col)
		for str_col in case.cls_contract.tuple_required
	]


def _all_members(dict_override: dict[str, str] | None = None) -> bytes:
	"""Build the archive holding every DFP member, one identifiable row each."""
	dict_members = {
		f"{case.str_stem}_2025.csv": _csv_text(
			list(case.cls_contract.tuple_required), [_member_row(case)]
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
	"""All nineteen contracts equal the verbatim headers CVM publishes — the oracle."""
	for case in CASES:
		str_line = (PATH_FIXTURES / f"{case.str_stem}_header.csv").read_text(encoding="iso-8859-1")
		assert case.cls_contract.tuple_required == tuple(str_line.strip().split(";")), (
			case.str_stem
		)
	assert len(CASES) == 19
	assert len({case.str_stem for case in CASES}) == 19


def test_the_statement_members_really_do_share_three_column_lists() -> None:
	"""⚠️ The inverted hazard — here same-width members really are identical, and it is measured.

	Every earlier dataset in this sweep taught the opposite — CRA, CRI, FCA and FRE all had members
	of equal width with *different* columns, where copying a sibling shipped a wrong contract with
	the suite green. DFP is the counter-case: the sixteen statement members carry only **three**
	distinct column lists.

	The claim is asserted against the **pinned fixtures**, not against the contracts alone, so it
	remains a statement about the source. Presuming members are identical and presuming they differ
	are the same error — only measurement settles it.
	"""
	dict_by_shape: dict[tuple[str, ...], list[str]] = {}
	for case in CASES:
		cols = tuple(
			(PATH_FIXTURES / f"{case.str_stem}_header.csv")
			.read_text(encoding="iso-8859-1")
			.strip()
			.split(";")
		)
		dict_by_shape.setdefault(cols, []).append(case.str_stem.replace("dfp_cia_aberta_", ""))

	# Nineteen members map onto six distinct lists — the three shared shapes and three singletons.
	assert len(dict_by_shape) == 6
	for int_width, tuple_members in SHARED_SHAPES.items():
		matches = [names for cols, names in dict_by_shape.items() if len(cols) == int_width]
		assert len(matches) == 1, f"width {int_width} should map to exactly one column list"
		assert tuple(sorted(matches[0])) == tuple(sorted(tuple_members)), int_width


def test_the_balance_sheet_lacks_the_period_start_date() -> None:
	"""The 14/15 difference is exactly ``DT_INI_EXERC`` — a balance sheet is a point in time.

	This is the *reason* two shapes exist, so it is asserted rather than left as a coincidence of
	column counts.
	"""
	set_bpa = set(DFP_CIA_ABERTA_BPA_CON.tuple_required)
	set_dre = set(DFP_CIA_ABERTA_DRE_CON.tuple_required)

	assert set_dre - set_bpa == {"DT_INI_EXERC"}
	assert not set_bpa - set_dre
	assert "DT_FIM_EXERC" in set_bpa
	assert "DT_INI_EXERC" not in set_bpa
	# DMPL is the 15-column shape plus the equity column.
	assert set(DFP_CIA_ABERTA_DMPL_CON.tuple_required) - set_dre == {"COLUNA_DF"}


def test_every_member_uses_the_index_naming_convention() -> None:
	"""All 19 members use ``CNPJ_CIA``/``DT_REFER`` — unlike FCA and FRE, whose satellites do not.

	FRE's satellites switch to ``CNPJ_Companhia``/``Data_Referencia`` while its index stays
	uppercase; DFP keeps one convention throughout. FRE is asserted as the live counter-example, so
	a template-minded change to either dataset fails here.
	"""
	for case in CASES:
		set_cols = set(case.cls_contract.tuple_required)
		assert {"CNPJ_CIA", "DT_REFER"} <= set_cols, case.str_stem
		assert "CNPJ_Companhia" not in set_cols, case.str_stem
		assert case.cls_contract.tuple_cnpj_cols == ("CNPJ_CIA",), case.str_stem
	# The FRE satellite is the counter-example — same portal branch, other convention.
	assert "CNPJ_Companhia" in FRE_CIA_ABERTA_AUDITOR.tuple_required
	assert "CNPJ_CIA" not in FRE_CIA_ABERTA_AUDITOR.tuple_required


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_returns_all_contract_columns(case: DfpCase, monkeypatch: pytest.MonkeyPatch) -> None:
	"""Each reader's frame carries exactly its contract's columns, plus provenance.

	Parameters
	----------
	case : DfpCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _all_members())

	df_ = case.cls_reader(date_ref=DATE_REF).read()

	assert len(df_) == 1
	assert list(df_.columns) == list(case.cls_contract.output_columns)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_coerces_every_declared_date_column(
	case: DfpCase, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Each reader coerces its own date columns, and they are exactly the ``DT_*`` ones.

	Parameters
	----------
	case : DfpCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _all_members())

	df_ = case.cls_reader(date_ref=DATE_REF).read()

	assert case.cls_reader._DATE_COLS
	# Measured on the 2025 artifact, where every DT_ column is ISO and no other column is a date.
	assert set(case.cls_reader._DATE_COLS) == {
		c for c in case.cls_contract.tuple_required if c.startswith("DT_")
	}, case.str_stem
	for str_col in case.cls_reader._DATE_COLS:
		assert isinstance(df_[str_col].iloc[0], date), f"{case.str_stem}.{str_col}"


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_selects_its_own_member(case: DfpCase, monkeypatch: pytest.MonkeyPatch) -> None:
	"""Each reader reads the member named by its own ``_MEMBER_STEM`` — not a sibling's.

	⚠️ This is the assertion the shared column lists make necessary. Because ten members carry an
	identical list, a reader pointed at the wrong file still returns a valid, correctly-typed frame
	with the right columns: no contract fails, no dtype check fails, nothing is red. Measured by
	mutation — swapping ``BPA_con``'s stem for ``BPA_ind``'s broke exactly one test, and that one
	only *incidentally* (it expects a ContractError from a deliberately broken member and the
	reader was reading the intact sibling instead). A ``DRE_con``/``DRE_ind`` swap would have
	passed the whole suite.

	Parameters
	----------
	case : DfpCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _all_members())

	df_ = case.cls_reader(date_ref=DATE_REF).read()

	assert case.str_stem == case.cls_reader._MEMBER_STEM
	assert df_["DENOM_CIA"].iloc[0] == case.str_stem


def test_read_keeps_vl_conta_as_exact_text(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``VL_CONTA`` comes back exactly as published, ten decimal places and all.

	Asserted on the **string**: a float comparison would not prove the point, because ``float()``
	compares equal to several different strings. Keeping the text is what preserves the published
	scale — ``float64`` renders this value as ``2398719197.0`` and the trailing digits are gone.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _all_members())

	df_ = DfpCiaAbertaBpaConReader(date_ref=DATE_REF).read()

	assert df_["VL_CONTA"].iloc[0] == VL_CONTA
	assert isinstance(df_["VL_CONTA"].iloc[0], str)
	assert str(float(VL_CONTA)) != VL_CONTA


def test_read_keeps_the_currency_scale_beside_the_value(monkeypatch: pytest.MonkeyPatch) -> None:
	"""⚠️ ``ESCALA_MOEDA`` is returned as published and the value is **not** rescaled.

	The scale of ``VL_CONTA`` lives in this separate column (``MIL`` / ``UNIDADE``), so a consumer
	that sums values without reading it is wrong by a factor of a thousand. Applying the scale here
	would mean the frame no longer holds what CVM published, the opposite of what this library
	job — so the reader keeps both columns and converts neither.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _all_members())

	df_ = DfpCiaAbertaBpaConReader(date_ref=DATE_REF).read()

	assert df_["ESCALA_MOEDA"].iloc[0] == "MIL"
	assert df_["VL_CONTA"].iloc[0] == VL_CONTA
	assert "ESCALA_MOEDA" in DFP_CIA_ABERTA_BPA_CON.tuple_required


def test_read_keeps_cd_cvm_leading_zero(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``CD_CVM`` arrives zero-padded (``001023``) and stays text.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _all_members())

	df_ = DfpCiaAbertaReader(date_ref=DATE_REF).read()

	assert df_["CD_CVM"].iloc[0] == CD_CVM
	assert isinstance(df_["CD_CVM"].iloc[0], str)


def test_read_accepts_a_blank_optional_column(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``TP_RELAT_AUD`` is blank on a declaration row — it stays empty, never a placeholder.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = list(DFP_CIA_ABERTA_PARECER.tuple_required)
	list_blank = ["" if c == "TP_RELAT_AUD" else _value_for(c) for c in list_cols]
	str_csv = _csv_text(list_cols, [_row(DFP_CIA_ABERTA_PARECER), list_blank])
	_patch(monkeypatch, _all_members({"dfp_cia_aberta_parecer_2025.csv": str_csv}))

	df_ = DfpCiaAbertaParecerReader(date_ref=DATE_REF).read()

	assert len(df_) == 2
	assert pd.isna(df_["TP_RELAT_AUD"].iloc[1])


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_requests_the_shared_yearly_url(
	case: DfpCase, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Every DFP reader fetches the same yearly archive, selected by ``date_ref.year`` alone.

	Parameters
	----------
	case : DfpCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_urls = _patch(monkeypatch, _all_members())

	case.cls_reader(date_ref=date(2025, 1, 1)).read()

	assert list_urls == [URL]


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_stamps_provenance(case: DfpCase, monkeypatch: pytest.MonkeyPatch) -> None:
	"""Each frame carries its own source key and the shared archive URL.

	Parameters
	----------
	case : DfpCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _all_members())

	df_ = case.cls_reader(date_ref=DATE_REF).read()

	assert df_["source_key"].iloc[0] == case.cls_contract.str_source_key
	assert df_["url"].iloc[0] == URL


def test_read_raises_contract_error_on_a_missing_column(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A member missing a required column fails before any typing is applied.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = list(DFP_CIA_ABERTA_BPA_CON.tuple_required)[:-1]
	str_csv = _csv_text(list_cols, [[_value_for(c) for c in list_cols]])
	_patch(monkeypatch, _all_members({"dfp_cia_aberta_BPA_con_2025.csv": str_csv}))

	with pytest.raises(ContractError):
		DfpCiaAbertaBpaConReader(date_ref=DATE_REF).read()


def test_read_persists_the_shared_raw_zip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
	"""``path_raw`` keeps the one archive every DFP reader shares.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided throwaway directory standing in for the bronze landing zone.
	"""
	_patch(monkeypatch, _all_members())
	path_raw = tmp_path / "bronze"

	DfpCiaAbertaParecerReader(date_ref=DATE_REF, path_raw=path_raw).read()

	assert (path_raw / "dfp_cia_aberta_2025.zip").exists()


def test_meta_url_carries_the_txt_infix() -> None:
	"""DFP's META is ``meta_dfp_cia_aberta_txt.zip``; the other three candidates 404.

	The survey predicted this spelling and, for the first time in this sub-root, the prediction
	held — which does not make the name derivable: FCA's correct form is the *no-prefix*
	``fca_cia_aberta.zip`` and IPE's is a loose ``.txt``. The URL is pinned per dataset.
	"""
	assert MetaDfpCiaAbertaReader._META_URL == (
		"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/META/meta_dfp_cia_aberta_txt.zip"
	)
	assert MetaDfpCiaAbertaReader._META_URL.endswith("_txt.zip")
	assert MetaDfpCiaAbertaReader._CONTRACT.str_source_key == "meta_dfp_cia_aberta"
