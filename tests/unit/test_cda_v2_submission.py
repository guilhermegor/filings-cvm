"""Unit tests for the CDA V2 submission writer.

Expectations come from the CVM page PadraoXMLCDANet.aspx (tag names and order, comma
decimals, Table A matrix, block x application-type relations), not from the writer.
"""
# ruff: noqa: S314  (parses the writer's own output, not untrusted input)

from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET

from pydantic import ValidationError
import pytest

from filings_cvm._internal.config.schemas.cda import CdaEmitter
from filings_cvm.submission import (
	CdaV2,
	CdaV2Aplic,
	CdaV2Cotas,
	CdaV2DemaisCodif,
	CdaV2DemaisNCodif,
	CdaV2Document,
	CdaV2Header,
	CdaV2Inform,
	CdaV2Negoc,
	CdaV2PosFim,
	CdaV2Swap,
	CdaV2SwapAplic,
	CdaV2SwapNegoc,
	CdaV2SwapPosFim,
	CdaV2TitPub,
)


NS = "{urn:cda}"
CNPJ = "11222333000181"


def _aplic(code: int = 37, **pos: object) -> CdaV2Aplic:
	pos = {"qtde_pos_fim": "10", "custo_correc_pos_fim": "5", "merc_pos_fim": "6", **pos}
	return CdaV2Aplic(
		cod_tp_aplic=code,
		qtde_dias_confid=0,
		negoc=CdaV2Negoc(
			tp_negoc=1,
			qtde_vendas_negoc="1.5",
			vl_vendas_negoc="2",
			qtde_aquis_negoc="3",
			vl_aquis_negoc="4",
		),
		pos_fim=CdaV2PosFim(**pos),
	)


def _doc(**blocks: list) -> CdaV2Document:
	return CdaV2Document(
		header=CdaV2Header(dt_compt="01/2024", dt_gerac_arq="05/02/2024"),
		informs=[CdaV2Inform(cnpj_fdo=CNPJ, vl_pl="1000.999", **blocks)],
	)


def _full_doc() -> CdaV2Document:
	return _doc(
		tit_pub=[CdaV2TitPub(cod_selic="100000", dt_venc="01/01/2030", aplic=_aplic(75))],
		cotas=[CdaV2Cotas(cnpj_fdo=CNPJ, aplic=_aplic(92))],
		swap=[
			CdaV2Swap(
				cod_swap="SWPSAB",
				aplic=CdaV2SwapAplic(
					cod_tp_aplic=183,
					qtde_dias_confid=0,
					negoc=CdaV2SwapNegoc(tp_negoc=2),
					pos_fim=CdaV2SwapPosFim(merc_pos_fim="1"),
				),
			)
		],
		demais_codif=[
			CdaV2DemaisCodif(
				cod_ativ="ABC", cod_tp_ativ=1, dt_ini_vigen="01/01/2000", aplic=_aplic(37)
			)
		],
		demais_n_codif=[
			CdaV2DemaisNCodif(
				cod_tp_ativ=999,
				desc="Algo",
				emis=CdaEmitter(tp_pf_pj_emis="PJ", nr_pf_pj_emis=CNPJ, nm_emis="Emissor"),
				aplic=_aplic(48),
			)
		],
	)


def _xml(doc: CdaV2Document) -> ET.Element:
	return ET.fromstring((CdaV2().export(doc) or "").split("\n", 1)[1])


def _tags(node: ET.Element) -> list[str]:
	return [child.tag.removeprefix(NS) for child in node]


def test_header_cod_doc_is_3() -> None:
	"""Header cod doc is 3."""
	assert _xml(_full_doc()).find(f"{NS}CAB_INFORM/{NS}COD_DOC").text == "3"


def test_header_versao_is_2_0() -> None:
	"""Header versao is 2 0."""
	assert _xml(_full_doc()).find(f"{NS}CAB_INFORM/{NS}VERSAO").text == "2.0"


def test_header_rejects_other_versao() -> None:
	"""Header rejects other versao."""
	with pytest.raises(ValidationError):
		CdaV2Header(versao="4.0", dt_compt="01/2024", dt_gerac_arq="05/02/2024")


def test_declaration_is_windows_1252() -> None:
	"""Declaration is windows 1252."""
	assert (CdaV2().export(_full_doc()) or "").startswith(
		'<?xml version="1.0" encoding="windows-1252"?>'
	)


def test_inform_children_order() -> None:
	"""Inform children order."""
	inform = _xml(_full_doc()).find(f"{NS}LISTA_INFORM/{NS}INFORM")
	assert _tags(inform) == ["CNPJ_FDO", "VL_PL", "LISTA_ATIV"]


def test_block_order_follows_the_page() -> None:
	"""Block order follows the page."""
	ativ = _xml(_full_doc()).find(f"{NS}LISTA_INFORM/{NS}INFORM/{NS}LISTA_ATIV")
	assert _tags(ativ) == ["TIT_PUB", "COTAS", "SWAP", "DEMAIS_CODIF", "DEMAIS_N_CODIF"]


def test_tit_pub_tag_order() -> None:
	"""Tit pub tag order."""
	node = _xml(_full_doc()).find(f".//{NS}TIT_PUB")
	assert _tags(node) == ["COD_SELIC", "DT_VENC", "APLIC"]


def test_cotas_tag_order() -> None:
	"""Cotas tag order."""
	assert _tags(_xml(_full_doc()).find(f".//{NS}COTAS")) == ["CNPJ_FDO", "APLIC"]


def test_swap_tag_order() -> None:
	"""Swap tag order."""
	assert _tags(_xml(_full_doc()).find(f".//{NS}SWAP")) == ["COD_SWAP", "APLIC"]


def test_demais_codif_tag_order() -> None:
	"""Demais codif tag order."""
	node = _xml(_full_doc()).find(f".//{NS}DEMAIS_CODIF")
	assert _tags(node) == ["COD_ATIV", "COD_TP_ATIV", "DT_INI_VIGEN", "APLIC"]


def test_demais_n_codif_tag_order() -> None:
	"""Demais n codif tag order."""
	node = _xml(_full_doc()).find(f".//{NS}DEMAIS_N_CODIF")
	assert _tags(node) == ["COD_TP_ATIV", "DESC", "EMIS", "APLIC"]


def test_emis_tag_order() -> None:
	"""Emis tag order."""
	node = _xml(_full_doc()).find(f".//{NS}EMIS")
	assert _tags(node) == ["TP_PF_PJ_EMIS", "NR_PF_PJ_EMIS", "NM_EMIS"]


def test_aplic_tag_order() -> None:
	"""Aplic tag order."""
	node = _xml(_full_doc()).find(f".//{NS}TIT_PUB/{NS}APLIC")
	assert _tags(node) == ["COD_TP_APLIC", "QTDE_DIAS_CONFID", "NEGOC", "POS_FIM"]


def test_negoc_tag_order() -> None:
	"""Negoc tag order."""
	node = _xml(_full_doc()).find(f".//{NS}TIT_PUB/{NS}APLIC/{NS}NEGOC")
	assert _tags(node) == [
		"TP_NEGOC",
		"QTDE_VENDAS_NEGOC",
		"VL_VENDAS_NEGOC",
		"QTDE_AQUIS_NEGOC",
		"VL_AQUIS_NEGOC",
	]


def test_pos_fim_tag_order() -> None:
	"""Pos fim tag order."""
	node = _xml(_full_doc()).find(f".//{NS}TIT_PUB/{NS}APLIC/{NS}POS_FIM")
	assert _tags(node) == ["QTDE_POS_FIM", "CUSTO_CORREC_POS_FIM", "MERC_POS_FIM"]


def test_swap_negoc_has_only_tp_negoc() -> None:
	"""Swap negoc has only tp negoc."""
	assert _tags(_xml(_full_doc()).find(f".//{NS}SWAP//{NS}NEGOC")) == ["TP_NEGOC"]


def test_swap_pos_fim_has_cost_only_when_given() -> None:
	"""Swap pos fim has cost only when given."""
	assert _tags(_xml(_full_doc()).find(f".//{NS}SWAP//{NS}POS_FIM")) == ["MERC_POS_FIM"]


def test_vl_pl_two_decimals_truncated_comma() -> None:
	"""Vl pl two decimals truncated comma."""
	assert _xml(_full_doc()).find(f".//{NS}VL_PL").text == "1000,99"


def test_quantity_six_decimals_comma() -> None:
	"""Quantity six decimals comma."""
	assert _xml(_full_doc()).find(f".//{NS}QTDE_VENDAS_NEGOC").text == "1,500000"


def test_cost_two_decimals_comma() -> None:
	"""Cost two decimals comma."""
	assert _xml(_full_doc()).find(f".//{NS}CUSTO_CORREC_POS_FIM").text == "5,00"


def test_output_has_no_dot_decimals() -> None:
	"""Output has no dot decimals."""
	assert "." not in _xml(_full_doc()).find(f".//{NS}MERC_POS_FIM").text


def test_leading_zero_cnpj_is_stripped() -> None:
	"""Leading zero cnpj is stripped."""
	cnpj = "00360305000104"
	doc = CdaV2Document(
		header=CdaV2Header(dt_compt="01/2024", dt_gerac_arq="05/02/2024"),
		informs=[CdaV2Inform(cnpj_fdo=cnpj, vl_pl="1")],
	)
	assert _xml(doc).find(f".//{NS}CNPJ_FDO").text == "360305000104"


def test_export_to_file_returns_none(tmp_path: Path) -> None:
	"""Export to file returns none."""
	assert CdaV2().export(_full_doc(), str(tmp_path / "cda.xml")) is None


def test_export_to_file_is_windows_1252(tmp_path: Path) -> None:
	"""Export to file is windows 1252."""
	path = tmp_path / "cda.xml"
	CdaV2().export(_full_doc(), str(path))
	assert b"windows-1252" in path.read_bytes()[:60]


def test_float_is_refused() -> None:
	"""Float is refused."""
	with pytest.raises(ValidationError):
		CdaV2PosFim(merc_pos_fim=0.1)


def test_vl_pl_decimal_type() -> None:
	"""Vl pl decimal type."""
	assert isinstance(_doc().informs[0].vl_pl, Decimal)


def test_more_than_50_informs_rejected() -> None:
	"""More than 50 informs rejected."""
	inform = CdaV2Inform(cnpj_fdo=CNPJ, vl_pl="1")
	with pytest.raises(ValidationError):
		CdaV2Document(
			header=CdaV2Header(dt_compt="01/2024", dt_gerac_arq="05/02/2024"),
			informs=[inform] * 51,
		)


def test_bad_competence_rejected() -> None:
	"""Bad competence rejected."""
	with pytest.raises(ValidationError):
		CdaV2Header(dt_compt="2024-01", dt_gerac_arq="05/02/2024")


def test_confid_days_above_90_rejected() -> None:
	"""Confid days above 90 rejected."""
	with pytest.raises(ValidationError):
		CdaV2Aplic(cod_tp_aplic=37, qtde_dias_confid=91, pos_fim=CdaV2PosFim(merc_pos_fim="1"))


def test_confid_days_is_mandatory() -> None:
	"""Confid days is mandatory."""
	with pytest.raises(ValidationError):
		CdaV2Aplic(cod_tp_aplic=37, pos_fim=CdaV2PosFim(merc_pos_fim="1"))


def test_tit_pub_rejects_other_aplic_type() -> None:
	"""Tit pub rejects other aplic type."""
	with pytest.raises(ValidationError, match="not allowed in TIT_PUB"):
		CdaV2TitPub(cod_selic="1", dt_venc="01/01/2030", aplic=_aplic(37))


def test_cotas_reject_stock_type() -> None:
	"""Cotas reject stock type."""
	with pytest.raises(ValidationError, match="not allowed in COTAS"):
		CdaV2Cotas(cnpj_fdo=CNPJ, aplic=_aplic(37))


def test_cotas_reject_invalid_cnpj() -> None:
	"""Cotas reject invalid cnpj."""
	with pytest.raises(ValidationError):
		CdaV2Cotas(cnpj_fdo="11222333000182", aplic=_aplic(92))


def test_swap_rejects_other_aplic_type() -> None:
	"""Swap rejects other aplic type."""
	with pytest.raises(ValidationError):
		CdaV2SwapAplic(
			cod_tp_aplic=37, qtde_dias_confid=0, pos_fim=CdaV2SwapPosFim(merc_pos_fim="1")
		)


def test_swap_rejects_bad_code() -> None:
	"""Swap rejects bad code."""
	with pytest.raises(ValidationError):
		CdaV2Swap(
			cod_swap="SAB",
			aplic=CdaV2SwapAplic(
				cod_tp_aplic=183, qtde_dias_confid=0, pos_fim=CdaV2SwapPosFim(merc_pos_fim="1")
			),
		)


def test_table_a_requires_final_quantity() -> None:
	"""Table a requires final quantity."""
	with pytest.raises(ValueError, match="posicao final is required"):
		CdaV2Aplic(
			cod_tp_aplic=37, qtde_dias_confid=0, pos_fim=CdaV2PosFim(merc_pos_fim="1")
		).check_table_a("DEMAIS_N_CODIF", 1)


def test_table_a_forbids_cost_for_futures() -> None:
	"""Table a forbids cost for futures."""
	with pytest.raises(ValueError, match="custo must not be filled"):
		_aplic(102).check_table_a("DEMAIS_N_CODIF", 9)


def test_table_a_forbids_sales_for_forward_purchases() -> None:
	"""Table a forbids sales for forward purchases."""
	with pytest.raises(ValueError, match="vendas must not be filled"):
		_aplic(42).check_table_a("DEMAIS_N_CODIF", 5)


def test_table_a_requires_cost_for_stocks() -> None:
	"""Table a requires cost for stocks."""
	with pytest.raises(ValueError, match="custo is required"):
		_aplic(37, custo_correc_pos_fim=None).check_table_a("DEMAIS_N_CODIF", 1)


def test_demais_codif_rejects_uncoded_asset_type() -> None:
	"""Demais codif rejects uncoded asset type."""
	with pytest.raises(ValidationError, match="not a coded asset type"):
		CdaV2DemaisCodif(
			cod_ativ="A", cod_tp_ativ=999, dt_ini_vigen="01/01/2000", aplic=_aplic(48)
		)


def test_asset_type_must_relate_to_aplic_type() -> None:
	"""Asset type must relate to aplic type."""
	with pytest.raises(ValidationError, match="not valid for COD_TP_APLIC 37"):
		CdaV2DemaisCodif(cod_ativ="A", cod_tp_ativ=3, dt_ini_vigen="01/01/2000", aplic=_aplic(37))


def test_demais_n_codif_desc_max_1000() -> None:
	"""Demais n codif desc max 1000."""
	with pytest.raises(ValidationError):
		CdaV2DemaisNCodif(
			cod_tp_ativ=999,
			desc="x" * 1001,
			emis=CdaEmitter(tp_pf_pj_emis="PJ", nr_pf_pj_emis=CNPJ, nm_emis="E"),
			aplic=_aplic(48),
		)


def test_negoc_requires_tp_negoc() -> None:
	"""Negoc requires tp negoc."""
	with pytest.raises(ValidationError):
		CdaV2Negoc(qtde_vendas_negoc="1", vl_vendas_negoc="1")
