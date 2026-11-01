"""Unit tests for the Extrato V3 submission writer (tags typed from PadraoXMLInfExtratoV3.asp)."""

from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET  # noqa: S405  # parses our own output in tests

from pydantic import ValidationError
import pytest

from filings_cvm.submission import (
	Extrato,
	ExtratoDocument,
	ExtratoHeader,
	ExtratoRow,
)


_NS = "{urn:extr}"
_CNPJ = "11222333000181"

# Tag lists typed from the page's sample file, in its order.
HEADER_TAGS = ["COD_DOC", "VERSAO", "DT_GERAC_ARQ"]
ROW_TAGS = [
	"CNPJ_FDO",
	"FORMA_CONDOMINIO",
	"PRAZO",
	"PUBLICO_ALVO",
	"FUNDO_ANBIMA",
	"COD_DISTR_FDO",
	"COD_POLIT_INVEST",
	"MAX_APP_COTAS_FUNDO",
	"RESULTADO_ATR_CARTEIRA",
	"FUNDO_INVERT_COTAS",
	"APLICACAO_MINIMA_FUNDO",
	"VALOR_COTA",
	"TIPO_VALOR_COTA",
	"VALOR_COTA_BASE_PL",
	"QT_DIA_CONV_COTA",
	"QT_DIA_PAGAM_COTA",
	"RESG_COTAS",
	"PRAZO_PAGAM_RESG",
	"TAXA_ADM",
	"TAXA_MAXIMA_CUSTODIA",
	"TX_PERFM",
	"TX_INGRESSO",
	"TX_SAIDA",
	"OPER_DERIV",
	"OPER_PATRIM_LIQ",
	"MERCADO_SEM_CONTRAPARTE_CENTRAL",
	"ATIV_EXTER",
	"FUNDO_ATIVOS",
	"REGULAMENTO_TIPO_EMISSOR",
	"REGULAMENTO_MODALIDADE_ATIVO",
]
BLOCK_TAGS = {
	"FORMA_CONDOMINIO": ["TIPO_CONDOMINIO", "ABERTA_NEG_MER_ORGAN", "LISTA_MERC_BLOQUEIO"],
	"PRAZO": ["TIPO_PRAZO", "DETALHAMENTO_PRAZO"],
	"FUNDO_ANBIMA": ["ANBIMA", "COD_CLASSIFICACAO"],
	"FUNDO_INVERT_COTAS": ["TIPO_FUNDO_INVERT", "TIPO_FUNDO"],
	"VALOR_COTA": ["ATUALIZADO_DIARIAMENTE", "PRAZO_ATUALIZACAO"],
	"RESG_COTAS": ["CARENCIA_RESG_COTAS", "DIAS_RESG_COTAS"],
	"PRAZO_PAGAM_RESG": ["DIAS_SEM_TAXA", "DIAS_COM_TAXA", "TIPO_DE_CONTAGEM"],
	"TX_PERFM": ["COBRA_TX_PERFM", "CALC_TX_PERFM"],
	"CALC_TX_PERFM": [
		"TAXA_PERFORMANCE",
		"TP_TAXA_PERFORMANCE",
		"PER_INDICE_REFERENCIA",
		"CUPOM",
		"METODO_CALC_TAXA",
		"INFO_ADICIONAL",
	],
	"TX_INGRESSO": ["COBRA_TX_INGRESSO", "TP_VL_FIXO_TX_INGRESSO", "VL_FIXO_TX_INGRESSO"],
	"TX_SAIDA": ["COBRA_TX_SAIDA", "TP_VL_FIXO_TX_INGRESSO", "VL_FIXO_TX_SAIDA"],
	"OPER_DERIV": ["REALIZ_OPER_DERIV", "OPERACOES_DERIVATIVOS"],
	"OPER_PATRIM_LIQ": ["REALIZA_OPER_PATRIM_LIQ", "QT_OPER_PATRIM_LIQ"],
	"ATIV_EXTER": ["INVEST_EXTERIOR", "PR_MAX_APLIC_ATIV_EXTER"],
	"FUNDO_ATIVOS": ["ADQUIRA_CREDITO_PRIVADO", "LIMITE_MAXIMO"],
}
TIPO_EMISSOR_BASES = [
	"INSTITUICOES_FINANCEIRAS",
	"COMPANHIAS_ABERTAS",
	"FUNDOS_INVESTIMENTO",
	"UNIAO_FEDERAL",
	"ADMINISTRADOR_GESTOR_PESSOAS_LIGADAS",
	"OUTROS",
]
MODALIDADE_BASES = [
	"COTAS_FI_555",
	"COTAS_FIC_555",
	"COTAS_FI_555_INVEST_QUALIFICADOS",
	"COTAS_FIC_555_INVEST_QUALIFICADOS",
	"COTAS_FI_555_INVEST_PROFISSIONAIS",
	"COTAS_FIC_555_INVEST_PROFISSIONAIS",
	"COTAS_FII",
	"COTAS_FIDC",
	"COTAS_FICFIDC",
	"COTAS_FIDC_NP",
	"COTAS_FICFIDC_NP",
	"COTAS_FUNDOS_INDICE_MERCADO_ETF",
	"CRI",
	"TITULOS_PUBLICOS_OPERACOES",
	"OURO",
	"TITULOS_EMISSAO_COOBRIGACAO",
	"VALORES_MOBILIARIOS_ALINEA",
	"DEPOSITO_ACOES",
	"DEBENTURES",
	"NOTAS_PROMISSORIAS",
	"OPERACOES_COMPROMISSADAS",
	"DERIVATIVOS",
	"OUTROS",
	"COTAS_FMIEE",
	"COTAS_FIP",
	"COTAS_FICFIP",
]


def _pairs(bases: list[str], low: str = "1.00", high: str = "50.00") -> dict[str, str]:
	out: dict[str, str] = {}
	for base in bases:
		out[f"{base.lower()}_min"] = low
		out[f"{base.lower()}_max"] = high
	return out


def _row(**over: object) -> dict[str, object]:
	row: dict[str, object] = {
		"cnpj_fdo": _CNPJ,
		"forma_condominio": {"tipo_condominio": "ABERTO"},
		"prazo": {"tipo_prazo": "INDETERMINADO"},
		"fundo_anbima": {"anbima": "N"},
		"cod_polit_invest": 1,
		"max_app_cotas_fundo": "10.5",
		"resultado_atr_carteira": "S",
		"fundo_invert_cotas": {"tipo_fundo_invert": "N"},
		"valor_cota": {"atualizado_diariamente": "S"},
		"resg_cotas": {"carencia_resg_cotas": "N"},
		"tx_perfm": {"cobra_tx_perfm": "N"},
		"tx_ingresso": {"cobra_tx_ingresso": "N"},
		"tx_saida": {"cobra_tx_saida": "N"},
		"oper_deriv": {"realiz_oper_deriv": "N"},
		"oper_patrim_liq": {"realiza_oper_patrim_liq": "N"},
		"mercado_sem_contraparte_central": "N",
		"ativ_exter": {"invest_exterior": "N"},
		"fundo_ativos": {"adquira_credito_privado": "N"},
		"regulamento_tipo_emissor": _pairs(TIPO_EMISSOR_BASES),
		"regulamento_modalidade_ativo": _pairs(MODALIDADE_BASES),
	}
	row.update(over)
	return row


def _doc(**over: object) -> ExtratoDocument:
	return ExtratoDocument(
		header=ExtratoHeader(dt_gerac_arq="31/10/2026"),
		rows=[ExtratoRow(**_row(**over))],
	)


def _tags(el: ET.Element) -> list[str]:
	return [c.tag.removeprefix(_NS) for c in el]


def _export(doc: ExtratoDocument) -> ET.Element:
	xml = Extrato().export(doc)
	assert xml is not None
	return ET.fromstring(xml.encode("windows-1252"))  # noqa: S314


def _full_row() -> dict[str, object]:
	return _row(
		forma_condominio={
			"tipo_condominio": "FECHADO",
			"aberta_neg_mer_organ": "S",
			"lista_merc_bloqueio": 2,
		},
		prazo={"tipo_prazo": "DETERMINADO", "detalhamento_prazo": "5 anos"},
		publico_alvo="INVESTIDORES QUALIFICADOS",
		fundo_anbima={"anbima": "S", "cod_classificacao": 12},
		cod_distr_fdo=2,
		fundo_invert_cotas={"tipo_fundo_invert": "S", "tipo_fundo": "FUNDO DE FUNDOS"},
		aplicacao_minima_fundo="100.50",
		valor_cota={"atualizado_diariamente": "N", "prazo_atualizacao": "Semanal"},
		tipo_valor_cota="DO DIA DA APLICACAO",
		valor_cota_base_pl="DO DIA ANTERIOR",
		qt_dia_conv_cota=1,
		qt_dia_pagam_cota=2,
		resg_cotas={"carencia_resg_cotas": "S", "dias_resg_cotas": 30},
		prazo_pagam_resg={"dias_sem_taxa": 1, "dias_com_taxa": 2, "tipo_de_contagem": "UTEIS"},
		taxa_adm="2.5",
		taxa_maxima_custodia="0.123456",
		tx_perfm={
			"cobra_tx_perfm": "S",
			"calc_tx_perfm": {
				"taxa_performance": "20",
				"tp_taxa_performance": 4,
				"per_indice_referencia": "100",
				"cupom": "6",
				"metodo_calc_taxa": "ATIVO",
			},
		},
		tx_ingresso={
			"cobra_tx_ingresso": "S",
			"tp_vl_fixo_tx_ingresso": "1",
			"vl_fixo_tx_ingresso": "1.5",
		},
		tx_saida={
			"cobra_tx_saida": "S",
			"tp_vl_fixo_tx_ingresso": "2",
			"vl_fixo_tx_saida": "10.25",
		},
		oper_deriv={"realiz_oper_deriv": "S", "operacoes_derivativos": "HEDGE"},
		oper_patrim_liq={"realiza_oper_patrim_liq": "S", "qt_oper_patrim_liq": "SL"},
		ativ_exter={"invest_exterior": "S", "pr_max_aplic_ativ_exter": "20"},
		fundo_ativos={"adquira_credito_privado": "S", "limite_maximo": "30.00"},
	)


def test_header_and_row_tags_follow_the_sample_order() -> None:
	"""Header and row tags follow the sample order."""
	root = _export(_doc())
	assert root.tag == f"{_NS}DOC_ARQ"
	assert _tags(root) == ["CAB_INFORM", "EXTRATO_FUNDO"]
	assert _tags(root[0]) == HEADER_TAGS
	assert [c.text for c in root[0]] == ["41", "3.0", "31/10/2026"]
	rows = list(root[1])
	assert [r.tag for r in rows] == [f"{_NS}ROW_EXTRATO"]
	expected = [
		t
		for t in ROW_TAGS
		if t
		not in {
			"PUBLICO_ALVO",
			"COD_DISTR_FDO",
			"APLICACAO_MINIMA_FUNDO",
			"TIPO_VALOR_COTA",
			"VALOR_COTA_BASE_PL",
			"QT_DIA_CONV_COTA",
			"QT_DIA_PAGAM_COTA",
			"PRAZO_PAGAM_RESG",
			"TAXA_ADM",
			"TAXA_MAXIMA_CUSTODIA",
		}
	]
	assert _tags(rows[0]) == expected


def test_every_block_emits_its_tag_list_when_fully_populated() -> None:
	"""Every block emits its tag list when fully populated."""
	root = ET.fromstring(  # noqa: S314
		Extrato()
		.export(
			ExtratoDocument(
				header=ExtratoHeader(dt_gerac_arq="01/01/2026"),
				rows=[ExtratoRow(**_full_row())],
			)
		)
		.encode("windows-1252")
	)
	row = root[1][0]
	assert _tags(row) == ROW_TAGS
	for name, tags in BLOCK_TAGS.items():
		block = next(el for el in row.iter() if el.tag == f"{_NS}{name}")
		if name in {"CALC_TX_PERFM"}:
			assert _tags(block) == [t for t in tags if t != "INFO_ADICIONAL"]
		else:
			assert _tags(block) == tags, name
	tipo = row.find(f"{_NS}REGULAMENTO_TIPO_EMISSOR")
	assert _tags(tipo) == [f"{b}_{s}" for b in TIPO_EMISSOR_BASES for s in ("MIN", "MAX")]
	modalidade = row.find(f"{_NS}REGULAMENTO_MODALIDADE_ATIVO")
	assert _tags(modalidade) == [f"{b}_{s}" for b in MODALIDADE_BASES for s in ("MIN", "MAX")]


def test_decimals_use_comma_and_truncate_with_stated_scales() -> None:
	"""Decimals use comma and truncate with stated scales."""
	row = _export(
		ExtratoDocument(
			header=ExtratoHeader(dt_gerac_arq="01/01/2026"),
			rows=[ExtratoRow(**_full_row())],
		)
	)[1][0]
	text = {el.tag.removeprefix(_NS): el.text for el in row.iter()}
	assert text["APLICACAO_MINIMA_FUNDO"] == "100,50"
	assert text["TAXA_MAXIMA_CUSTODIA"] == "0,123456"
	assert text["TAXA_ADM"] == "2,5000"
	assert text["QT_OPER_PATRIM_LIQ"] == "SL"
	assert text["LIMITE_MAXIMO"] == "30,00"
	assert text["OUTROS_MIN"] == "1,00"


def test_money_truncates_toward_zero() -> None:
	"""Money truncates toward zero."""
	row = ExtratoRow(**_row(aplicacao_minima_fundo="1.999"))
	assert row.aplicacao_minima_fundo == Decimal("1.99")


@pytest.mark.parametrize("bad", [1.5, True, "abc", "NaN", "-1"])
def test_decimal_refuses_float_bool_garbage_and_negative(bad: object) -> None:
	"""Decimal refuses float bool garbage and negative."""
	with pytest.raises(ValidationError):
		ExtratoRow(**_row(aplicacao_minima_fundo=bad))


def test_percentage_above_100_rejected() -> None:
	"""Percentage above 100 rejected."""
	with pytest.raises(ValidationError):
		ExtratoRow(**_row(max_app_cotas_fundo="100.01"))


@pytest.mark.parametrize(
	"cnpj", ["11.222.333/0001-81", "11222333000182", " 11222333000181", "1122233300018\n", "x"]
)
def test_cnpj_shape_and_check_digit(cnpj: str) -> None:
	"""Cnpj shape and check digit."""
	if cnpj == "11.222.333/0001-81":
		assert ExtratoRow(**_row(cnpj_fdo=cnpj)).cnpj_fdo == _CNPJ
		return
	with pytest.raises(ValidationError):
		ExtratoRow(**_row(cnpj_fdo=cnpj))


@pytest.mark.parametrize(
	"date", ["31/02/2026", "1/1/2026", "01/01/0001", "2026-01-01", "01/01/2026\n"]
)
def test_impossible_or_malformed_dates_rejected(date: str) -> None:
	"""Impossible or malformed dates rejected."""
	with pytest.raises(ValidationError):
		ExtratoHeader(dt_gerac_arq=date)


@pytest.mark.parametrize(
	("field", "value"),
	[
		("forma_condominio", {"tipo_condominio": "FECHADO"}),
		(
			"forma_condominio",
			{"tipo_condominio": "ABERTO", "aberta_neg_mer_organ": "N", "lista_merc_bloqueio": 1},
		),
		("prazo", {"tipo_prazo": "DETERMINADO"}),
		("fundo_anbima", {"anbima": "S"}),
		("fundo_anbima", {"anbima": "N", "cod_classificacao": 1}),
		("fundo_anbima", {"anbima": "S", "cod_classificacao": 69}),
		("fundo_invert_cotas", {"tipo_fundo_invert": "S"}),
		("valor_cota", {"atualizado_diariamente": "N"}),
		("resg_cotas", {"carencia_resg_cotas": "S"}),
		("resg_cotas", {"carencia_resg_cotas": "N", "dias_resg_cotas": 3}),
		("resg_cotas", {"carencia_resg_cotas": "S", "dias_resg_cotas": -1}),
		("tx_perfm", {"cobra_tx_perfm": "S"}),
		("tx_perfm", {"cobra_tx_perfm": "N", "calc_tx_perfm": {}}),
		("tx_ingresso", {"cobra_tx_ingresso": "S"}),
		(
			"tx_ingresso",
			{
				"cobra_tx_ingresso": "S",
				"tp_vl_fixo_tx_ingresso": "2",
				"vl_fixo_tx_ingresso": "1.005",
			},
		),
		(
			"tx_ingresso",
			{
				"cobra_tx_ingresso": "S",
				"tp_vl_fixo_tx_ingresso": "1",
				"vl_fixo_tx_ingresso": "100.0001",
			},
		),
		(
			"tx_saida",
			{"cobra_tx_saida": "S", "tp_vl_fixo_tx_ingresso": "1", "vl_fixo_tx_saida": "150"},
		),
		(
			"tx_saida",
			{"cobra_tx_saida": "S", "tp_vl_fixo_tx_ingresso": "3", "vl_fixo_tx_saida": "1"},
		),
		("oper_deriv", {"realiz_oper_deriv": "S"}),
		("oper_patrim_liq", {"realiza_oper_patrim_liq": "S"}),
		("ativ_exter", {"invest_exterior": "S"}),
		("fundo_ativos", {"adquira_credito_privado": "S"}),
		("regulamento_tipo_emissor", _pairs(TIPO_EMISSOR_BASES, "60", "10")),
	],
)
def test_block_per_answer_rules_are_enforced(field: str, value: object) -> None:
	"""Block per answer rules are enforced."""
	with pytest.raises(ValidationError):
		ExtratoRow(**_row(**{field: value}))


def test_performance_fee_rules_depend_on_the_investor() -> None:
	"""Performance fee rules depend on the investor."""
	calc_free = {"info_adicional": "critérios do regulamento"}
	tx = {"cobra_tx_perfm": "S", "calc_tx_perfm": calc_free}
	with pytest.raises(ValidationError):
		ExtratoRow(**_row(tx_perfm=tx))
	ok = ExtratoRow(**_row(tx_perfm=tx, publico_alvo="INVESTIDORES PROFISSIONAIS"))
	assert ok.tx_perfm.calc_tx_perfm.info_adicional is not None
	full = {
		"taxa_performance": "20",
		"tp_taxa_performance": 4,
		"per_indice_referencia": "100",
		"info_adicional": "extra text",
	}
	with pytest.raises(ValidationError):
		ExtratoRow(**_row(tx_perfm={"cobra_tx_perfm": "S", "calc_tx_perfm": full}))
	full["tp_taxa_performance"] = 36
	with pytest.raises(ValidationError):
		ExtratoRow(
			**_row(
				tx_perfm={"cobra_tx_perfm": "S", "calc_tx_perfm": full},
				publico_alvo="INVESTIDORES QUALIFICADOS",
			)
		)


@pytest.mark.parametrize("text", ["", "   ", "x" * 201, "bad\x00", "日本"])
def test_text_fields_are_non_empty_bounded_and_encodable(text: str) -> None:
	"""Text fields are non empty bounded and encodable."""
	with pytest.raises(ValidationError):
		ExtratoRow(**_row(prazo={"tipo_prazo": "DETERMINADO", "detalhamento_prazo": text}))


def test_document_needs_between_1_and_1000_rows_and_rejects_extras() -> None:
	"""Document needs between 1 and 1000 rows and rejects extras."""
	row = ExtratoRow(**_row())
	header = ExtratoHeader(dt_gerac_arq="01/01/2026")
	with pytest.raises(ValidationError):
		ExtratoDocument(header=header, rows=[])
	with pytest.raises(ValidationError):
		ExtratoDocument(header=header, rows=[row] * 1001)
	with pytest.raises(ValidationError):
		ExtratoHeader(dt_gerac_arq="01/01/2026", cod_doc=42)
	with pytest.raises(ValidationError):
		ExtratoRow(**_row(unknown=1))


def test_export_writes_windows_1252_bytes_and_returns_none(tmp_path: Path) -> None:
	"""Export writes windows 1252 bytes and returns none."""
	target = tmp_path / "e.xml"
	doc = _doc(
		fundo_invert_cotas={"tipo_fundo_invert": "S", "tipo_fundo": "FUNDO-ESPELHO"},
		publico_alvo="PÚBLICO EM GERAL",
	)
	assert Extrato().export(doc, str(target)) is None
	raw = target.read_bytes()
	assert raw.startswith(b'<?xml version="1.0" encoding="windows-1252"?>')
	assert "PÚBLICO EM GERAL".encode("windows-1252") in raw


def test_failed_export_does_not_wipe_an_existing_file(tmp_path: Path) -> None:
	"""Failed export does not wipe an existing file."""
	target = tmp_path / "e.xml"
	target.write_bytes(b"keep")
	bad = ExtratoRow.model_construct(**{**_row(), "cnpj_fdo": "日本"})
	doc = ExtratoDocument.model_construct(
		header=ExtratoHeader(dt_gerac_arq="01/01/2026"), rows=[bad]
	)
	with pytest.raises((ValueError, AttributeError, TypeError)):
		Extrato().export(doc, str(target))
	assert target.read_bytes() == b"keep"


def test_unencodable_text_raises_value_error_before_touching_the_file(tmp_path: Path) -> None:
	"""Unencodable text raises value error before touching the file."""
	target = tmp_path / "e.xml"
	target.write_bytes(b"keep")
	header = ExtratoHeader.model_construct(cod_doc=41, versao="3.0", dt_gerac_arq="日本")
	doc = ExtratoDocument.model_construct(header=header, rows=[])
	with pytest.raises(ValueError, match="windows-1252"):
		Extrato().export(doc, str(target))
	assert target.read_bytes() == b"keep"


def test_oversize_file_is_refused(tmp_path: Path) -> None:
	"""Oversize file is refused."""
	target = tmp_path / "e.xml"
	row = ExtratoRow(**_row())
	doc = ExtratoDocument.model_construct(
		header=ExtratoHeader(dt_gerac_arq="01/01/2026"), rows=[row] * 1000
	)
	with pytest.raises(ValueError, match="1 MB"):
		Extrato().export(doc, str(target))
	assert not target.exists()
