"""Unit tests for the Perfil Mensal original-layout submission writer.

The oracle is the CVM page ``PadraoXMLPerfil.asp``: the expected tag order below is typed from
its XML sample (not derived from the model), and the scales from its tag descriptions.
"""

from decimal import Decimal
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET  # noqa: S405  # parses our own output only

from pydantic import ValidationError
import pytest

from filings_cvm.submission import (
	PerfilMensalOriginal,
	PerfilMensalOriginalClientCount,
	PerfilMensalOriginalDocument,
	PerfilMensalOriginalHeader,
	PerfilMensalOriginalPatrimonyDistribution,
	PerfilMensalOriginalRow,
	PerfilMensalOriginalTradingDays,
)


VALID_CNPJ = "11222333000181"
OTHER_CNPJ = "11444777000161"

# NR_* tags of NR_CLIENT, in the page's sample order.
NR_TAGS = [
	"NR_PF_PRIV_BANK",
	"NR_PF_VARJ",
	"NR_PJ_N_FINANC_PRIV_BANK",
	"NR_PJ_N_FINANC_VARJ",
	"NR_BNC_COMERC_NAC",
	"NR_PJ_CORR_DIST_NAC",
	"NR_PJ_OUTR_FINANC_NAC",
	"NR_INV_N_RES",
	"NR_ENT_AB_FC_PREV_COMPL",
	"NR_SOC_SEG_RESEG",
	"NR_SOC_CAPTLZ_ARRENDM_MERC",
	"NR_FDOS_CLUB_INV",
	"NR_COTST_DISTR_FDO",
	"NR_OUTROS_N_RELAC",
]
# PR_* tags of DISTR_PATRIM, in the page's sample order.
PR_TAGS = [
	"PR_PF_PRIV_BANK",
	"PR_PF_VARJ",
	"PR_PJ_N_FINANC_PRIV_BANK",
	"PR_PJ_N_FINANC_VARJ",
	"PR_BNC_COMERC_NAC",
	"PR_PJ_CORR_DIST_NAC",
	"PR_PJ_OUTR_FINANC_NAC",
	"PR_INV_N_RES",
	"PR_ENT_AB_FC_PREV_COMPL",
	"PR_SOC_SEG_RESEG",
	"PR_SOC_CAPTLZ_ARRENDM_MERC",
	"PR_FDOS_CLUB_INV",
	"PR_COTST_DISTR_FDO",
	"PR_OUTROS_N_RELAC",
]
# Every tag of the page's sample, depth-first, for a row with all optional tags present.
SAMPLE_TAG_ORDER = [
	"DOC_ARQ",
	"CAB_INFORM",
	"COD_DOC",
	"DT_COMPT",
	"DT_GERAC_ARQ",
	"PERFIL_MENSAL",
	"ROW_PERFIL",
	"CNPJ_FDO",
	"NR_CLIENT",
	*NR_TAGS,
	"DISTR_PATRIM",
	*PR_TAGS,
	"PERC_PL_MAIOR_COTST",
	"RESM_TEOR_VT_PROFRD",
	"JUST_SUM_VT_PROFRD",
	"PRINC_FAT_RISC",
	"DESC_PRINC_ATV_OPER_RISC",
	"PR_PRINC_ATV_OPER_RISC",
	"VAR_PERC_PL",
	"MOD_VAR_UTILIZ",
	"NR_DIAS_NEGOC",
	"ATIV_50_PERC",
	"ATIV_100_PERC",
	"APRES_LIQDZ",
	"PERC_PL_CONV_CAIXA",
	"PRAZ_MED_CART_TIT",
	"RES_DELIB",
]


def _clients() -> PerfilMensalOriginalClientCount:
	"""Build an NR_CLIENT block with every count set to one."""
	return PerfilMensalOriginalClientCount(
		**dict.fromkeys(PerfilMensalOriginalClientCount.model_fields, 1)
	)


def _distribution(value: str = "7.1") -> PerfilMensalOriginalPatrimonyDistribution:
	"""Build a DISTR_PATRIM block with every tag set to ``value``."""
	return PerfilMensalOriginalPatrimonyDistribution(
		**dict.fromkeys(PerfilMensalOriginalPatrimonyDistribution.model_fields, value)
	)


def _row(cnpj: str = VALID_CNPJ, **extra: Any) -> PerfilMensalOriginalRow:  # noqa: ANN401
	"""Build a row holding only the mandatory fields, with ``extra`` overriding or adding."""
	fields = {"perc_pl_maior_cotst": "12.3", **extra}
	return PerfilMensalOriginalRow(
		cnpj_fdo=cnpj, nr_client=_clients(), distr_patrim=_distribution(), **fields
	)


def _full_row() -> PerfilMensalOriginalRow:
	"""Build a row with every optional tag present."""
	return _row(
		resm_teor_vt_profrd="Resumo dos votos",
		just_sum_vt_profrd="Justificativa",
		princ_fat_risc="Juros",
		desc_princ_atv_oper_risc="Ativo X",
		pr_princ_atv_oper_risc="5.5",
		var_perc_pl="1.2345",
		mod_var_utiliz="2",
		nr_dias_negoc=PerfilMensalOriginalTradingDays(
			ativ_50_perc="3.5", ativ_100_perc="9", apres_liqdz="S"
		),
		perc_pl_conv_caixa="40",
		praz_med_cart_tit="11.25",
		res_delib="Deliberacoes",
	)


def _doc(*rows: PerfilMensalOriginalRow) -> PerfilMensalOriginalDocument:
	"""Wrap rows in a document with a valid header."""
	return PerfilMensalOriginalDocument(
		header=PerfilMensalOriginalHeader(dt_compt="01/2008", dt_gerac_arq="15/02/2008"),
		rows=list(rows) or [_row()],
	)


def _xml(*rows: PerfilMensalOriginalRow) -> str:
	"""Export a document to its XML string."""
	xml = PerfilMensalOriginal().export(_doc(*rows))
	assert xml is not None  # noqa: S101  # narrows the Optional return for the helper's callers
	return xml


def _tags(xml: str) -> list[str]:
	"""List the namespace-stripped tag names of a document, depth-first."""
	root = ET.fromstring(xml.encode("windows-1252"))  # noqa: S314
	return [element.tag.rpartition("}")[2] for element in root.iter()]


def _text_of(xml: str, tag: str) -> str | None:
	"""Return the text of the first ``tag`` element, ignoring the namespace."""
	root = ET.fromstring(xml.encode("windows-1252"))  # noqa: S314
	return next((e.text for e in root.iter() if e.tag.endswith(tag)), None)


def test_export_full_row_follows_the_page_sample_tag_order() -> None:
	"""A row with every optional tag emits the exact tag sequence of the CVM sample."""
	assert _tags(_xml(_full_row())) == SAMPLE_TAG_ORDER


def test_export_mandatory_row_omits_every_absent_optional_tag() -> None:
	"""Optional tags that were not given do not appear in the output at all."""
	expected = [t for t in SAMPLE_TAG_ORDER if t not in _OPTIONAL_TAGS]
	assert _tags(_xml()) == expected


_OPTIONAL_TAGS = {
	"RESM_TEOR_VT_PROFRD",
	"JUST_SUM_VT_PROFRD",
	"PRINC_FAT_RISC",
	"DESC_PRINC_ATV_OPER_RISC",
	"PR_PRINC_ATV_OPER_RISC",
	"VAR_PERC_PL",
	"MOD_VAR_UTILIZ",
	"NR_DIAS_NEGOC",
	"ATIV_50_PERC",
	"ATIV_100_PERC",
	"APRES_LIQDZ",
	"PERC_PL_CONV_CAIXA",
	"PRAZ_MED_CART_TIT",
	"RES_DELIB",
}


def test_export_header_carries_no_versao_tag() -> None:
	"""The original page's CAB_INFORM has COD_DOC, DT_COMPT, DT_GERAC_ARQ and nothing else."""
	assert "VERSAO" not in _tags(_xml())


def test_export_declares_windows_1252_and_the_urn_perf_namespace() -> None:
	"""The prolog and the root element are the page's, verbatim."""
	head = _xml().splitlines()[:2]
	assert head == ['<?xml version="1.0" encoding="windows-1252"?>', '<DOC_ARQ xmlns="urn:perf">']


def test_export_cod_doc_is_forty() -> None:
	"""COD_DOC is 40 for the Perfil Mensal, without leading zeros."""
	assert _text_of(_xml(), "COD_DOC") == "40"


@pytest.mark.parametrize(
	("tag", "kwargs", "expected"),
	[
		("PERC_PL_MAIOR_COTST", {}, "12,3"),
		("PR_PRINC_ATV_OPER_RISC", {"pr_princ_atv_oper_risc": "5"}, "5,0"),
		("VAR_PERC_PL", {"var_perc_pl": "1.2"}, "1,2000"),
		("PERC_PL_CONV_CAIXA", {"perc_pl_conv_caixa": "40"}, "40,0"),
		("PRAZ_MED_CART_TIT", {"praz_med_cart_tit": "11.25"}, "11,2500"),
	],
)
def test_export_decimals_use_comma_and_the_pages_scale(
	tag: str, kwargs: dict[str, str], expected: str
) -> None:
	"""Decimals render with a comma at the scale the page states."""
	assert _text_of(_xml(_row(**kwargs)), tag) == expected


@pytest.mark.parametrize(
	("tag", "kwargs", "expected"),
	[
		("PERC_PL_MAIOR_COTST", {"perc_pl_maior_cotst": "12.99"}, "12,9"),
		("VAR_PERC_PL", {"var_perc_pl": "1.23459"}, "1,2345"),
		("PR_PRINC_ATV_OPER_RISC", {"pr_princ_atv_oper_risc": "5.99"}, "5,9"),
	],
)
def test_export_excess_precision_is_truncated_never_rounded(
	tag: str, kwargs: dict[str, str], expected: str
) -> None:
	"""A value past the page's scale is cut toward zero."""
	row = _row(**kwargs)
	assert _text_of(_xml(row), tag) == expected


def test_export_trading_days_use_four_decimals() -> None:
	"""ATIV_50_PERC and ATIV_100_PERC carry 4 decimals."""
	days = PerfilMensalOriginalTradingDays(ativ_50_perc="3.5", ativ_100_perc="9")
	assert _text_of(_xml(_row(nr_dias_negoc=days)), "ATIV_100_PERC") == "9,0000"


def test_export_escapes_markup_in_free_text() -> None:
	"""Free text is XML-escaped, so it cannot inject tags."""
	xml = _xml(_row(res_delib="a < b & c"))
	assert _text_of(xml, "RES_DELIB") == "a < b & c"


def test_export_strips_the_cnpj_mask() -> None:
	"""A masked CNPJ is stored and emitted bare."""
	assert _text_of(_xml(_row(cnpj="11.222.333/0001-81")), "CNPJ_FDO") == VALID_CNPJ


def test_export_one_row_block_per_fund() -> None:
	"""Each fund gets its own ROW_PERFIL, in input order."""
	xml = _xml(_row(), _row(OTHER_CNPJ))
	assert xml.count("<ROW_PERFIL>") == 2


def test_export_to_path_writes_windows_1252_bytes(tmp_path: Path) -> None:
	"""The file is windows-1252: accented text is one byte, not UTF-8's two."""
	out = tmp_path / "perfil.xml"
	PerfilMensalOriginal().export(_doc(_row(res_delib="Deliberação")), output_path=str(out))
	assert "Deliberação".encode("windows-1252") in out.read_bytes()


def test_export_to_path_returns_none(tmp_path: Path) -> None:
	"""Writing to a path returns None, per the SubmissionWriter port."""
	out = tmp_path / "perfil.xml"
	assert PerfilMensalOriginal().export(_doc(), output_path=str(out)) is None


def test_export_to_path_matches_the_returned_string(tmp_path: Path) -> None:
	"""File and string output are the same document."""
	out = tmp_path / "perfil.xml"
	doc = _doc(_full_row())
	PerfilMensalOriginal().export(doc, output_path=str(out))
	assert out.read_bytes().decode("windows-1252") == PerfilMensalOriginal().export(doc)


@pytest.mark.parametrize(
	"kwargs",
	[
		{"cnpj": "11222333000180"},  # bad check digit
		{"perc_pl_maior_cotst": "100.1"},  # above the page's maximum of 100
		{"perc_pl_conv_caixa": "100.1"},
		{"mod_var_utiliz": "4"},  # only "1", "2", "3"
		{"praz_med_cart_tit": "12345.0"},  # more than 4 integer digits
		{"pr_princ_atv_oper_risc": "123456789.0"},  # more than 7 integer digits
		{"var_perc_pl": "12345678901.0"},  # more than 10 integer digits
		{"princ_fat_risc": "x" * 401},  # 400-character limit
		{"res_delib": "x" * 4001},  # 4000-character limit
		{"resm_teor_vt_profrd": "x" * 4001},
		{"just_sum_vt_profrd": "x" * 4001},
		{"res_delib": "bad \x00 char"},  # control character
		{"res_delib": "emoji \U0001f600"},  # not windows-1252 encodable
	],
)
def test_row_rejects_values_outside_the_page(kwargs: dict[str, str]) -> None:
	"""Values the page forbids fail at construction."""
	with pytest.raises(ValidationError):
		_row(**kwargs)


def test_row_rejects_a_negative_client_count() -> None:
	"""NR_* are non-negative integers."""
	with pytest.raises(ValidationError):
		PerfilMensalOriginalClientCount(
			**{**dict.fromkeys(PerfilMensalOriginalClientCount.model_fields, 1), "nr_pf_varj": -1}
		)


def test_row_rejects_a_percentage_above_one_hundred_in_distr_patrim() -> None:
	"""PR_* have a maximum of 100."""
	with pytest.raises(ValidationError):
		_distribution("100.1")


def test_distr_patrim_requires_every_tag() -> None:
	"""The page marks DISTR_PATRIM mandatory, with all 14 tags."""
	fields = dict.fromkeys(PerfilMensalOriginalPatrimonyDistribution.model_fields, "1")
	del fields["pr_fdos_club_inv"]
	with pytest.raises(ValidationError):
		PerfilMensalOriginalPatrimonyDistribution(**fields)


def test_client_count_rejects_a_v4_only_tag() -> None:
	"""NR_REG_PREV_SERV_PUB exists in V4 but not in the original layout."""
	fields = dict.fromkeys(PerfilMensalOriginalClientCount.model_fields, 1)
	with pytest.raises(ValidationError):
		PerfilMensalOriginalClientCount(**fields, nr_reg_prev_serv_pub=1)


def test_row_requires_distr_patrim() -> None:
	"""A row without DISTR_PATRIM is rejected."""
	with pytest.raises(ValidationError):
		PerfilMensalOriginalRow(cnpj_fdo=VALID_CNPJ, nr_client=_clients(), perc_pl_maior_cotst="1")  # type: ignore[call-arg]


@pytest.mark.parametrize(
	"kwargs",
	[
		{"ativ_50_perc": "1"},  # 100% missing
		{"ativ_100_perc": "1"},  # 50% missing
		{},  # empty block
		{"ativ_50_perc": "12345", "ativ_100_perc": "1"},  # more than 4 integer digits
	],
)
def test_trading_days_rejects_what_the_page_forbids(kwargs: dict[str, str]) -> None:
	"""The 50%/100% tags come together, and an empty block is omitted."""
	with pytest.raises(ValidationError):
		PerfilMensalOriginalTradingDays(**kwargs)


def test_trading_days_accepts_the_liquidity_flag_alone() -> None:
	"""APRES_LIQDZ may stand alone."""
	assert PerfilMensalOriginalTradingDays(apres_liqdz="N").apres_liqdz == "N"


def test_trading_days_rejects_a_liquidity_flag_other_than_s_or_n() -> None:
	"""APRES_LIQDZ is "S" or "N"."""
	with pytest.raises(ValidationError):
		PerfilMensalOriginalTradingDays(apres_liqdz="X")


@pytest.mark.parametrize(
	("dt_compt", "dt_gerac_arq"),
	[
		("2008-01", "15/02/2008"),
		("13/2008", "15/02/2008"),
		("01/2008", "2008-02-15"),
		("01/2008", "31/02/2008"),
	],
)
def test_header_rejects_malformed_dates(dt_compt: str, dt_gerac_arq: str) -> None:
	"""DT_COMPT is MM/AAAA and DT_GERAC_ARQ is a real DD/MM/AAAA date."""
	with pytest.raises(ValidationError):
		PerfilMensalOriginalHeader(dt_compt=dt_compt, dt_gerac_arq=dt_gerac_arq)


def test_header_rejects_another_cod_doc() -> None:
	"""COD_DOC is fixed at 40."""
	with pytest.raises(ValidationError):
		PerfilMensalOriginalHeader(cod_doc=41, dt_compt="01/2008", dt_gerac_arq="15/02/2008")


def test_header_rejects_a_versao_field() -> None:
	"""The original layout has no VERSAO."""
	with pytest.raises(ValidationError):
		PerfilMensalOriginalHeader(dt_compt="01/2008", dt_gerac_arq="15/02/2008", versao="1.0")  # type: ignore[call-arg]


def test_document_rejects_a_fund_twice() -> None:
	"""One ROW_PERFIL per fund in a file."""
	with pytest.raises(ValidationError):
		_doc(_row(), _row())


def test_document_requires_at_least_one_row() -> None:
	"""An empty PERFIL_MENSAL is rejected."""
	with pytest.raises(ValidationError):
		PerfilMensalOriginalDocument(
			header=PerfilMensalOriginalHeader(dt_compt="01/2008", dt_gerac_arq="15/02/2008"),
			rows=[],
		)


def test_decimal_types_stay_decimal() -> None:
	"""Quantized fields are Decimal, never float."""
	assert isinstance(_full_row().var_perc_pl, Decimal)
