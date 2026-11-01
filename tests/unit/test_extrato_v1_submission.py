"""Unit tests for the Extrato V1 submission writer (tags typed from PadraoXMLInfExtrato450.asp)."""

import contextlib
from decimal import Decimal
from functools import reduce
import operator
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET  # noqa: S405  # parses our own output in tests

from pydantic import ValidationError
import pytest

from filings_cvm.submission import (
	ExtratoV1,
	ExtratoV1Document,
	ExtratoV1Header,
	ExtratoV1Row,
)


_NS = "{urn:extr}"
_CNPJ = "11222333000181"

# Tag lists typed from the page's sample file, in its order.
HEADER_TAGS = ["COD_DOC", "VERSAO", "DT_GERAC_ARQ"]
ROW_TAGS = [
	"CNPJ_FDO",
	"BASE_INFORM_FORM",
	"COTA_MERC_SECUND",
	"COD_DISTR_FDO",
	"SERV_ATEND_COTISTA",
	"CORRET_MESMO_GRP_ADM",
	"COD_POLIT_INVEST",
	"DS_RESUMO_POLIT",
	"QT_DIA_DIVULG_CART",
	"PROSP_POLIT_INVEST_TAXA_ADM",
	"VL_APLIC_MIN",
	"VL_MOVIM_MIN",
	"VL_SALDO_MIN",
	"COD_COTA_PATRIM_LIQ",
	"COD_COTA_ENTR",
	"QT_DIA_CONV_COTA",
	"QT_DIA_PAGAM_COTA",
	"RESG_COTAS",
	"TX_ADM",
	"TX_PERFM",
	"TX_INGRESSO",
	"TX_SAIDA",
	"OPER_DERIV",
	"DERIV_PROT_CART",
	"RESTR_CONTRP_ADM",
	"RESTR_CONTRP_TESOUR",
	"AVAL_RISCO_MERC",
	"RISCO_MERC",
	"OPER_PATRIM_LIQ",
	"ATIV_EXTER",
	"LIM_CIA_ABERTA",
	"LIM_TITPUB",
	"LIM_OPER_COMPROM",
	"LIM_APLIC_OPER_COMPOM",
	"LIM_FDO_INVEST",
	"LIM_OUTRO_FDO_INVEST",
	"LIM_CREPRIV",
	"LIM_INST_FIN",
	"LIM_APLIC_CIA_ABERTA",
	"LIM_MESMO_FDO_INVEST",
	"LIM_APLIC_PF_PJ",
	"LIM_TIT_ADM",
	"LIM_FDO_ADM",
	"LIM_EMPREST_ACOES",
	"LIM_EMPREST_TITPUB",
]
# Inner tags of the blocks, typed from the same sample.
BLOCK_TAGS = {
	"BASE_INFORM_FORM": ["DT_ASSEMB", "DT_VIGOR_INFORM", "DT_PROSP"],
	"COTA_MERC_SECUND": ["COTA_NEGOC_MERC_SECUND", "COD_MERC_SECUND"],
	"SERV_ATEND_COTISTA": [
		"TEL_ATEND_COTISTA",
		"DS_ENDER",
		"DS_EMAIL",
		"DS_WEB",
		"DS_NOME_RESP",
	],
	"RESG_COTAS": ["CARENCIA_RESG_COTAS", "DIAS_RESG_COTAS"],
	"TX_PERFM": ["COBRA_TX_PERFM", "CALC_TX_PERFM", "PRAZO_APROP", "PRAZO_PAGAM"],
	"TX_INGRESSO": ["COBRA_TX_INGRESSO", "PR_TX_INGRESSO"],
	"TX_SAIDA": ["COBRA_TX_SAIDA", "VL_FIXO_TX_SAIDA"],
	"OPER_DERIV": ["REALIZ_OPER_DERIV", "PR_MAX_OPER_DERIV"],
	"RISCO_MERC": ["EXP_RISCO_MERC", "DS_RISCO_MERC"],
	"OPER_PATRIM_LIQ": ["REALIZA_OPER_PATRIM_LIQ", "QT_OPER_PATRIM_LIQ"],
	"ATIV_EXTER": ["INVEST_EXTERIOR", "HORAR_FECH_MERC", "PR_MAX_APLIC_ATIV_EXTER"],
	"LIM_CIA_ABERTA": ["PR_MIN_CIA_ABERTA", "PR_MAX_CIA_ABERTA"],
	"LIM_TITPUB": ["PR_MIN_TITPUB", "PR_MAX_TITPUB"],
	"LIM_EMPREST_ACOES": ["PR_MIN_EMPREST_ACOES", "PR_MAX_EMPREST_ACOES"],
	"LIM_EMPREST_TITPUB": ["PR_MIN_EMPREST_TITPUB", "PR_MAX_EMPREST_TITPUB"],
}
CALC_TAGS = ["VL_TX_PERFM", "COD_PARAM_TX_PERFM", "PR_IND_REFER", "PR_CUPOM", "INFO_ADICIONAL"]
# Single-tag limit blocks: (block, tag).
LIMIT_TAGS = {
	"LIM_OPER_COMPROM": "PR_MAX_OPER_COMPROM",
	"LIM_APLIC_OPER_COMPOM": "PR_MAX_APLIC_OPER_COMPOM",
	"LIM_FDO_INVEST": "PR_MAX_APLIC_FDO_INVEST",
	"LIM_OUTRO_FDO_INVEST": "PR_MAX_APLIC_OUTRO_FDO_INVEST",
	"LIM_CREPRIV": "PR_MAX_APLIC_CREPRIV",
	"LIM_INST_FIN": "PR_MAX_INST_FIN",
	"LIM_APLIC_CIA_ABERTA": "PR_MAX_APLIC_CIA_ABERTA",
	"LIM_MESMO_FDO_INVEST": "PR_MAX_APLIC_MESMO_FDO_INVEST",
	"LIM_APLIC_PF_PJ": "PR_MAX_APLIC_PF_PJ",
	"LIM_TIT_ADM": "PR_MAX_TIT_ADM",
	"LIM_FDO_ADM": "PR_MAX_FDO_ADM",
}


def _row_head() -> dict[str, Any]:
	"""Build the first half of a valid row.

	Returns
	-------
	dict[str, Any]
		Row keyword arguments up to the service contact.
	"""
	return {
		"cnpj_fdo": _CNPJ,
		"base_inform_form": {
			"dt_assemb": "01/02/2020",
			"dt_vigor_inform": "02/02/2020",
			"dt_prosp": "03/02/2020",
		},
		"cota_merc_secund": {"cota_negoc_merc_secund": "S", "cod_merc_secund": 1},
		"cod_distr_fdo": 2,
		"serv_atend_cotista": {
			"tel_atend_cotista": {"nr_ddd": "11", "nr_tel": "30001234"},
			"ds_ender": "Rua A, 1",
			"ds_email": "a@b.com",
			"ds_web": "www.b.com",
			"ds_nome_resp": "Maria",
		},
	}


def _row_tail() -> dict[str, Any]:
	"""Build the second half of a valid row.

	Returns
	-------
	dict[str, Any]
		Row keyword arguments from the first flag onwards.
	"""
	return {
		"corret_mesmo_grp_adm": "N",
		"cod_polit_invest": 1,
		"ds_resumo_polit": "Resumo da política",
		"qt_dia_divulg_cart": 30,
		"prosp_polit_invest_taxa_adm": "S",
		"vl_aplic_min": "100.50",
		"vl_movim_min": "10",
		"vl_saldo_min": "0",
		"cod_cota_patrim_liq": 1,
		"cod_cota_entr": 6,
		"qt_dia_conv_cota": 1,
		"qt_dia_pagam_cota": 2,
		"resg_cotas": {"carencia_resg_cotas": "S", "dias_resg_cotas": 90},
		"tx_adm": "2.5",
		"tx_perfm": {
			"cobra_tx_perfm": "S",
			"calc_tx_perfm": {
				"vl_tx_perfm": "20",
				"cod_param_tx_perfm": 4,
				"pr_ind_refer": "100",
				"pr_cupom": "6",
			},
			"prazo_aprop": 180,
			"prazo_pagam": {"vl_prazo_pagam": 6, "ds_prazo_pagam": "M"},
		},
		"tx_ingresso": {"cobra_tx_ingresso": "S", "pr_tx_ingresso": "1.5"},
		"tx_saida": {"cobra_tx_saida": "S", "vl_fixo_tx_saida": "10.5"},
		"oper_deriv": {"realiz_oper_deriv": "S", "pr_max_oper_deriv": "20"},
		"deriv_prot_cart": "N",
		"restr_contrp_adm": "S",
		"restr_contrp_tesour": "S",
		"aval_risco_merc": "S",
		"risco_merc": {"exp_risco_merc": "S", "ds_risco_merc": "VaR 2%"},
		"oper_patrim_liq": {"realiza_oper_patrim_liq": "S", "qt_oper_patrim_liq": "1.25"},
		"ativ_exter": {
			"invest_exterior": "S",
			"horar_fech_merc": "18:00",
			"pr_max_aplic_ativ_exter": "10",
		},
		"lim_cia_aberta": {"pr_min_cia_aberta": "1", "pr_max_cia_aberta": "50"},
		"lim_titpub": {"pr_min_titpub": "0", "pr_max_titpub": "100"},
		"lim_oper_comprom": {"pr_max_oper_comprom": "10"},
		"lim_aplic_oper_compom": {"pr_max_aplic_oper_compom": "11"},
		"lim_fdo_invest": {"pr_max_aplic_fdo_invest": "12"},
		"lim_outro_fdo_invest": {"pr_max_aplic_outro_fdo_invest": "13"},
		"lim_crepriv": {"pr_max_aplic_crepriv": "14"},
		"lim_inst_fin": {"pr_max_inst_fin": "15"},
		"lim_aplic_cia_aberta": {"pr_max_aplic_cia_aberta": "16"},
		"lim_mesmo_fdo_invest": {"pr_max_aplic_mesmo_fdo_invest": "17"},
		"lim_aplic_pf_pj": {"pr_max_aplic_pf_pj": "18"},
		"lim_tit_adm": {"pr_max_tit_adm": "19"},
		"lim_fdo_adm": {"pr_max_fdo_adm": "20"},
		"lim_emprest_acoes": {"pr_min_emprest_acoes": "1", "pr_max_emprest_acoes": "2"},
		"lim_emprest_titpub": {"pr_min_emprest_titpub": "3", "pr_max_emprest_titpub": "4"},
	}


def _row(**over: Any) -> dict[str, Any]:  # noqa: ANN401
	"""Build a fully populated valid row, overridden per test.

	Parameters
	----------
	**over : Any
		Fields to replace.

	Returns
	-------
	dict[str, Any]
		Row keyword arguments.
	"""
	base = {**_row_head(), **_row_tail()}
	return {**base, **over}


def _doc(**over: Any) -> ExtratoV1Document:  # noqa: ANN401
	"""Build a one-row document.

	Parameters
	----------
	**over : Any
		Row fields to replace.

	Returns
	-------
	ExtratoV1Document
		The validated document.
	"""
	return ExtratoV1Document(
		header=ExtratoV1Header(dt_gerac_arq="31/10/2026"),
		rows=[ExtratoV1Row(**_row(**over))],
	)


def _parse(**over: Any) -> ET.Element:  # noqa: ANN401
	"""Export a document and return the parsed root.

	Parameters
	----------
	**over : Any
		Row fields to replace.

	Returns
	-------
	ET.Element
		The ``DOC_ARQ`` root.
	"""
	return ET.fromstring(ExtratoV1().export(_doc(**over)).split("?>", 1)[1])  # noqa: S314


def _row_el(**over: Any) -> ET.Element:  # noqa: ANN401
	"""Return the ``ROW_EXTRATO`` element of an export.

	Parameters
	----------
	**over : Any
		Row fields to replace.

	Returns
	-------
	ET.Element
		The row element.
	"""
	return _parse(**over).find(f"{_NS}EXTRATO_FUNDO/{_NS}ROW_EXTRATO")


def _tags(element: ET.Element) -> list[str]:
	"""List the child tag names of an element without the namespace.

	Parameters
	----------
	element : ET.Element
		The parent.

	Returns
	-------
	list[str]
		Child names in document order.
	"""
	return [child.tag.removeprefix(_NS) for child in element]


def test_export_declaration_is_windows_1252() -> None:
	"""The prolog names windows-1252, as the page's sample does."""
	assert ExtratoV1().export(_doc()).startswith('<?xml version="1.0" encoding="windows-1252"?>')


def test_export_root_namespace_is_urn_extr() -> None:
	"""The root is DOC_ARQ in the urn:extr namespace."""
	assert _parse().tag == f"{_NS}DOC_ARQ"


def test_export_header_tags_and_fixed_values() -> None:
	"""The header carries the three tags in order."""
	assert _tags(_parse().find(f"{_NS}CAB_INFORM")) == HEADER_TAGS


@pytest.mark.parametrize(("tag", "text"), [("COD_DOC", "41"), ("VERSAO", "1.0")])
def test_header_fixed_values(tag: str, text: str) -> None:
	"""COD_DOC is 41 and VERSAO is 1.0 (the page's values)."""
	assert _parse().find(f"{_NS}CAB_INFORM/{_NS}{tag}").text == text


def test_row_tags_follow_the_sample_order() -> None:
	"""A fully populated row emits every tag of the sample, in its order."""
	assert _tags(_row_el()) == ROW_TAGS


@pytest.mark.parametrize("block", sorted(BLOCK_TAGS))
def test_block_tags_follow_the_sample_order(block: str) -> None:
	"""Each multi-tag block emits its children in the sample's order."""
	assert _tags(_row_el().find(f"{_NS}{block}")) == BLOCK_TAGS[block]


def test_calc_tx_perfm_tags_follow_the_sample_order() -> None:
	"""The performance-fee calculation emits its five tags in order."""
	row = _row()
	row["tx_perfm"]["calc_tx_perfm"]["info_adicional"] = "texto livre"
	element = ET.fromstring(  # noqa: S314
		ExtratoV1()
		.export(
			ExtratoV1Document(
				header=ExtratoV1Header(dt_gerac_arq="31/10/2026"),
				rows=[ExtratoV1Row(**row)],
			)
		)
		.split("?>", 1)[1]
	)
	assert _tags(element.find(f".//{_NS}CALC_TX_PERFM")) == CALC_TAGS


@pytest.mark.parametrize(("block", "tag"), sorted(LIMIT_TAGS.items()))
def test_single_tag_limit_blocks(block: str, tag: str) -> None:
	"""Each single-limit block carries the sample's tag."""
	assert _tags(_row_el().find(f"{_NS}{block}")) == [tag]


@pytest.mark.parametrize(
	("field", "tags"),
	[
		("tx_ingresso", ["COBRA_TX_INGRESSO", "VL_FIXO_TX_INGRESSO", "PR_TX_INGRESSO"]),
		("tx_saida", ["COBRA_TX_SAIDA", "VL_FIXO_TX_SAIDA", "PR_TX_SAIDA"]),
	],
)
def test_fee_models_declare_the_sample_tag_order(field: str, tags: list[str]) -> None:
	"""A fee takes one amount at a time, so the full order is pinned on the model."""
	model = ExtratoV1Row.model_fields[field].annotation
	assert [name.upper() for name in model.model_fields] == tags


def test_tel_atend_cotista_tags() -> None:
	"""The phone block holds DDD then number."""
	element = _row_el().find(f"{_NS}SERV_ATEND_COTISTA/{_NS}TEL_ATEND_COTISTA")
	assert _tags(element) == ["NR_DDD", "NR_TEL"]


def test_prazo_pagam_tags() -> None:
	"""The payment term holds value then unit."""
	element = _row_el().find(f"{_NS}TX_PERFM/{_NS}PRAZO_PAGAM")
	assert _tags(element) == ["VL_PRAZO_PAGAM", "DS_PRAZO_PAGAM"]


@pytest.mark.parametrize(
	("path", "text"),
	[
		("VL_APLIC_MIN", "100,50"),
		("VL_MOVIM_MIN", "10,00"),
		("TX_ADM", "2,5000"),
		("OPER_PATRIM_LIQ/QT_OPER_PATRIM_LIQ", "1,25"),
		("TX_SAIDA/VL_FIXO_TX_SAIDA", "10,50"),
		("TX_INGRESSO/PR_TX_INGRESSO", "1,5000"),
		("LIM_CIA_ABERTA/PR_MAX_CIA_ABERTA", "50,0000"),
	],
)
def test_decimal_scales_and_comma_separator(path: str, text: str) -> None:
	"""Money takes 2 places, percentages 4, question 34 takes 2; the separator is a comma."""
	element = reduce(lambda el, part: el.find(f"{_NS}{part}"), path.split("/"), _row_el())
	assert element.text == text


def test_cnpj_is_emitted_without_leading_zeros() -> None:
	"""The page: dots, dashes, slashes and leading zeros are omitted."""
	assert _row_el(cnpj_fdo="00.360.305/0001-04").find(f"{_NS}CNPJ_FDO").text == "360305000104"


def test_unlimited_leverage_is_the_literal_sl() -> None:
	"""The page: without a limit, QT_OPER_PATRIM_LIQ is SL."""
	block = {"realiza_oper_patrim_liq": "S", "qt_oper_patrim_liq": "SL"}
	tag = _row_el(oper_patrim_liq=block).find(f"{_NS}OPER_PATRIM_LIQ/{_NS}QT_OPER_PATRIM_LIQ")
	assert tag.text == "SL"


def test_optional_blocks_are_omitted() -> None:
	"""Closed-fund-only and optional limit blocks vanish when not given."""
	row = _row_el(cota_merc_secund=None, lim_cia_aberta=None, lim_emprest_titpub=None)
	assert "COTA_MERC_SECUND" not in _tags(row) + _tags(row.find(f"{_NS}ATIV_EXTER"))


def test_tx_adm_accepts_free_text_for_qualified_funds() -> None:
	"""The page lets qualified-investor funds describe TX_ADM as text."""
	text = _row_el(tx_adm="Conforme regulamento").find(f"{_NS}TX_ADM").text
	assert text == "Conforme regulamento"


def test_xml_is_escaped() -> None:
	"""Markup characters in text are escaped, so the output parses."""
	row = _row_el(ds_resumo_polit="a < b & c")
	assert row.find(f"{_NS}DS_RESUMO_POLIT").text == "a < b & c"


def test_non_ascii_text_round_trips_windows_1252(tmp_path: Path) -> None:
	"""Accented text is written as windows-1252 bytes."""
	out = tmp_path / "e.xml"
	ExtratoV1().export(_doc(ds_resumo_polit="Política ç"), output_path=str(out))
	assert "Política ç".encode("windows-1252") in out.read_bytes()


def test_export_to_file_returns_none(tmp_path: Path) -> None:
	"""With a path the writer returns None."""
	assert ExtratoV1().export(_doc(), output_path=str(tmp_path / "e.xml")) is None


def _failing_export(out: Path) -> None:
	"""Export a document that windows-1252 cannot encode to ``out``.

	Parameters
	----------
	out : Path
		The destination, which must survive the failure.
	"""
	bad = ExtratoV1Row(**_row()).model_copy(update={"ds_resumo_polit": "日本"})
	doc = ExtratoV1Document.model_construct(
		header=ExtratoV1Header(dt_gerac_arq="31/10/2026"), rows=[bad]
	)
	ExtratoV1().export(doc, output_path=str(out))


def test_unencodable_document_raises_value_error(tmp_path: Path) -> None:
	"""A character windows-1252 cannot carry is refused."""
	with pytest.raises(ValueError, match="windows-1252"):
		_failing_export(tmp_path / "e.xml")


def test_failed_export_leaves_existing_file_intact(tmp_path: Path) -> None:
	"""A document that cannot be encoded never truncates the target."""
	out = tmp_path / "e.xml"
	out.write_bytes(b"keep")
	with contextlib.suppress(ValueError):
		_failing_export(out)
	assert out.read_bytes() == b"keep"


def test_oversized_file_is_refused() -> None:
	"""The page caps a file at 1 MB."""
	rows = [ExtratoV1Row(**_row(ds_resumo_polit="x" * 4000)) for _ in range(300)]
	doc = ExtratoV1Document(header=ExtratoV1Header(dt_gerac_arq="31/10/2026"), rows=rows)
	with pytest.raises(ValueError, match="1 MB"):
		ExtratoV1().export(doc)


# --- rejection of invalid input ------------------------------------------------------------

_BASE = _row()


def _with(path: str, value: object) -> dict[str, Any]:
	"""Copy the base row with one dotted-path field replaced.

	Parameters
	----------
	path : str
		Dotted path into the nested row.
	value : object
		The new value.

	Returns
	-------
	dict[str, Any]
		The modified row.
	"""
	row = _row()
	*head, last = path.split(".")
	reduce(operator.getitem, head, row)[last] = value
	return row


@pytest.mark.parametrize(
	("path", "value"),
	[
		("cnpj_fdo", "11222333000182"),
		("cnpj_fdo", " 11222333000181"),
		("base_inform_form.dt_prosp", "31/02/2020"),
		("base_inform_form.dt_vigor_inform", "2020-02-01"),
		("cota_merc_secund.cod_merc_secund", 4),
		("cod_distr_fdo", 4),
		("cod_polit_invest", 5),
		("cod_cota_patrim_liq", 3),
		("cod_cota_entr", 4),
		("cod_cota_entr", 5),
		("serv_atend_cotista.tel_atend_cotista.nr_ddd", "01"),
		("serv_atend_cotista.tel_atend_cotista.nr_ddd", "12345"),
		("serv_atend_cotista.tel_atend_cotista.nr_tel", "123456789012"),
		("serv_atend_cotista.tel_atend_cotista.nr_tel", "3000-1234"),
		("serv_atend_cotista.ds_ender", "x" * 51),
		("serv_atend_cotista.ds_email", "x" * 51),
		("serv_atend_cotista.ds_web", "x" * 51),
		("serv_atend_cotista.ds_nome_resp", "x" * 101),
		("ds_resumo_polit", "x" * 4001),
		("ds_resumo_polit", ""),
		("vl_aplic_min", 1.5),
		("vl_aplic_min", "-1"),
		("tx_adm", "150"),
		("tx_adm", "x" * 401),
		("tx_adm", 2.5),
		("qt_dia_conv_cota", -1),
		("qt_dia_conv_cota", True),
		("risco_merc.ds_risco_merc", "x" * 201),
		("ativ_exter.horar_fech_merc", "x" * 101),
		("oper_patrim_liq.qt_oper_patrim_liq", "SLX"),
		("lim_cia_aberta.pr_max_cia_aberta", "100.0001"),
		("lim_tit_adm.pr_max_tit_adm", "-1"),
	],
)
def test_invalid_field_is_rejected(path: str, value: object) -> None:
	"""Values outside the page's shapes, tables and bounds are refused."""
	with pytest.raises(ValidationError):
		ExtratoV1Row(**_with(path, value))


@pytest.mark.parametrize(
	("path", "value"),
	[
		("cota_merc_secund", {"cota_negoc_merc_secund": "N", "cod_merc_secund": 1}),
		("resg_cotas", {"carencia_resg_cotas": "N", "dias_resg_cotas": 5}),
		("risco_merc", {"exp_risco_merc": "N", "ds_risco_merc": "x"}),
		("oper_patrim_liq", {"realiza_oper_patrim_liq": "N", "qt_oper_patrim_liq": "1"}),
		("oper_patrim_liq", {"realiza_oper_patrim_liq": "S"}),
		("tx_perfm", {"cobra_tx_perfm": "N", "prazo_aprop": 10}),
		("tx_perfm", {"cobra_tx_perfm": "S"}),
		("tx_ingresso", {"cobra_tx_ingresso": "S"}),
		("tx_ingresso", {"cobra_tx_ingresso": "N", "pr_tx_ingresso": "1"}),
		(
			"tx_ingresso",
			{"cobra_tx_ingresso": "S", "pr_tx_ingresso": "1", "vl_fixo_tx_ingresso": "2"},
		),
		("tx_saida", {"cobra_tx_saida": "S"}),
		("lim_cia_aberta", {"pr_min_cia_aberta": "60", "pr_max_cia_aberta": "50"}),
		("lim_emprest_acoes", {"pr_min_emprest_acoes": "5", "pr_max_emprest_acoes": "4"}),
		("lim_tit_adm", {}),
		("lim_fdo_adm", {}),
		("unknown_block", {}),
	],
)
def test_invalid_block_is_rejected(path: str, value: object) -> None:
	"""Conditional rules, mandatory limits, min/max order and unknown fields are refused."""
	with pytest.raises(ValidationError):
		ExtratoV1Row(**_with(path, value))


@pytest.mark.parametrize(
	"calc",
	[
		{},
		{"vl_tx_perfm": "20"},
		{"vl_tx_perfm": "20", "cod_param_tx_perfm": 36, "pr_ind_refer": "100"},
		{"vl_tx_perfm": "20", "cod_param_tx_perfm": 0, "pr_ind_refer": "100"},
	],
)
def test_invalid_performance_calc_is_rejected(calc: dict[str, Any]) -> None:
	"""The fee needs its mandatory trio or a description; index codes are table D."""
	tx = {"cobra_tx_perfm": "S", "calc_tx_perfm": calc, "prazo_aprop": 1,
		"prazo_pagam": {"vl_prazo_pagam": 1, "ds_prazo_pagam": "D"}}  # fmt: skip
	with pytest.raises(ValidationError):
		ExtratoV1Row(**_row(tx_perfm=tx))


def test_performance_fee_accepts_description_only() -> None:
	"""A qualified-investor fund may describe the fee as text."""
	tx = {"cobra_tx_perfm": "S", "calc_tx_perfm": {"info_adicional": "20% do que exceder"},
		"prazo_aprop": 1, "prazo_pagam": {"vl_prazo_pagam": 1, "ds_prazo_pagam": "A"}}  # fmt: skip
	assert ExtratoV1Row(**_row(tx_perfm=tx)).tx_perfm.calc_tx_perfm.vl_tx_perfm is None


def test_prazo_pagam_unit_is_d_m_or_a() -> None:
	"""The unit is one of D, M or A."""
	tx = _row()["tx_perfm"]
	tx["prazo_pagam"]["ds_prazo_pagam"] = "X"
	with pytest.raises(ValidationError):
		ExtratoV1Row(**_row(tx_perfm=tx))


def test_percentage_is_truncated_not_rounded() -> None:
	"""Excess places are cut toward zero."""
	assert ExtratoV1Row(**_row(tx_adm="2.99999")).tx_adm == Decimal("2.9999")


def test_document_needs_at_least_one_row() -> None:
	"""An empty document is refused."""
	with pytest.raises(ValidationError):
		ExtratoV1Document(header=ExtratoV1Header(dt_gerac_arq="31/10/2026"), rows=[])


def test_header_rejects_other_versions() -> None:
	"""VERSAO is fixed at 1.0."""
	with pytest.raises(ValidationError):
		ExtratoV1Header(versao="3.0", dt_gerac_arq="31/10/2026")


def test_models_are_immutable() -> None:
	"""Rows are frozen."""
	with pytest.raises(ValidationError):
		ExtratoV1Row(**_row()).cnpj_fdo = "1"
