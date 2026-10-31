"""Unit tests for the Lâmina V3 submission writer.

The expected tag lists below are typed from the CVM page's sample file, not derived from the
models, so a field declared out of order or under the wrong name fails here.
"""

import copy
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET

from pydantic import ValidationError
import pytest

from filings_cvm.submission import Lamina, LaminaDocument


NS = "{urn:lamina}"
VALID_CNPJ = "11222333000181"
OTHER_CNPJ = "11444777000161"

# Top-level children of a fully populated INFORM, in the order of the page's sample file.
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
		"cnpj_fundo": VALID_CNPJ,
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
	"""Build an INFORM with every optional block and field filled."""
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
			"comp_carteira": [
				{"especie_ativo": "Titulos publicos", "perc_pl": "60"},
				{"especie_ativo": "Operacoes compromissadas", "perc_pl": "40"},
			],
		},
		infor_tab_rent_anual={
			"rent_5anos": "45.1234",
			"ind_refer": "CDI",
			"rent_ind_ref": "40",
			"anos_abaixo": 1,
			"inic_funcio": "15/03/2021",
			"antes_inic2": {"ano": [2019, 2020]},
		},
		lista_tab_rent_anual={
			"tab_rent_anual": [
				{
					"ano_rent": 2023,
					"rent_liq": "-1.5",
					"var_ind_ref": "13",
					"rent_perc_ind_ref": "-11.5",
					"comentarios": "Ano dificil",
				},
				{"ano_rent": 2024, "rent_liq": "10"},
			]
		},
		lista_tab_rent_mensal={
			"tab_rent_mensal": [
				{
					"mes": 1,
					"rent_mens": "0.8",
					"var_mens_ind_ref": "0.9",
					"rent_mens_perc_ind_ref": "88.8888",
					"comentarios": "Janeiro",
				},
				{"mes": 12, "rent_mens": "-0.1"},
			]
		},
		form_calc_rent="Cota liquida de despesas",
		tab_var_desemp={
			"var_desemp": "5",
			"formula_rentab": "Indice mais spread",
			"cenario_gatilho": "Pior, medio e bom",
			"esclarec": "Explicacao",
		},
		inform_exemplo_comp={
			"ano_ant": 2023,
			"ano_emiss": 2024,
			"valor_resg": "1000",
			"impostos": "15.55",
			"valor_ing": "1",
			"valor_saida": "2",
			"ajuste_perfor": "-3",
			"valor_despesas": "12.3",
		},
		tab_simul_despesas={
			"desp_prev3": "30",
			"desp_prev5": "50",
			"retor_brut3": "-4.5",
			"retor_brut5": "60",
		},
	)


def _doc(*informs: dict[str, object], **header: object) -> LaminaDocument:
	"""Build a document around the given INFORM dicts."""
	head = {"dt_compt": "01/2025", "dt_gerac_arq": "15/01/2025", **header}
	return LaminaDocument.model_validate({"header": head, "informs": list(informs)})


def _root(doc: LaminaDocument) -> ET.Element:
	"""Export a document and parse the XML back."""
	return ET.fromstring(Lamina().export(doc).split("\n", 1)[1])  # type: ignore[union-attr]  # noqa: S314


def _pairs(element: ET.Element) -> list[tuple[str, str | None]]:
	"""Return (tag, text) for each child, with the namespace stripped."""
	return [(child.tag.removeprefix(NS), child.text) for child in element]


def _first_inform(doc: LaminaDocument) -> ET.Element:
	"""Return the first INFORM element of an exported document."""
	return _root(doc).find(f"{NS}LISTA_INFORM/{NS}INFORM")  # type: ignore[return-value]


def _block(doc: LaminaDocument, name: str) -> ET.Element:
	"""Return one named child block of the first INFORM."""
	return _first_inform(doc).find(f"{NS}{name}")  # type: ignore[return-value]


def _rejects(**overrides: object) -> None:
	"""Assert an INFORM built with these overrides fails validation."""
	with pytest.raises(ValidationError):
		_doc(_inform(**overrides))


# --- document structure -------------------------------------------------------------------


def test_export_declares_windows_1252_and_the_lamina_namespace() -> None:
	"""The prolog and root match the page's sample."""
	xml = Lamina().export(_doc(_inform()))
	assert xml.startswith('<?xml version="1.0" encoding="windows-1252"?>\n')
	assert '<DOC_ARQ xmlns="urn:lamina">' in xml


def test_header_block_xml() -> None:
	"""CAB_INFORM carries 24, 3.0, the competence and the generation date, in that order."""
	header = _root(_doc(_inform())).find(f"{NS}CAB_INFORM")
	assert _pairs(header) == [
		("COD_DOC", "24"),
		("VERSAO", "3.0"),
		("DT_COMPT", "01/2025"),
		("DT_GERAC_ARQ", "15/01/2025"),
	]


def test_fully_populated_inform_emits_every_tag_in_sample_order() -> None:
	"""Every top-level INFORM tag appears once, in the order of the page's sample file."""
	tags = [tag for tag, _ in _pairs(_first_inform(_doc(_full_inform())))]
	assert tags == INFORM_TAGS


def test_minimal_inform_omits_every_optional_block() -> None:
	"""With only mandatory data no optional tag is written, not even empty."""
	tags = [tag for tag, _ in _pairs(_first_inform(_doc(_inform())))]
	optional = {
		"ALAV",
		"CARENCIA",
		"INFOR_TX_ENTR",
		"INFOR_TX_SAIDA",
		"INFOR_DESPESAS",
		"LISTA_COMP_CARTEIRA",
		"INFOR_TAB_RENT_ANUAL",
		"LISTA_TAB_RENT_ANUAL",
		"LISTA_TAB_RENT_MENSAL",
		"FORM_CALC_RENT",
		"TAB_VAR_DESEMP",
		"INFORM_EXEMPLO_COMP",
		"TAB_SIMUL_DESPESAS",
		"COD_SUBCLASSE",
	}
	assert not optional & set(tags)
	assert tags == [t for t in INFORM_TAGS if t not in optional]


def test_scalar_fields_xml() -> None:
	"""Top-level scalars: bare CNPJ, comma decimals at the table's scale, plain integers."""
	pairs = dict(_pairs(_first_inform(_doc(_full_inform()))))
	assert pairs["CNPJ_FUNDO"] == VALID_CNPJ
	assert pairs["ATIVO_EXT"] == "10,0000"
	assert pairs["CRED_PRIV"] == "20,0000"
	assert pairs["ALAV"] == "200,0000"
	assert pairs["PERC_MAX"] == "100,0000"
	assert pairs["INV_INICIAL"] == "100,00"
	assert pairs["INV_ADIC"] == "50,00"
	assert pairs["RESG_MIN"] == "10,00"
	assert pairs["VALOR_PERM"] == "0,00"
	assert pairs["HOR_APL_RESG"] == "14:30"
	assert pairs["TP_PRAZO_DIAS"] == "1"
	assert pairs["PRAZO_PAGAM"] == "3"
	assert pairs["CLASSIF_RISCO"] == "3"
	assert pairs["TEL_SAC"] == "1140041234"
	assert pairs["UTILIZ_DERIV_APENAS_PROTECAO_CART"] == "S"
	assert pairs["PERDAS_SIGN"] == "N"
	assert pairs["PL_NEGAT"] == "N"


def test_subclass_inform_writes_cod_subclasse_and_no_cnpj() -> None:
	"""A subclass INFORM carries COD_SUBCLASSE instead of CNPJ_FUNDO."""
	doc = _doc(_inform(cnpj_fundo=None, cod_subclasse="SUB-001"))
	pairs = _pairs(_first_inform(doc))
	assert pairs[0] == ("COD_SUBCLASSE", "SUB-001")
	assert "CNPJ_FUNDO" not in dict(pairs)


def test_several_informs_are_written_in_order() -> None:
	"""One INFORM per fund, in the order given."""
	doc = _doc(_inform(), _inform(cnpj_fundo=OTHER_CNPJ))
	cnpjs = [e.text for e in _root(doc).iter(f"{NS}CNPJ_FUNDO")]
	assert cnpjs == [VALID_CNPJ, OTHER_CNPJ]


# --- one test per nested block ------------------------------------------------------------


@pytest.mark.parametrize(
	("name", "expected"),
	[
		("CARENCIA", [("DIAS_CAR", "30"), ("COND_CAR", "Sem resgate")]),
		(
			"CONVERSAO",
			[("ABERT_FECH", "A"), ("DIA_APLIC", "1"), ("ABERT_FECH_C", "F"), ("DIA_RESG", "2")],
		),
		("INFOR_TX_ENTR", [("TX_ENTR", "0,5000"), ("COND_ENTR", "Sobre a aplicacao")]),
		(
			"INFOR_TX_SAIDA",
			[("DIAS_SAIDA", "10"), ("TX_SAIDA", "1,0000"), ("COND_SAIDA", "Antes de 10 dias")],
		),
		(
			"INFOR_DESPESAS",
			[
				("DESPESAS", "0,7500"),
				("INIC_PERIODO", "01/01/2024"),
				("FIM_PERIODO", "31/12/2024"),
				("END_ELET_ADM", "www.adm.com.br"),
			],
		),
		(
			"TAB_VAR_DESEMP",
			[
				("VAR_DESEMP", "5,0000"),
				("FORMULA_RENTAB", "Indice mais spread"),
				("CENARIO_GATILHO", "Pior, medio e bom"),
				("ESCLAREC", "Explicacao"),
			],
		),
		(
			"INFORM_EXEMPLO_COMP",
			[
				("ANO_ANT", "2023"),
				("ANO_EMISS", "2024"),
				("VALOR_RESG", "1000,00"),
				("IMPOSTOS", "15,55"),
				("VALOR_ING", "1,00"),
				("VALOR_SAIDA", "2,00"),
				("AJUSTE_PERFOR", "-3,00"),
				("VALOR_DESPESAS", "12,30"),
			],
		),
		(
			"TAB_SIMUL_DESPESAS",
			[
				("DESP_PREV3", "30,00"),
				("DESP_PREV5", "50,00"),
				("RETOR_BRUT3", "-4,50"),
				("RETOR_BRUT5", "60,00"),
			],
		),
	],
)
def test_flat_block_of_full_inform_emits_tags_in_sample_order(
	name: str, expected: list[tuple[str, str]]
) -> None:
	"""Each flat block of a fully populated INFORM emits its tags in sample order."""
	assert _pairs(_block(_doc(_full_inform()), name)) == expected


@pytest.mark.parametrize(
	("fee", "expected"),
	[
		pytest.param(
			{"tipo_tx_adm": "F", "tx_adm": "1.5", "esclarec": "Ao ano"},
			[("TIPO_TX_ADM", "F"), ("TX_ADM", "1,5000"), ("ESCLAREC", "Ao ano")],
			id="fixed",
		),
		pytest.param(
			{"tipo_tx_adm": "V", "tx_min": "0.5", "tx_max": "2"},
			[("TIPO_TX_ADM", "V"), ("TX_MIN", "0,5000"), ("TX_MAX", "2,0000")],
			id="variable",
		),
	],
)
def test_management_fee_block_per_fee_type_emits_only_its_rate_tags(
	fee: dict[str, str], expected: list[tuple[str, str]]
) -> None:
	"""INFOR_TX_ADM: a fixed fee writes TX_ADM; a variable fee writes TX_MIN/TX_MAX instead."""
	assert _pairs(_block(_doc(_inform(infor_tx_adm=fee)), "INFOR_TX_ADM")) == expected


def test_portfolio_block_xml() -> None:
	"""LISTA_COMP_CARTEIRA: PL_FUNDO then a COMP_CARTEIRA per asset type."""
	block = _block(_doc(_full_inform()), "LISTA_COMP_CARTEIRA")
	assert _pairs(block)[0] == ("PL_FUNDO", "1000000,50")
	assets = [_pairs(item) for item in block.findall(f"{NS}COMP_CARTEIRA")]
	assert assets == [
		[("ESPECIE_ATIVO", "Titulos publicos"), ("PERC_PL", "60,0000")],
		[("ESPECIE_ATIVO", "Operacoes compromissadas"), ("PERC_PL", "40,0000")],
	]
	assert [tag for tag, _ in _pairs(block)] == ["PL_FUNDO", "COMP_CARTEIRA", "COMP_CARTEIRA"]


def test_annual_summary_block_xml() -> None:
	"""INFOR_TAB_RENT_ANUAL: scalars in sample order, then ANTES_INIC2 with one ANO per year."""
	block = _block(_doc(_full_inform()), "INFOR_TAB_RENT_ANUAL")
	assert [(t, x) for t, x in _pairs(block) if t != "ANTES_INIC2"] == [
		("RENT_5ANOS", "45,1234"),
		("IND_REFER", "CDI"),
		("RENT_IND_REF", "40,0000"),
		("ANOS_ABAIXO", "1"),
		("INIC_FUNCIO", "15/03/2021"),
	]
	assert [tag for tag, _ in _pairs(block)][-1] == "ANTES_INIC2"
	years = block.find(f"{NS}ANTES_INIC2")
	assert _pairs(years) == [("ANO", "2019"), ("ANO", "2020")]


def test_annual_return_table_xml() -> None:
	"""LISTA_TAB_RENT_ANUAL: a TAB_RENT_ANUAL per year; a negative return keeps its sign."""
	rows = _block(_doc(_full_inform()), "LISTA_TAB_RENT_ANUAL").findall(f"{NS}TAB_RENT_ANUAL")
	assert [_pairs(r) for r in rows] == [
		[
			("ANO_RENT", "2023"),
			("RENT_LIQ", "-1,5000"),
			("VAR_IND_REF", "13,0000"),
			("RENT_PERC_IND_REF", "-11,5000"),
			("COMENTARIOS", "Ano dificil"),
		],
		[("ANO_RENT", "2024"), ("RENT_LIQ", "10,0000")],
	]


def test_monthly_return_table_xml() -> None:
	"""LISTA_TAB_RENT_MENSAL: a TAB_RENT_MENSAL per month, month unpadded, tag MES."""
	rows = _block(_doc(_full_inform()), "LISTA_TAB_RENT_MENSAL").findall(f"{NS}TAB_RENT_MENSAL")
	assert [_pairs(r) for r in rows] == [
		[
			("MES", "1"),
			("RENT_MENS", "0,8000"),
			("VAR_MENS_IND_REF", "0,9000"),
			("RENT_MENS_PERC_IND_REF", "88,8888"),
			("COMENTARIOS", "Janeiro"),
		],
		[("MES", "12"), ("RENT_MENS", "-0,1000")],
	]


# --- encoding and file output -------------------------------------------------------------


def test_text_is_xml_escaped() -> None:
	"""Markup characters in free text are escaped and survive a parse round trip."""
	doc = _doc(_inform(nome_fantasia='A & B <C> "D"'))
	assert dict(_pairs(_first_inform(doc)))["NOME_FANTASIA"] == 'A & B <C> "D"'
	assert "A &amp; B &lt;C&gt;" in Lamina().export(doc)


def test_file_is_written_as_windows_1252_bytes(tmp_path: Path) -> None:
	"""Accented text and the euro sign are single windows-1252 bytes; export returns None."""
	target = tmp_path / "lamina.xml"
	doc = _doc(_inform(nome_fantasia="Ação € Fundo"))
	assert Lamina().export(doc, output_path=str(target)) is None
	raw = target.read_bytes()
	assert "Ação € Fundo".encode("windows-1252") in raw
	assert raw == Lamina().export(doc).encode("windows-1252")


def test_failed_export_leaves_an_existing_file_untouched(tmp_path: Path) -> None:
	"""A character windows-1252 cannot hold must not truncate the target (validation bypassed)."""
	target = tmp_path / "lamina.xml"
	target.write_bytes(b"previous content")
	good = _doc(_inform())
	inform = good.informs[0].model_copy(update={"nome_fantasia": "Ω"})
	bad = good.model_copy(update={"informs": [inform]})
	with pytest.raises(ValueError, match="windows-1252"):
		Lamina().export(bad, output_path=str(target))
	assert target.read_bytes() == b"previous content"


def test_export_refuses_a_control_character_that_bypassed_validation(tmp_path: Path) -> None:
	"""NUL is not XML; the self-check refuses it and the target stays intact."""
	target = tmp_path / "lamina.xml"
	target.write_bytes(b"previous content")
	good = _doc(_inform())
	inform = good.informs[0].model_copy(update={"nome_fantasia": "a\x00b"})
	bad = good.model_copy(update={"informs": [inform]})
	with pytest.raises(ValueError, match="cannot be serialised"):
		Lamina().export(bad, output_path=str(target))
	assert target.read_bytes() == b"previous content"


# --- validation: dates and times ----------------------------------------------------------


@pytest.mark.parametrize(
	"value",
	["13/2025", "00/2025", "1/2025", "01/25", "2025-01", "01/2025\n", "０１/2025", "01/1899", ""],
)
def test_competence_rejects_malformed_or_impossible_values(value: str) -> None:
	"""DT_COMPT must be a real MM/AAAA."""
	with pytest.raises(ValidationError):
		_doc(_inform(), dt_compt=value)


@pytest.mark.parametrize(
	"value",
	[
		"31/02/2025",
		"29/02/2025",
		"32/01/2025",
		"00/01/2025",
		"2025-01-15",
		"15/01/2025\n",
		"1/1/2025",
		"15/01/1899",
		"１５/01/2025",
	],
)
def test_generation_date_rejects_impossible_dates(value: str) -> None:
	"""DT_GERAC_ARQ must be a real DD/MM/AAAA (31/02 and a non-leap 29/02 are refused)."""
	with pytest.raises(ValidationError):
		_doc(_inform(), dt_gerac_arq=value)


def test_generation_date_accepts_a_leap_day() -> None:
	"""29/02/2024 exists."""
	_doc(_inform(), dt_gerac_arq="29/02/2024")


@pytest.mark.parametrize("value", ["24:00", "9:00", "12:60", "12:30\n", "12h30", ""])
def test_application_time_rejects_malformed_values(value: str) -> None:
	"""HOR_APL_RESG must be a 24-hour HH:MM."""
	_rejects(hor_apl_resg=value)


def test_expense_period_must_not_end_before_it_starts() -> None:
	"""FIM_PERIODO before INIC_PERIODO is refused; the same day is allowed."""
	block = {"despesas": "1", "end_elet_adm": "x"}
	with pytest.raises(ValidationError):
		_doc(
			_inform(
				infor_despesas={**block, "inic_periodo": "02/01/2024", "fim_periodo": "01/01/2024"}
			)
		)
	_doc(
		_inform(
			infor_despesas={**block, "inic_periodo": "01/01/2024", "fim_periodo": "01/01/2024"}
		)
	)


def test_start_of_operations_rejects_an_impossible_date() -> None:
	"""INIC_FUNCIO is a real date."""
	_rejects(infor_tab_rent_anual={"inic_funcio": "30/02/2022"})


# --- validation: decimals -----------------------------------------------------------------


@pytest.mark.parametrize("field", ["ativo_ext", "inv_inicial", "perc_max", "alav", "valor_perm"])
@pytest.mark.parametrize("bad", [1.5, True, float("nan"), "NaN", "Infinity", "abc", "1,5", [1]])
def test_decimal_fields_refuse_floats_and_non_finite_values(field: str, bad: object) -> None:
	"""A float (or bool, NaN, infinity, comma text) never becomes a Decimal field."""
	_rejects(**{field: bad})


def test_decimal_fields_accept_decimal_int_and_str() -> None:
	"""Decimal, int and str are the three accepted inputs."""
	doc = _doc(_inform(inv_inicial=Decimal("10.5"), inv_adic=7, resg_min="1.25"))
	pairs = dict(_pairs(_first_inform(doc)))
	assert (pairs["INV_INICIAL"], pairs["INV_ADIC"], pairs["RESG_MIN"]) == (
		"10,50",
		"7,00",
		"1,25",
	)


def test_excess_decimal_places_are_truncated_not_rounded() -> None:
	"""Scale is enforced by truncating toward zero: 10.99999 percent -> 10,9999; 1.999 -> 1,99."""
	pairs = dict(_pairs(_first_inform(_doc(_inform(ativo_ext="10.99999", inv_inicial="1.999")))))
	assert pairs["ATIVO_EXT"] == "10,9999"
	assert pairs["INV_INICIAL"] == "1,99"


def test_a_tiny_negative_value_truncates_to_zero_without_a_sign() -> None:
	"""-0.001 on a signed 2-place field is 0,00, never -0,00."""
	doc = _doc(
		_inform(
			lista_comp_carteira={
				"pl_fundo": "-0.001",
				"comp_carteira": [{"especie_ativo": "x", "perc_pl": "1"}],
			}
		)
	)
	assert _pairs(_block(doc, "LISTA_COMP_CARTEIRA"))[0] == ("PL_FUNDO", "0,00")


@pytest.mark.parametrize(
	"field",
	[
		"inv_inicial",
		"inv_adic",
		"resg_min",
		"valor_perm",
		"ativo_ext",
		"cred_priv",
		"perc_max",
		"alav",
	],
)
def test_non_negative_fields_refuse_negative_values(field: str) -> None:
	"""Minimums, limits and shares cannot be negative."""
	_rejects(**{field: "-1"})


@pytest.mark.parametrize("field", ["ativo_ext", "cred_priv", "perc_max"])
def test_shares_are_capped_at_one_hundred(field: str) -> None:
	"""100 is accepted, anything above is refused (PERC_MAX states 100,00 as its maximum)."""
	_doc(_inform(**{field: "100"}))
	_rejects(**{field: "100.0001"})


def test_leverage_has_no_upper_bound_and_may_be_omitted() -> None:
	"""ALAV above 100 is valid; its absence means no limit and writes no tag."""
	_doc(_inform(alav="1000"))
	assert "ALAV" not in dict(_pairs(_first_inform(_doc(_inform()))))


def test_a_value_wider_than_the_digit_cap_is_refused() -> None:
	"""A huge magnitude fails instead of being written."""
	_rejects(inv_inicial="1e40")
	_rejects(inv_inicial="9" * 17)


def test_signed_fields_accept_negative_values() -> None:
	"""Returns, PL_FUNDO, AJUSTE_PERFOR and hypothetical returns may be negative."""
	_doc(
		_full_inform()
		| {"lista_tab_rent_anual": {"tab_rent_anual": [{"ano_rent": 2024, "rent_liq": "-150"}]}}
	)


def test_fee_rates_and_expenses_are_non_negative_and_capped() -> None:
	"""TX_ADM, TX_ENTR, TX_SAIDA and DESPESAS stay within 0 to 100."""
	_rejects(infor_tx_adm={"tipo_tx_adm": "F", "tx_adm": "-1"})
	_rejects(infor_tx_adm={"tipo_tx_adm": "F", "tx_adm": "101"})
	_rejects(infor_tx_entr={"tx_entr": "-1", "cond_entr": "x"})
	_rejects(infor_tx_saida={"dias_saida": 1, "tx_saida": "101", "cond_saida": "x"})


def test_cost_example_money_that_cannot_be_negative_is_refused() -> None:
	"""VALOR_RESG, IMPOSTOS, VALOR_ING, VALOR_SAIDA, VALOR_DESPESAS and the expense projections."""
	example = _full_inform()["inform_exemplo_comp"]
	for field in ("valor_resg", "impostos", "valor_ing", "valor_saida", "valor_despesas"):
		_rejects(inform_exemplo_comp={**example, field: "-1"})
	sim = _full_inform()["tab_simul_despesas"]
	for field in ("desp_prev3", "desp_prev5"):
		_rejects(tab_simul_despesas={**sim, field: "-1"})


# --- validation: integers and codes -------------------------------------------------------


@pytest.mark.parametrize("bad", [-1, 32768, 1.0, "3", True])
def test_shorts_are_strict_non_negative_16_bit_integers(bad: object) -> None:
	"""PRAZO_PAGAM refuses negatives, overflow, floats, numeric strings and bool."""
	_rejects(prazo_pagam=bad)
	assert dict(_pairs(_first_inform(_doc(_inform(prazo_pagam=32767)))))["PRAZO_PAGAM"] == "32767"


@pytest.mark.parametrize("bad", [0, 6, 2.0, "3", True])
def test_risk_class_is_an_integer_from_one_to_five(bad: object) -> None:
	"""CLASSIF_RISCO is 1 to 5."""
	_rejects(classif_risco=bad)


@pytest.mark.parametrize("bad", ["0", "3", "", "um", 1])
def test_payment_day_type_is_the_string_1_or_2(bad: object) -> None:
	"""TP_PRAZO_DIAS accepts only the strings 1 and 2."""
	_rejects(tp_prazo_dias=bad)
	_doc(_inform(tp_prazo_dias="2"))


@pytest.mark.parametrize("field", ["utiliz_deriv_apenas_protecao_cart", "perdas_sign", "pl_negat"])
@pytest.mark.parametrize("bad", ["s", "sim", "", "SN", True])
def test_flags_are_s_or_n(field: str, bad: object) -> None:
	"""The S/N flags accept exactly S or N."""
	_rejects(**{field: bad})


@pytest.mark.parametrize("bad", ["a", "", "AF", "aberta"])
def test_conversion_basis_is_a_or_f(bad: str) -> None:
	"""ABERT_FECH and ABERT_FECH_C accept only A or F."""
	conv = {"abert_fech": "A", "dia_aplic": 1, "abert_fech_c": "F", "dia_resg": 2}
	_rejects(conversao={**conv, "abert_fech": bad})
	_rejects(conversao={**conv, "abert_fech_c": bad})


@pytest.mark.parametrize(
	"bad",
	[
		"",
		"0",
		"01140041234",
		"11 4004 1234",
		"1140041234\n",
		"(11)40041234",
		"９９",
		"9" * 20,
		"9223372036854775808",
	],
)
def test_phone_is_digits_only_without_zero_filler(bad: str) -> None:
	"""TEL_SAC is a long: digits only, no leading zero, within 64 bits."""
	_rejects(tel_sac=bad)


def test_phone_accepts_the_largest_long() -> None:
	"""2**63 - 1 is the edge that still fits."""
	_doc(_inform(tel_sac="9223372036854775807"))


@pytest.mark.parametrize("bad", ["", " ", "x" * 51, "a\x00b"])
def test_subclass_code_is_a_bounded_non_empty_text(bad: str) -> None:
	"""COD_SUBCLASSE: non-blank, at most 50 characters, no control characters."""
	_rejects(cnpj_fundo=None, cod_subclasse=bad)


def test_subclass_code_at_the_limit_is_accepted() -> None:
	"""Fifty characters pass."""
	_doc(_inform(cnpj_fundo=None, cod_subclasse="x" * 50))


@pytest.mark.parametrize("bad", ["11222333000180", "123", "", "11.222.333/0001-81\n"])
def test_cnpj_is_check_digit_validated(bad: str) -> None:
	"""CNPJ_FUNDO fails on wrong digits, wrong length, empty and a trailing newline."""
	_rejects(cnpj_fundo=bad)


def test_cnpj_is_stored_unmasked() -> None:
	"""A masked CNPJ is written bare."""
	doc = _doc(_inform(cnpj_fundo="11.222.333/0001-81"))
	assert dict(_pairs(_first_inform(doc)))["CNPJ_FUNDO"] == VALID_CNPJ


# --- validation: text ---------------------------------------------------------------------


@pytest.mark.parametrize(
	("field", "limit"),
	[
		("nome_fantasia", 500),
		("end_eletr", 100),
		("desc_pub_alvo", 1000),
		("restr_inv", 500),
		("desc_objet", 1000),
		("desc_pol_inv", 1000),
		("obs_hor_apl_resg", 500),
		("tx_desempenho", 500),
		("ds_forma_remun_distr", 900),
		("princ_distr_oferta", 300),
		("princ_conflito_interes", 600),
		("reclamacoes", 50),
		("info_adic", 500),
	],
)
def test_text_fields_enforce_the_pages_lengths(field: str, limit: int) -> None:
	"""Each text field accepts exactly "até N casas" and refuses N + 1 or blank."""
	_doc(_inform(**{field: "x" * limit}))
	_rejects(**{field: "x" * (limit + 1)})
	_rejects(**{field: ""})
	_rejects(**{field: "   "})


def test_optional_text_fields_enforce_their_lengths_too() -> None:
	"""IND_REFER (20), COMENTARIOS (500), ESCLAREC (500) and the rest of the optional text."""
	_rejects(infor_tab_rent_anual={"ind_refer": "x" * 21})
	_doc(_inform(infor_tab_rent_anual={"ind_refer": "x" * 20}))
	_rejects(infor_tx_adm={"tipo_tx_adm": "F", "tx_adm": "1", "esclarec": "x" * 501})
	_rejects(infor_tx_adm={"tipo_tx_adm": "F", "tx_adm": "1", "esclarec": ""})
	_rejects(form_calc_rent="x" * 501)
	_rejects(carencia={"dias_car": 1, "cond_car": "x" * 501})
	_rejects(
		infor_despesas={
			"despesas": "1",
			"inic_periodo": "01/01/2024",
			"fim_periodo": "01/01/2024",
			"end_elet_adm": "x" * 101,
		}
	)
	_rejects(
		lista_comp_carteira={
			"pl_fundo": "1",
			"comp_carteira": [{"especie_ativo": "x" * 501, "perc_pl": "1"}],
		}
	)


@pytest.mark.parametrize("bad", ["a\x00b", "a\x07b", "a\rb", "a\x7fb", "Ω", "😀", "a\x81b"])
def test_text_rejects_control_and_unencodable_characters(bad: str) -> None:
	"""Control characters and anything windows-1252 cannot encode are refused at validation."""
	_rejects(nome_fantasia=bad)


def test_text_keeps_newlines_and_tabs() -> None:
	"""Newline and tab are legal in free text and round-trip."""
	doc = _doc(_inform(desc_objet="linha 1\nlinha 2\tfim"))
	assert dict(_pairs(_first_inform(doc)))["DESC_OBJET"] == "linha 1\nlinha 2\tfim"


# --- validation: structure and cross-field rules ------------------------------------------


def test_exactly_one_fund_identifier_is_required() -> None:
	"""Both or neither of CNPJ_FUNDO and COD_SUBCLASSE is refused."""
	_rejects(cod_subclasse="SUB-1")
	_rejects(cnpj_fundo=None)


def test_a_fund_cannot_appear_twice_in_a_file() -> None:
	"""A repeated CNPJ or subclass code is refused."""
	with pytest.raises(ValidationError):
		_doc(_inform(), _inform())
	sub = _inform(cnpj_fundo=None, cod_subclasse="S1")
	with pytest.raises(ValidationError):
		_doc(sub, copy.deepcopy(sub))
	_doc(_inform(), _inform(cnpj_fundo=None, cod_subclasse="S1"))


def test_a_file_holds_between_one_and_seventy_informs() -> None:
	"""Zero informs and 71 informs are refused; 70 distinct subclasses pass."""

	def sub(n: int) -> dict[str, object]:
		return _inform(cnpj_fundo=None, cod_subclasse=f"S{n}")

	_doc(*[sub(n) for n in range(70)])
	with pytest.raises(ValidationError):
		_doc(*[sub(n) for n in range(71)])
	with pytest.raises(ValidationError):
		_doc()


@pytest.mark.parametrize(
	"bad", [{"cod_doc": 1}, {"cod_doc": 25}, {"cod_doc": "24"}, {"versao": "4.0"}]
)
def test_header_constants_are_fixed(bad: dict[str, object]) -> None:
	"""COD_DOC is 24 and VERSAO is 3.0; other values are refused."""
	with pytest.raises(ValidationError):
		_doc(_inform(), **bad)


@pytest.mark.parametrize(
	"fee",
	[
		pytest.param({"tipo_tx_adm": "F"}, id="fixed-without-tx_adm"),
		pytest.param({"tipo_tx_adm": "F", "tx_adm": "1", "tx_min": "1"}, id="fixed-with-tx_min"),
		pytest.param({"tipo_tx_adm": "F", "tx_adm": "1", "tx_max": "1"}, id="fixed-with-tx_max"),
		pytest.param({"tipo_tx_adm": "V"}, id="variable-without-bounds"),
		pytest.param({"tipo_tx_adm": "V", "tx_min": "1"}, id="variable-without-tx_max"),
		pytest.param({"tipo_tx_adm": "V", "tx_max": "1"}, id="variable-without-tx_min"),
		pytest.param(
			{"tipo_tx_adm": "V", "tx_min": "1", "tx_max": "2", "tx_adm": "1"},
			id="variable-with-tx_adm",
		),
		pytest.param(
			{"tipo_tx_adm": "V", "tx_min": "2", "tx_max": "1"}, id="variable-min-above-max"
		),
	],
)
def test_management_fee_rejects_fields_inconsistent_with_its_type(fee: dict[str, str]) -> None:
	"""A fixed fee takes only TX_ADM; a variable fee takes TX_MIN <= TX_MAX and no TX_ADM."""
	_rejects(infor_tx_adm=fee)


def test_variable_fee_accepts_equal_bounds() -> None:
	"""TX_MIN equal to TX_MAX is a valid variable fee."""
	_doc(_inform(infor_tx_adm={"tipo_tx_adm": "V", "tx_min": "1", "tx_max": "1"}))


def test_fee_type_is_f_or_v() -> None:
	"""TIPO_TX_ADM accepts only F or V."""
	_rejects(infor_tx_adm={"tipo_tx_adm": "X", "tx_adm": "1"})


def test_portfolio_has_between_one_and_five_asset_types() -> None:
	"""COMP_CARTEIRA repeats 1 to 5 times."""
	asset = {"especie_ativo": "x", "perc_pl": "1"}
	_doc(_inform(lista_comp_carteira={"pl_fundo": "1", "comp_carteira": [asset] * 5}))
	_rejects(lista_comp_carteira={"pl_fundo": "1", "comp_carteira": [asset] * 6})
	_rejects(lista_comp_carteira={"pl_fundo": "1", "comp_carteira": []})


def test_annual_table_has_between_one_and_five_distinct_years() -> None:
	"""TAB_RENT_ANUAL: at most 5 rows, no repeated year, at least one when the list exists."""

	def rows(years: list[int]) -> dict[str, object]:
		return {"tab_rent_anual": [{"ano_rent": y, "rent_liq": "1"} for y in years]}

	_doc(_inform(lista_tab_rent_anual=rows([2020, 2021, 2022, 2023, 2024])))
	_rejects(lista_tab_rent_anual=rows([2019, 2020, 2021, 2022, 2023, 2024]))
	_rejects(lista_tab_rent_anual=rows([2024, 2024]))
	_rejects(lista_tab_rent_anual=rows([]))
	_rejects(lista_tab_rent_anual=rows([1899]))


def test_monthly_table_has_between_one_and_twelve_distinct_months() -> None:
	"""TAB_RENT_MENSAL: months 1 to 12, at most 12 rows, no repeats."""

	def rows(months: list[int]) -> dict[str, object]:
		return {"tab_rent_mensal": [{"mes": m, "rent_mens": "1"} for m in months]}

	_doc(_inform(lista_tab_rent_mensal=rows(list(range(1, 13)))))
	_rejects(lista_tab_rent_mensal=rows([1, 1]))
	_rejects(lista_tab_rent_mensal=rows([0]))
	_rejects(lista_tab_rent_mensal=rows([13]))
	_rejects(lista_tab_rent_mensal=rows([]))
	_rejects(lista_tab_rent_mensal=rows(list(range(1, 13)) + [1]))


def test_years_before_the_fund_existed_do_not_overlap_reported_years() -> None:
	"""ANTES_INIC2 lists years with no data, so a year cannot also have a return row."""
	rent = {"tab_rent_anual": [{"ano_rent": 2022, "rent_liq": "1"}]}
	_rejects(infor_tab_rent_anual={"antes_inic2": {"ano": [2022]}}, lista_tab_rent_anual=rent)
	_doc(_inform(infor_tab_rent_anual={"antes_inic2": {"ano": [2021]}}, lista_tab_rent_anual=rent))
	_rejects(infor_tab_rent_anual={"antes_inic2": {"ano": [2021, 2021]}})
	_rejects(infor_tab_rent_anual={"antes_inic2": {"ano": []}})


def test_reference_index_columns_need_a_reference_index() -> None:
	"""RENT_IND_REF and the per-row index columns are only valid when IND_REFER is given."""
	_rejects(infor_tab_rent_anual={"rent_ind_ref": "1"})
	_rejects(
		lista_tab_rent_anual={
			"tab_rent_anual": [{"ano_rent": 2024, "rent_liq": "1", "var_ind_ref": "1"}]
		}
	)
	_rejects(
		lista_tab_rent_anual={
			"tab_rent_anual": [{"ano_rent": 2024, "rent_liq": "1", "rent_perc_ind_ref": "0"}]
		}
	)
	_rejects(
		lista_tab_rent_mensal={
			"tab_rent_mensal": [{"mes": 1, "rent_mens": "1", "var_mens_ind_ref": "0"}]
		}
	)
	_rejects(
		lista_tab_rent_mensal={
			"tab_rent_mensal": [{"mes": 1, "rent_mens": "1", "rent_mens_perc_ind_ref": "1"}]
		}
	)
	_doc(
		_inform(
			infor_tab_rent_anual={"ind_refer": "CDI", "rent_ind_ref": "1"},
			lista_tab_rent_anual={
				"tab_rent_anual": [{"ano_rent": 2024, "rent_liq": "1", "var_ind_ref": "0"}]
			},
		)
	)


def test_years_in_return_rows_are_four_digit_years() -> None:
	"""A year of 0, 99 or 10000 is refused."""
	for year in (0, 99, 10000, 2024.0, "2024"):
		_rejects(lista_tab_rent_anual={"tab_rent_anual": [{"ano_rent": year, "rent_liq": "1"}]})


def test_years_since_losing_value_is_between_zero_and_five() -> None:
	"""ANOS_ABAIXO counts years among the last five."""
	for bad in (-1, 6, 1.0):
		_rejects(infor_tab_rent_anual={"anos_abaixo": bad})
	_doc(_inform(infor_tab_rent_anual={"anos_abaixo": 0}))
	_doc(_inform(infor_tab_rent_anual={"anos_abaixo": 5}))


def test_cost_example_years_must_be_consecutive() -> None:
	"""ANO_ANT is the year immediately before ANO_EMISS."""
	base = {"valor_resg": "1", "impostos": "0", "valor_despesas": "0"}
	_doc(_inform(inform_exemplo_comp={**base, "ano_ant": 2023, "ano_emiss": 2024}))
	_rejects(inform_exemplo_comp={**base, "ano_ant": 2022, "ano_emiss": 2024})
	_rejects(inform_exemplo_comp={**base, "ano_ant": 2024, "ano_emiss": 2024})


def test_models_reject_unknown_fields_and_are_immutable() -> None:
	"""An unknown field is refused and a built document cannot be edited in place."""
	_rejects(campo_inventado="x")
	_rejects(
		conversao={"abert_fech": "A", "dia_aplic": 1, "abert_fech_c": "F", "dia_resg": 2, "x": 1}
	)
	doc = _doc(_inform())
	with pytest.raises(ValidationError):
		doc.informs[0].nome_fantasia = "outro"  # type: ignore[misc]


def test_mandatory_blocks_cannot_be_omitted() -> None:
	"""CONVERSAO, INFOR_TX_ADM and the mandatory scalars are required."""
	for field in (
		"conversao",
		"infor_tx_adm",
		"classif_risco",
		"tel_sac",
		"info_adic",
		"hor_apl_resg",
		"tx_desempenho",
		"ativo_ext",
		"perc_max",
	):
		kwargs = _inform()
		del kwargs[field]
		with pytest.raises(ValidationError):
			_doc(kwargs)


def test_lamina_is_exported_from_the_submission_package() -> None:
	"""The writer and its document model are public names of the submission section."""
	import filings_cvm.submission as submission

	assert {"Lamina", "LaminaDocument", "LaminaInform", "LaminaHeader"} <= set(submission.__all__)
