"""Unit tests for the Lâmina V2 submission writer.

The expected tag lists are typed from the V2 page's sample file (``PadraoXMLLaminaV2.asp``), not
derived from the models. The serialiser and the V3 blocks are shared with V3 and covered by
``test_lamina_submission.py``; these tests pin what V2 changes: ``VERSAO`` 2.0, no
``COD_SUBCLASSE``, ``CNPJ_FUNDO`` mandatory, and the tag order.
"""

from pathlib import Path
from xml.etree import ElementTree as ET

from pydantic import ValidationError
import pytest

from filings_cvm.submission import LaminaV2, LaminaV2Document


NS = "{urn:lamina}"
CNPJ = "11222333000181"

# Top-level children of a fully populated INFORM, in the order of the V2 page's sample file.
INFORM_TAGS = [
	"CNPJ_FUNDO",
	"NOME_FANTASIA",
	"END_ELETR",
	"DESC_PUB_ALVO",
	"RESTR_INV",
	"DESC_OBJET",
	"DESC_POL_INV",
	"ATIVO_EXT",
	"CRED_PRIV",
	"ALAV",
	"UTILIZ_DERIV_APENAS_PROTECAO_CART",
	"PERDAS_SIGN",
	"PL_NEGAT",
	"PERC_MAX",
	"INV_INICIAL",
	"INV_ADIC",
	"RESG_MIN",
	"HOR_APL_RESG",
	"OBS_HOR_APL_RESG",
	"VALOR_PERM",
	"CARENCIA",
	"CONVERSAO",
	"TP_PRAZO_DIAS",
	"PRAZO_PAGAM",
	"INFOR_TX_ADM",
	"INFOR_TX_ENTR",
	"INFOR_TX_SAIDA",
	"TX_DESEMPENHO",
	"INFOR_DESPESAS",
	"LISTA_COMP_CARTEIRA",
	"CLASSIF_RISCO",
	"INFOR_TAB_RENT_ANUAL",
	"LISTA_TAB_RENT_ANUAL",
	"LISTA_TAB_RENT_MENSAL",
	"FORM_CALC_RENT",
	"TAB_VAR_DESEMP",
	"INFORM_EXEMPLO_COMP",
	"TAB_SIMUL_DESPESAS",
	"DS_FORMA_REMUN_DISTR",
	"PRINC_DISTR_OFERTA",
	"PRINC_CONFLITO_INTERES",
	"TEL_SAC",
	"RECLAMACOES",
	"INFO_ADIC",
]


def _inform(**overrides: object) -> dict[str, object]:
	"""Build the mandatory fields of one INFORM; keyword overrides replace or add fields."""
	base: dict[str, object] = {
		"cnpj_fundo": CNPJ,
		"nome_fantasia": "Fundo Alfa",
		"end_eletr": "www.alfa.com.br",
		"desc_pub_alvo": "Investidores em geral",
		"restr_inv": "Nenhuma",
		"desc_objet": "Superar o CDI",
		"desc_pol_inv": "Titulos publicos",
		"ativo_ext": "10",
		"cred_priv": "20",
		"utiliz_deriv_apenas_protecao_cart": "S",
		"perdas_sign": "N",
		"pl_negat": "N",
		"perc_max": "100",
		"inv_inicial": "100",
		"inv_adic": "50",
		"resg_min": "10",
		"hor_apl_resg": "14:30",
		"obs_hor_apl_resg": "Ate as 14h30",
		"valor_perm": "0",
		"conversao": {"abert_fech": "A", "dia_aplic": 1, "abert_fech_c": "F", "dia_resg": 2},
		"tp_prazo_dias": "1",
		"prazo_pagam": 3,
		"infor_tx_adm": {"tipo_tx_adm": "F", "tx_adm": "1.5"},
		"tx_desempenho": "20% do que exceder o CDI",
		"classif_risco": 3,
		"ds_forma_remun_distr": "Parte da taxa de administracao",
		"princ_distr_oferta": "Nao",
		"princ_conflito_interes": "Nenhum",
		"tel_sac": "1140041234",
		"reclamacoes": "sac@alfa.com.br",
		"info_adic": "Nada a declarar",
	}
	base.update(overrides)
	return base


def _full_inform() -> dict[str, object]:
	"""Build an INFORM with every optional block filled."""
	return _inform(
		alav="200",
		carencia={"dias_car": 30, "cond_car": "Sem resgate"},
		infor_tx_entr={"tx_entr": "0.5", "cond_entr": "Sobre a aplicacao"},
		infor_tx_saida={"dias_saida": 10, "tx_saida": "1", "cond_saida": "Antes de 10 dias"},
		infor_despesas={
			"despesas": "0.75",
			"inic_periodo": "01/01/2024",
			"fim_periodo": "31/12/2024",
			"end_elet_adm": "www.adm.com.br",
		},
		lista_comp_carteira={
			"pl_fundo": "1000000.5",
			"comp_carteira": [{"especie_ativo": "Titulos publicos", "perc_pl": "100"}],
		},
		infor_tab_rent_anual={"rent_5anos": "45.1234", "ind_refer": "CDI"},
		lista_tab_rent_anual={"tab_rent_anual": [{"ano_rent": 2024, "rent_liq": "10.5"}]},
		lista_tab_rent_mensal={"tab_rent_mensal": [{"mes": 1, "rent_mens": "0.9"}]},
		form_calc_rent="Cota final sobre inicial",
		tab_var_desemp={"var_desemp": "1", "formula_rentab": "x"},
		inform_exemplo_comp={
			"ano_ant": 2023,
			"ano_emiss": 2024,
			"valor_resg": "1000",
			"impostos": "10",
			"valor_despesas": "5",
		},
		tab_simul_despesas={
			"desp_prev3": "10",
			"desp_prev5": "20",
			"retor_brut3": "30",
			"retor_brut5": "50",
		},
	)


def _doc(inform: dict[str, object], **header: object) -> LaminaV2Document:
	"""Build a V2 document around one INFORM."""
	head = {"dt_compt": "01/2025", "dt_gerac_arq": "15/01/2025", **header}
	return LaminaV2Document.model_validate({"header": head, "informs": [inform]})


def _root(doc: LaminaV2Document) -> ET.Element:
	"""Export a document and parse the XML back."""
	return ET.fromstring(LaminaV2().export(doc).split("\n", 1)[1])  # type: ignore[union-attr]  # noqa: S314


def _tags(element: ET.Element) -> list[str]:
	"""Return the namespace-stripped tag of each child."""
	return [child.tag.removeprefix(NS) for child in element]


def test_header_carries_version_2_0_in_page_order() -> None:
	"""CAB_INFORM is COD_DOC 24, VERSAO 2.0, DT_COMPT, DT_GERAC_ARQ."""
	header = _root(_doc(_inform())).find(f"{NS}CAB_INFORM")
	assert [(c.tag.removeprefix(NS), c.text) for c in header] == [
		("COD_DOC", "24"),
		("VERSAO", "2.0"),
		("DT_COMPT", "01/2025"),
		("DT_GERAC_ARQ", "15/01/2025"),
	]


def test_export_declares_windows_1252_and_the_lamina_namespace() -> None:
	"""The prolog and root match the V2 sample."""
	xml = LaminaV2().export(_doc(_inform()))
	assert xml.startswith(
		'<?xml version="1.0" encoding="windows-1252"?>\n<DOC_ARQ xmlns="urn:lamina">'
	)


def test_fully_populated_inform_emits_every_tag_in_v2_sample_order() -> None:
	"""Every top-level INFORM tag appears once, in the V2 sample's order, with no subclass tag."""
	inform = _root(_doc(_full_inform())).find(f"{NS}LISTA_INFORM/{NS}INFORM")
	assert _tags(inform) == INFORM_TAGS


def test_version_other_than_2_0_is_rejected() -> None:
	"""VERSAO is fixed by the standard; V3's 3.0 is not accepted."""
	with pytest.raises(ValidationError):
		_doc(_inform(), versao="3.0")


def test_subclass_code_is_rejected() -> None:
	"""COD_SUBCLASSE does not exist in V2."""
	with pytest.raises(ValidationError):
		_doc(_inform(cod_subclasse="A1"))


def test_missing_cnpj_is_rejected() -> None:
	"""CNPJ_FUNDO is mandatory in V2."""
	with pytest.raises(ValidationError):
		_doc(_inform(cnpj_fundo=None))


def test_invalid_cnpj_check_digits_are_rejected() -> None:
	"""A CNPJ with wrong check digits fails validation."""
	with pytest.raises(ValidationError):
		_doc(_inform(cnpj_fundo="11222333000182"))


def test_repeated_fund_in_one_file_is_rejected() -> None:
	"""The same CNPJ twice in one file is refused."""
	with pytest.raises(ValidationError):
		LaminaV2Document.model_validate(
			{
				"header": {"dt_compt": "01/2025", "dt_gerac_arq": "15/01/2025"},
				"informs": [_inform(), _inform()],
			}
		)


def test_more_than_70_funds_are_rejected() -> None:
	"""The page caps a file at 70 funds."""
	informs = [_inform(cnpj_fundo=f"{n:08d}000100") for n in range(71)]
	with pytest.raises(ValidationError):
		LaminaV2Document.model_validate(
			{"header": {"dt_compt": "01/2025", "dt_gerac_arq": "15/01/2025"}, "informs": informs}
		)


def test_decimal_uses_comma_separator() -> None:
	"""Decimals are written with a comma, never a point (page: 'Vírgula ... casas decimais')."""
	tx = _root(_doc(_inform())).find(f"{NS}LISTA_INFORM/{NS}INFORM/{NS}ATIVO_EXT")
	assert tx.text == "10,0000"


def test_export_to_file_writes_windows_1252(tmp_path: Path) -> None:
	"""A path writes the encoded file and returns None."""
	target = tmp_path / "lamina_v2.xml"
	doc = _doc(_inform(nome_fantasia="Fundo Ação"))
	LaminaV2().export(doc, str(target))
	assert "Ação".encode("windows-1252") in target.read_bytes()
