"""Unit tests for the Informe Mensal FIDC (ICVM 576) submission writer.

Expected tags, order, scales and rules are taken from the CVM page
``PadraoXMLMensalFIDC576.asp``, not from the code under test.
"""

from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
import re
import types
from typing import Any, Literal, Union, get_args, get_origin

from pydantic import BaseModel, ValidationError
import pytest

from filings_cvm.submission import InfMensalFidc, InfMensalFidcDocument


# Valid check digits under the repo's routines (same fixtures as the sibling writers).
VALID_CNPJ = "11222333000181"
VALID_CPF = "52998224725"

# Direct children of LISTA_INFORM, in the order the page's template lists them.
SPEC_LISTA_INFORM_ORDER = [
	"APLIC_ATIVO",
	"CART_SEGMT",
	"PASSIV",
	"PATRLIQ",
	"COMPMT_DICRED_AQUIS",
	"COMPMT_DICRED_SEM_AQUIS",
	"NEGOC_DICRED_MES",
	"INFORM",
	"TAXA_NEGOC_DICRED_MES",
	"OUTRAS_INFORM",
]


def _value_for(annotation: Any, name: str) -> Any:  # noqa: ANN401
	"""Build a zero/neutral value for a required field annotation."""
	origin = get_origin(annotation)
	if origin is list:
		return [_value_for(get_args(annotation)[0], name)]
	if origin is Literal:
		return get_args(annotation)[0]
	if origin in (Union, types.UnionType):
		return _value_for(next(a for a in get_args(annotation) if a is not type(None)), name)
	if isinstance(annotation, type) and issubclass(annotation, BaseModel):
		return _zeros(annotation)
	if annotation is Decimal:
		return "0"
	if annotation is int:
		return 0
	if name == "dt_compt":
		return "10/2020"
	return VALID_CNPJ


def _zeros(model: type[BaseModel]) -> dict[str, Any]:
	"""Build a fully-populated all-zero payload (every mandatory tag "preenchida com zero")."""
	return {
		name: _value_for(info.annotation, name)
		for name, info in model.model_fields.items()
		if info.is_required()
	}


def _doc(mutate: Callable[[dict[str, Any]], None] | None = None) -> InfMensalFidcDocument:
	"""Build a closed-fund document from zeros, optionally mutating the raw payload first."""
	data = _zeros(InfMensalFidcDocument)
	data["cab_inform"]["tp_condominio"] = "FECHADO"
	if mutate is not None:
		mutate(data)
	return InfMensalFidcDocument.model_validate(data)


def _xml(doc: InfMensalFidcDocument) -> str:
	"""Export to a string."""
	out = InfMensalFidc().export(doc)
	assert out is not None
	return out


def test_export_minimal_document_has_root_namespace_and_header_in_spec_order() -> None:
	"""The envelope and CAB_INFORM follow the template of the page."""
	xml = _xml(_doc())
	assert xml.startswith(
		'<?xml version="1.0" encoding="windows-1252"?>\n<DOC_ARQ xmlns="urn:fidc">'
	)
	assert xml.endswith("</DOC_ARQ>")
	header_tags = re.findall(r"<(\w+)>", xml.split("</CAB_INFORM>")[0])
	assert header_tags == [
		"CAB_INFORM",
		"DT_COMPT",
		"NR_CNPJ_ADM",
		"NR_CNPJ_FUNDO",
		"TP_CONDOMINIO",
		"FDO_EXCL",
		"COTST_VINCUL",
	]
	assert "<DT_COMPT>10/2020</DT_COMPT>" in xml
	assert "PR_ENTRE_RESGATE" not in xml  # open-fund-only tag, absent for FECHADO


def test_export_lista_inform_children_follow_template_order() -> None:
	"""LISTA_INFORM children appear in the page's order, each exactly once."""
	xml = _xml(_doc())
	body = xml.split("<LISTA_INFORM>")[1].split("</LISTA_INFORM>")[0]
	top = re.findall(r"^ {8}<(\w+)>", body, flags=re.MULTILINE)
	assert top == SPEC_LISTA_INFORM_ORDER


def test_export_mandatory_empty_blocks_are_emitted_as_empty_tags() -> None:
	"""Tabela X items 3 and 7: NUM_COTISTAS_DESC and DESEMP are mandatory but may be empty."""
	xml = _xml(_doc())
	assert "<NUM_COTISTAS_DESC></NUM_COTISTAS_DESC>" in xml
	assert "<DESEMP></DESEMP>" in xml
	assert "<LISTA_CEDENT>" not in xml  # optional list omitted


def test_export_decimals_use_comma_and_spec_scales() -> None:
	"""2 casas for money, up to 8 for quota unit values/quantities; excess is truncated."""

	def mutate(data: dict[str, Any]) -> None:
		outras = data["lista_inform"]["outras_inform"]
		outras["desc_serie_classe"]["desc_serie_classe_senior"][0] = {
			"qt_cotas": "1234.123456789",
			"vl_cotas": "1.5",
		}
		outras["capta_resga_amorti"]["capt_mes"]["classe_senior"][0] = {
			"qt_cotas": "2.123456789",
			"vl_cotas": "10.999",
		}

	xml = _xml(_doc(mutate))
	assert "<QT_COTAS>1234,12345678</QT_COTAS>" in xml
	assert "<VL_COTAS>1,50000000</VL_COTAS>" in xml
	assert "<QT_COTAS>2,12345678</QT_COTAS>" in xml
	assert "<VL_COTAS>10,99</VL_COTAS>" in xml  # truncated, not rounded to 11,00
	assert "<VL_DISPONIB>0,00</VL_DISPONIB>" in xml


def test_export_repeats_series_and_aliased_tags() -> None:
	"""One CLASSE_SENIOR per series, and block-prefixed tags keep their page names."""

	def mutate(data: dict[str, Any]) -> None:
		num = data["lista_inform"]["outras_inform"]["num_cotistas"]
		num.update(qt_total_cotistas=5, qt_total_cotistas_senior=5)
		num["classe_senior"] = [{"vl_classe": 2}, {"vl_classe": 3}]

	xml = _xml(_doc(mutate))
	assert xml.count("<VL_CLASSE>") == 2
	assert "<TAXA_NEGOC_DICRED_MES_AQUIS_DESC_COMPRA>" in xml
	assert "<TAXA_NEGOC_DICRED_MES_ATIV_RF_JUROS_VENDA>" in xml


def test_export_open_fund_emits_redemption_terms_and_liquidity() -> None:
	"""Open funds carry the four PR_/TP_ tags and at least one LIQUIDEZ field."""

	def mutate(data: dict[str, Any]) -> None:
		data["cab_inform"].update(
			tp_condominio="ABERTO",
			pr_entre_resgate=30,
			tp_dias_resgate="2",
			pr_entre_conver=2,
			tp_dias_conver="1",
		)
		data["lista_inform"]["outras_inform"]["liquidez"] = {"vl_ativ_liqdez": "1.00"}

	xml = _xml(_doc(mutate))
	assert "<PR_ENTRE_RESGATE>30</PR_ENTRE_RESGATE>" in xml
	assert "<TP_DIAS_CONVER>1</TP_DIAS_CONVER>" in xml
	assert "<VL_ATIV_LIQDEZ>1,00</VL_ATIV_LIQDEZ>" in xml
	assert "VL_ATIV_LIQDEZ_30" not in xml  # unfilled horizons are omitted


def test_export_to_file_writes_windows_1252_and_returns_none(tmp_path: Path) -> None:
	"""With an output path the file is written and nothing is returned."""
	target = tmp_path / "fidc.xml"
	assert InfMensalFidc().export(_doc(), str(target)) is None
	assert target.read_bytes().decode("windows-1252").startswith("<?xml")


def test_totals_that_match_the_spec_sums_are_accepted() -> None:
	"""Item 16 (net equity) with a non-zero value and the 4,2-scale truncation."""

	def mutate(data: dict[str, Any]) -> None:
		data["lista_inform"]["patrliq"].update(vl_som_patrliq="100.99", vl_patrim_liq="100.999")

	assert "<VL_SOM_PATRLIQ>100,99</VL_SOM_PATRLIQ>" in _xml(_doc(mutate))


def test_sacado_with_placeholder_document_is_accepted() -> None:
	"""The page prescribes 99.999.999/9999-99 for debtors with no CNPJ."""

	def mutate(data: dict[str, Any]) -> None:
		sac = data["lista_inform"]["inform"]["lista_dev_sacados"]["dev_sacados"][0]
		sac["nr_pf_pj_sacado_deved_1"] = "99.999.999/9999-99"

	assert "99.999.999/9999-99" in _xml(_doc(mutate))


# ----------------------------------------------------------------- negative cases


def test_invalid_fund_cnpj_is_rejected() -> None:
	"""CNPJ with bad check digits fails the page's 'CPF/CNPJ tem que ser válidos'."""
	with pytest.raises(ValidationError, match="CNPJ"):
		_doc(lambda d: d["cab_inform"].update(nr_cnpj_fundo="11222333000182"))


@pytest.mark.parametrize("value", ["2020-10", "13/2020", "10/20", "00/2020"])
def test_competence_must_be_mm_aaaa(value: str) -> None:
	"""DT_COMPT is MM/AAAA."""
	with pytest.raises(ValidationError, match="MM/AAAA"):
		_doc(lambda d: d["cab_inform"].update(dt_compt=value))


def test_closed_fund_must_not_carry_redemption_terms() -> None:
	"""Cabeçalho item 1: the four tags are restricted to open funds."""
	with pytest.raises(ValidationError, match="open funds"):
		_doc(lambda d: d["cab_inform"].update(pr_entre_resgate=30))


def test_open_fund_without_liquidity_is_rejected() -> None:
	"""Open fund: 'no item Liquidez, pelo menos um dos campos deve ser preenchido'."""
	with pytest.raises(ValidationError, match="LIQUIDEZ"):
		_doc(lambda d: d["cab_inform"].update(tp_condominio="ABERTO"))


def test_somatorio_that_disagrees_with_its_terms_is_rejected() -> None:
	"""Item 16: VL_SOM_PATRLIQ must equal the net equity."""
	with pytest.raises(ValidationError, match="SOMATÓRIO"):
		_doc(lambda d: d["lista_inform"]["patrliq"].update(vl_patrim_liq="10.00"))


def test_provision_above_covered_credits_is_rejected() -> None:
	"""The provision must be <= the sum of the credits it covers."""

	def mutate(data: dict[str, Any]) -> None:
		data["lista_inform"]["aplic_ativo"]["cred_existe"]["vl_provis_reduc_recup"] = "5.00"

	with pytest.raises(ValidationError, match="PROVIS"):
		_doc(mutate)


def test_quota_holder_total_must_match_series_counts() -> None:
	"""Tabela X item 4: QT_TOTAL_COTISTAS_SENIOR is the sum of the series' VL_CLASSE."""

	def mutate(data: dict[str, Any]) -> None:
		num = data["lista_inform"]["outras_inform"]["num_cotistas"]
		num.update(qt_total_cotistas=3, qt_total_cotistas_senior=3)

	with pytest.raises(ValidationError, match="QT_TOTAL_COTISTAS_SENIOR"):
		_doc(mutate)


def test_sacado_with_invalid_document_is_rejected() -> None:
	"""Debtor documents must be valid CPF/CNPJ (or the prescribed placeholders)."""

	def mutate(data: dict[str, Any]) -> None:
		sac = data["lista_inform"]["inform"]["lista_dev_sacados"]["dev_sacados"][0]
		sac["nr_pf_pj_sacado_deved_1"] = "12345678901"

	with pytest.raises(ValidationError, match="CPF/CNPJ"):
		_doc(mutate)


def test_informe_without_any_sacado_is_rejected() -> None:
	"""'Não aceitar o envio sem ter pelo menos a informação de um Sacado/Devedor'."""

	def mutate(data: dict[str, Any]) -> None:
		data["lista_inform"]["inform"]["lista_dev_sacados"]["dev_sacados"] = []

	with pytest.raises(ValidationError, match=r"(?s)dev_sacados.*at least 1 item"):
		_doc(mutate)


def test_informe_without_senior_series_is_rejected() -> None:
	"""Tabela X item 5: at least one senior series is mandatory."""

	def mutate(data: dict[str, Any]) -> None:
		data["lista_inform"]["outras_inform"]["rent_mes"]["rent_classe_senior"] = []

	with pytest.raises(ValidationError, match=r"(?s)rent_classe_senior.*at least 1 item"):
		_doc(mutate)


def test_unknown_tag_is_rejected() -> None:
	"""Blocks forbid extra fields, so a misspelt tag cannot be silently dropped."""
	with pytest.raises(ValidationError, match=r"(?s)vl_patrim_liquido.*Extra inputs"):
		_doc(lambda d: d["lista_inform"]["patrliq"].update(vl_patrim_liquido="1"))


def test_cpf_sacado_is_accepted() -> None:
	"""A valid CPF is a legal debtor document."""

	def mutate(data: dict[str, Any]) -> None:
		sac = data["lista_inform"]["inform"]["lista_dev_sacados"]["dev_sacados"][0]
		sac["nr_pf_pj_sacado_deved_1"] = VALID_CPF

	assert VALID_CPF in _xml(_doc(mutate))
