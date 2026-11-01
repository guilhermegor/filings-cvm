"""Unit tests for the Lâmina V1 submission writer.

The expected tag lists are typed from the CVM page's sample file (PadraoXMLLamina.asp), not
derived from the models, so a field declared out of order or under the wrong name fails here.
"""

import contextlib
import copy
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET

from pydantic import ValidationError
import pytest

from filings_cvm.submission import LaminaV1, LaminaV1Document


NS = "{urn:lamina}"
CNPJ = "11222333000181"
OTHER_CNPJ = "11444777000161"

INFORM_TAGS = [
	"CNPJ_FUNDO", "NOME_FANTASIA", "END_ELETR", "DESC_PUB_ALVO", "RESTR_INV", "DESC_OBJET",
	"DESC_POL_INV", "ATIVO_EXT", "CRED_PRIV", "ALAV", "CONC_EMISSOR", "PERDAS_SIGN", "PL_NEGAT",
	"INV_INICIAL", "INV_ADIC", "RESG_MIN", "HOR_APL_RESG", "VALOR_PERM", "CARENCIA", "CONVERSAO",
	"PRAZO_PAGAM", "INFOR_TX_ADM", "INFOR_TX_ENTR", "INFOR_TX_SAIDA", "TX_DESEMPENHO",
	"INFOR_DESPESAS", "LISTA_COMP_CARTEIRA", "CLASSIF_RISCO", "INFOR_TAB_RENT_ANUAL",
	"LISTA_TAB_RENT_ANUAL", "LISTA_TAB_RENT_MENSAL", "FORM_CALC_RENT", "TAB_VAR_DESEMP",
	"INFORM_EXEMPLO_COMP", "TAB_SIMUL_DESPESAS", "TEL_SAC", "RECLAMACOES",
]  # fmt: skip
V3_ONLY_TAGS = [
	"COD_SUBCLASSE", "UTILIZ_DERIV_APENAS_PROTECAO_CART", "PERC_MAX", "OBS_HOR_APL_RESG",
	"TP_PRAZO_DIAS", "DS_FORMA_REMUN_DISTR", "PRINC_DISTR_OFERTA", "PRINC_CONFLITO_INTERES",
	"INFO_ADIC",
]  # fmt: skip


def _inform(cnpj: str = CNPJ) -> dict:
	"""Build a fully populated INFORM payload.

	Parameters
	----------
	cnpj : str
		The fund CNPJ.

	Returns
	-------
	dict
		The INFORM fields.
	"""
	return {
		"cnpj_fundo": cnpj,
		"nome_fantasia": "Fundo Alfa",
		"end_eletr": "www.alfa.com.br",
		"desc_pub_alvo": "Investidores em geral",
		"restr_inv": "Nenhuma",
		"desc_objet": "Buscar rentabilidade",
		"desc_pol_inv": "Renda fixa",
		"ativo_ext": "10",
		"cred_priv": "20",
		"alav": "1",
		"conc_emissor": "30",
		"perdas_sign": "N",
		"pl_negat": "N",
		"inv_inicial": "1000",
		"inv_adic": "100",
		"resg_min": "100",
		"hor_apl_resg": "14:30",
		"valor_perm": "500",
		"carencia": {"dias_car": 30, "cond_car": "Sem resgate"},
		"conversao": {"abert_fech": "A", "dia_aplic": 0, "abert_fech_c": "F", "dia_resg": 1},
		"prazo_pagam": 2,
		"infor_tx_adm": {"tipo_tx_adm": "F", "tx_adm": "1.5"},
		"infor_tx_entr": {"tx_entr": "0", "cond_entr": "Nenhuma"},
		"infor_tx_saida": {"dias_saida": 30, "tx_saida": "1", "cond_saida": "Nenhuma"},
		"tx_desempenho": "20% acima do CDI",
		"infor_despesas": {
			"despesas": "2",
			"inic_periodo": "01/01/2024",
			"fim_periodo": "31/12/2024",
			"end_elet_adm": "www.adm.com.br",
		},
		"lista_comp_carteira": {
			"pl_fundo": "1000000",
			"comp_carteira": [{"especie_ativo": "Titulos publicos", "perc_pl": "90"}],
		},
		"classif_risco": 3,
		**_return_blocks(),
		"tel_sac": "1130000000",
		"reclamacoes": "sac@alfa.com.br",
	}


def _return_blocks() -> dict:
	"""Build the return, example and simulation blocks of an INFORM payload.

	Returns
	-------
	dict
		The block fields, in page order.
	"""
	return {
		"infor_tab_rent_anual": {
			"rent_5anos": "50",
			"ind_refer": "CDI",
			"rent_ind_ref": "45",
			"anos_abaixo": 1,
			"inic_funcio": "01/01/2020",
			"antes_inic2": {"ano": [2019]},
		},
		"lista_tab_rent_anual": {
			"tab_rent_anual": [{"ano_rent": 2024, "rent_liq": "10", "var_ind_ref": "9"}]
		},
		"lista_tab_rent_mensal": {"tab_rent_mensal": [{"mes": 1, "rent_mens": "1"}]},
		"form_calc_rent": "CDI + 1%",
		"tab_var_desemp": {"var_desemp": "1", "formula_rentab": "CDI"},
		"inform_exemplo_comp": {
			"ano_ant": 2023,
			"ano_emiss": 2024,
			"valor_resg": "1000",
			"impostos": "10",
			"valor_despesas": "20",
		},
		"tab_simul_despesas": {
			"desp_prev3": "60",
			"desp_prev5": "100",
			"retor_brut3": "300",
			"retor_brut5": "500",
		},
	}


def _doc(*informs: dict) -> dict:
	"""Build a document payload.

	Parameters
	----------
	*informs : dict
		The INFORM payloads; one default when none is given.

	Returns
	-------
	dict
		The document fields.
	"""
	return {
		"header": {"dt_compt": "12/2024", "dt_gerac_arq": "15/01/2025"},
		"informs": list(informs or [_inform()]),
	}


def _xml(*informs: dict) -> ET.Element:
	"""Export a document and parse the result.

	Parameters
	----------
	*informs : dict
		The INFORM payloads.

	Returns
	-------
	ET.Element
		The parsed root.
	"""
	return ET.fromstring(LaminaV1().export(LaminaV1Document(**_doc(*informs))).encode("cp1252"))  # noqa: S314


def _inform_el() -> ET.Element:
	"""Return the first INFORM element of the default document.

	Returns
	-------
	ET.Element
		The INFORM element.
	"""
	return _xml().find(f"{NS}LISTA_INFORM/{NS}INFORM")


def test_inform_children_follow_the_page_sample_order() -> None:
	"""The INFORM children are exactly the page's sample tags, in order."""
	assert [c.tag.removeprefix(NS) for c in _inform_el()] == INFORM_TAGS


@pytest.mark.parametrize("tag", V3_ONLY_TAGS)
def test_v3_only_tags_are_absent(tag: str) -> None:
	"""No tag that V1 lacks (and V3 has) is emitted."""
	assert _inform_el().find(f"{NS}{tag}") is None


def test_header_is_cod_24_version_1_0() -> None:
	"""The header carries COD_DOC 24 and VERSAO 1.0, in the page's order."""
	header = _xml().find(f"{NS}CAB_INFORM")
	assert [(c.tag.removeprefix(NS), c.text) for c in header] == [
		("COD_DOC", "24"),
		("VERSAO", "1.0"),
		("DT_COMPT", "12/2024"),
		("DT_GERAC_ARQ", "15/01/2025"),
	]


def test_root_declares_the_sample_namespace() -> None:
	"""The root is DOC_ARQ in the sample's urn:lamina namespace."""
	assert _xml().tag == f"{NS}DOC_ARQ"


def test_declaration_is_windows_1252() -> None:
	"""The XML declaration names windows-1252."""
	assert (
		LaminaV1()
		.export(LaminaV1Document(**_doc()))
		.startswith('<?xml version="1.0" encoding="windows-1252"?>')
	)


def test_decimals_use_comma_and_are_truncated() -> None:
	"""Decimal fields use a comma and the repository scale (percent 4 places)."""
	data = _inform()
	data["alav"] = "1.23456"
	assert _inform_el_for(data).find(f"{NS}ALAV").text == "1,2345"


def _inform_el_for(data: dict) -> ET.Element:
	"""Export one INFORM payload and return its element.

	Parameters
	----------
	data : dict
		The INFORM payload.

	Returns
	-------
	ET.Element
		The INFORM element.
	"""
	return _xml(data).find(f"{NS}LISTA_INFORM/{NS}INFORM")


def test_cnpj_is_written_without_mask() -> None:
	"""CNPJ_FUNDO is the 14 digits."""
	assert _inform_el().find(f"{NS}CNPJ_FUNDO").text == CNPJ


def test_optional_blocks_are_omitted_when_none() -> None:
	"""CARENCIA is optional and omitted when not given."""
	data = _inform()
	del data["carencia"]
	assert _inform_el_for(data).find(f"{NS}CARENCIA") is None


def test_two_funds_repeat_the_inform_element() -> None:
	"""Each fund is its own INFORM."""
	root = _xml(_inform(), _inform(OTHER_CNPJ))
	assert len(root.findall(f"{NS}LISTA_INFORM/{NS}INFORM")) == 2


def _drop(key: str) -> dict:
	"""Return an INFORM payload without ``key``.

	Parameters
	----------
	key : str
		The field to drop.

	Returns
	-------
	dict
		The INFORM payload.
	"""
	data = _inform()
	del data[key]
	return data


@pytest.mark.parametrize("key", ["cnpj_fundo", "alav", "conc_emissor", "tel_sac", "reclamacoes"])
def test_page_required_fields_are_required(key: str) -> None:
	"""A field the page does not mark optional cannot be omitted."""
	with pytest.raises(ValidationError):
		LaminaV1Document(**_doc(_drop(key)))


@pytest.mark.parametrize("key", V3_ONLY_TAGS[1:] + ["cod_subclasse"])
def test_v3_fields_are_rejected(key: str) -> None:
	"""A V3-only field is refused rather than silently dropped."""
	data = _inform()
	data[key] = "S"
	with pytest.raises(ValidationError):
		LaminaV1Document(**_doc(data))


def test_float_decimal_is_rejected() -> None:
	"""Binary floats are refused for decimal fields."""
	data = _inform()
	data["alav"] = 1.5
	with pytest.raises(ValidationError):
		LaminaV1Document(**_doc(data))


def test_invalid_cnpj_is_rejected() -> None:
	"""A CNPJ with a wrong check digit is refused."""
	with pytest.raises(ValidationError):
		LaminaV1Document(**_doc(_inform("11222333000182")))


def test_repeated_fund_is_rejected() -> None:
	"""The same CNPJ twice in one file is refused."""
	with pytest.raises(ValidationError):
		LaminaV1Document(**_doc(_inform(), _inform()))


def test_more_than_70_funds_are_rejected() -> None:
	"""The page caps a file at 70 funds."""
	with pytest.raises(ValidationError):
		LaminaV1Document(**_doc(*[_inform() for _ in range(71)]))


def test_header_version_is_pinned() -> None:
	"""Only VERSAO 1.0 is accepted."""
	data = _doc()
	data["header"]["versao"] = "3.0"
	with pytest.raises(ValidationError):
		LaminaV1Document(**data)


def test_return_table_cross_checks_apply() -> None:
	"""A repeated year in the annual table is refused (shared V3 rule)."""
	data = copy.deepcopy(_inform())
	row = data["lista_tab_rent_anual"]["tab_rent_anual"][0]
	data["lista_tab_rent_anual"]["tab_rent_anual"] = [row, row]
	with pytest.raises(ValidationError):
		LaminaV1Document(**_doc(data))


def test_fixed_fee_needs_tx_adm() -> None:
	"""A fixed management fee without TX_ADM is refused."""
	data = _inform()
	data["infor_tx_adm"] = {"tipo_tx_adm": "F"}
	with pytest.raises(ValidationError):
		LaminaV1Document(**_doc(data))


def test_file_is_written_in_windows_1252(tmp_path: Path) -> None:
	"""A written file holds the cp1252 bytes."""
	data = _inform()
	data["nome_fantasia"] = "Fundo Ação"
	out = tmp_path / "lamina.xml"
	LaminaV1().export(LaminaV1Document(**_doc(data)), str(out))
	assert "Fundo Ação".encode("cp1252") in out.read_bytes()


def test_export_to_file_returns_none(tmp_path: Path) -> None:
	"""Writing to a path returns None."""
	assert LaminaV1().export(LaminaV1Document(**_doc()), str(tmp_path / "l.xml")) is None


def _export_unencodable(out: Path) -> None:
	"""Export a document holding text windows-1252 cannot carry.

	Parameters
	----------
	out : Path
		The destination file.
	"""
	doc = LaminaV1Document(**_doc())
	object.__setattr__(doc.header, "dt_compt", "\u4e2d")
	LaminaV1().export(doc, str(out))


def test_unencodable_text_raises(tmp_path: Path) -> None:
	"""Text windows-1252 cannot carry raises ValueError."""
	with pytest.raises(ValueError, match="windows-1252"):
		_export_unencodable(tmp_path / "lamina.xml")


def test_failed_export_leaves_existing_file_untouched(tmp_path: Path) -> None:
	"""The old file survives a failed export."""
	out = tmp_path / "lamina.xml"
	out.write_bytes(b"old")
	with contextlib.suppress(ValueError):
		_export_unencodable(out)
	assert out.read_bytes() == b"old"


def test_money_scale_is_two_places() -> None:
	"""Money is truncated to two places with a comma."""
	data = _inform()
	data["inv_inicial"] = Decimal("1000.999")
	assert _inform_el_for(data).find(f"{NS}INV_INICIAL").text == "1000,99"
