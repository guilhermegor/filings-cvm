"""Unit tests for the CDA V3 submission writer.

Expectations come from the CVM page PadraoXMLCDANetV3.aspx (tag order, comma decimals,
scales, the V3 deltas over V4), not from the writer.
"""
# ruff: noqa: S314  (parses the writer's own output, not untrusted input)

from xml.etree import ElementTree as ET

from pydantic import ValidationError
import pytest

from filings_cvm.submission import (
	Cda,
	CdaAplic,
	CdaAtivoExt,
	CdaDocument,
	CdaHeader,
	CdaInform,
	CdaNegoc,
	CdaPosFim,
	CdaV3,
	CdaV3Cotas,
	CdaV3DepPrazoTitIf,
	CdaV3Document,
	CdaV3Header,
	CdaV3Inform,
	CdaV3InvExt,
)


VALID_CNPJ = "11222333000181"
NS = {"c": "urn:cda"}


def _tags(node: ET.Element) -> list[str]:
	"""Local tag names of a node's children."""
	return [e.tag.split("}")[1] for e in node]


def _aplic(**kwargs: object) -> CdaAplic:
	"""APLIC for an optional-everything type (197/189): final position only."""
	return CdaAplic(
		empr_ligada="N",
		qtde_dias_confid=0,
		negoc=CdaNegoc(
			tp_negoc=1,
			qtde_vendas_negoc="1",
			vl_vendas_negoc="10",
			qtde_aquis_negoc="2.5",
			vl_aquis_negoc="20.999",
		),
		pos_fim=CdaPosFim(qtde_pos_fim="100", merc_pos_fim="1234.5"),
		**kwargs,
	)


def _doc(**inform_kwargs: object) -> CdaV3Document:
	"""One fund, header 03/2024."""
	return CdaV3Document(
		header=CdaV3Header(dt_compt="03/2024", dt_gerac_arq="05/04/2024"),
		informs=[CdaV3Inform(cnpj_fdo=VALID_CNPJ, vl_pl="1000000.129", **inform_kwargs)],
	)


def _root(doc: CdaV3Document) -> ET.Element:
	"""Parse the writer's XML."""
	return ET.fromstring(CdaV3().export(doc).split("\n", 1)[1])


def test_export_header_is_version_3() -> None:
	"""COD_DOC=3, VERSAO=3.0 (page: header 'não deve ser modificado')."""
	root = _root(_doc())
	assert [e.text for e in root.find("c:CAB_INFORM", NS)] == ["3", "3.0", "03/2024", "05/04/2024"]


def test_export_declares_windows_1252_and_namespace() -> None:
	"""XML declaration and urn:cda namespace as on the page."""
	xml = CdaV3().export(_doc())
	assert xml.startswith('<?xml version="1.0" encoding="windows-1252"?>')
	assert 'xmlns="urn:cda"' in xml


def test_export_vl_pl_two_decimals_truncated_with_comma() -> None:
	"""VL_PL: 21 integer + 2 decimals, comma separator."""
	assert _root(_doc()).find(".//c:VL_PL", NS).text == "1000000,12"


def test_export_cotas_layout_has_no_cod_tp_aplic() -> None:
	"""COTAS: CNPJ_FDO then APLIC without COD_TP_APLIC; scales 15.6 / 15.2."""
	cotas = CdaV3Cotas(cnpj_fdo=VALID_CNPJ, aplic=_aplic())
	node = _root(_doc(cotas=[cotas])).find(".//c:COTAS", NS)
	assert _tags(node) == ["CNPJ_FDO", "APLIC"]
	assert _tags(node.find("c:APLIC", NS)) == [
		"EMPR_LIGADA",
		"QTDE_DIAS_CONFID",
		"NEGOC",
		"POS_FIM",
	]
	assert node.find("c:APLIC/c:NEGOC/c:QTDE_AQUIS_NEGOC", NS).text == "2,500000"
	assert node.find("c:APLIC/c:NEGOC/c:VL_AQUIS_NEGOC", NS).text == "20,99"


def test_export_inv_ext_tag_order() -> None:
	"""INV_EXT per the V3 page: no INV_COLETIVO flags, APLIC without COD_TP_APLIC."""
	inv = CdaV3InvExt(
		cod_tp_ativ=1,
		nm_emis="Acme Inc",
		cod_pais=5,
		cod_bv_merc="NYSE",
		cod_ativo_bv_merc="ACME",
		st_classif_risco="N",
		aplic=_aplic(),
	)
	node = _root(_doc(inv_ext=[inv])).find(".//c:INV_EXT", NS)
	assert _tags(node) == [
		"COD_TP_ATIV",
		"NM_EMIS",
		"COD_PAIS",
		"COD_BV_MERC",
		"COD_ATIVO_BV_MERC",
		"ST_CLASSIF_RISCO",
		"APLIC",
	]
	assert "COD_TP_APLIC" not in _tags(node.find("c:APLIC", NS))


def test_export_dep_prazo_tag_order_pre_fixed() -> None:
	"""DEP_PRAZO_TIT_IF per the V3 page (pre-fixed, no rating)."""
	dep = CdaV3DepPrazoTitIf(
		cod_tp_ativ=51,
		emis={"cnpj_emis": VALID_CNPJ, "nm_emis": "Banco"},
		dt_venc="01/01/2030",
		st_tit_pos_fix="N",
		tit_pre_fix_taxa_contr="15.1234567",
		st_classif_risco="N",
		aplic=_aplic(),
	)
	node = _root(_doc(dep_prazo_tit_if=[dep])).find(".//c:DEP_PRAZO_TIT_IF", NS)
	assert _tags(node) == [
		"COD_TP_ATIV",
		"EMIS",
		"DT_VENC",
		"ST_TIT_POS_FIX",
		"TIT_PRE_FIX_TAXA_CONTR",
		"ST_CLASSIF_RISCO",
		"APLIC",
	]
	assert node.find("c:TIT_PRE_FIX_TAXA_CONTR", NS).text == "15,123456"


def test_cotas_rejects_v4_subclass_code() -> None:
	"""COTAS in V3 has no subclass code."""
	with pytest.raises(ValidationError, match="cod_subclasse"):
		CdaV3Cotas(cod_subclasse="X1", aplic=_aplic())


def test_dep_prazo_rejects_v4_desc_ativ_vinc() -> None:
	"""DESC_ATIV_VINC is not on the V3 page."""
	with pytest.raises(ValidationError, match="desc_ativ_vinc"):
		CdaV3DepPrazoTitIf(
			cod_tp_ativ=51,
			desc_ativ_vinc="x",
			emis={"cnpj_emis": VALID_CNPJ, "nm_emis": "Banco"},
			dt_venc="01/01/2030",
			st_tit_pos_fix="N",
			tit_pre_fix_taxa_contr="1",
			st_classif_risco="N",
			aplic=_aplic(),
		)


def test_inv_ext_rejects_ativo_ext() -> None:
	"""V3 APLIC of INV_EXT has no ATIVO_EXT."""
	with pytest.raises(ValidationError, match="ativo_ext"):
		CdaV3InvExt(
			cod_tp_ativ=1,
			nm_emis="Acme",
			cod_pais=5,
			cod_bv_merc="NYSE",
			cod_ativo_bv_merc="ACME",
			st_classif_risco="N",
			aplic=_aplic(ativo_ext=CdaAtivoExt(desc_at_ext="d", qtde_at_ext=1, valor_at_ext="1")),
		)


def test_header_rejects_version_4() -> None:
	"""VERSAO must be 3.0."""
	with pytest.raises(ValidationError):
		CdaV3Header(versao="4.0", dt_compt="03/2024", dt_gerac_arq="05/04/2024")


def test_document_rejects_more_than_50_funds() -> None:
	"""Page: at most 50 funds per file (V4 allows 1000)."""
	inform = CdaV3Inform(cnpj_fdo=VALID_CNPJ, vl_pl="1")
	with pytest.raises(ValidationError):
		CdaV3Document(
			header=CdaV3Header(dt_compt="03/2024", dt_gerac_arq="05/04/2024"),
			informs=[inform] * 51,
		)


def test_writer_refuses_v4_document() -> None:
	"""A V4 document must not be serialised as V3."""
	doc = CdaDocument(
		header=CdaHeader(dt_compt="03/2024", dt_gerac_arq="05/04/2024"),
		informs=[CdaInform(cnpj_fdo=VALID_CNPJ, vl_pl="1")],
	)
	with pytest.raises(TypeError):
		CdaV3().export(doc)


def test_v4_writer_unchanged_by_v3_header() -> None:
	"""The V4 writer still stamps 4.0."""
	doc = CdaDocument(
		header=CdaHeader(dt_compt="03/2024", dt_gerac_arq="05/04/2024"),
		informs=[CdaInform(cnpj_fdo=VALID_CNPJ, vl_pl="1")],
	)
	assert "<VERSAO>4.0</VERSAO>" in Cda().export(doc)


def test_export_writes_file_as_windows_1252(tmp_path: object) -> None:
	"""output_path gets windows-1252 bytes and returns None."""
	path = tmp_path / "cda.xml"
	assert CdaV3().export(_doc(), str(path)) is None
	assert path.read_bytes().startswith(b'<?xml version="1.0" encoding="windows-1252"?>')


def test_inv_ext_rejects_v4_collective_flags() -> None:
	"""The V4-only INV_COLETIVO flags must raise, not be silently dropped."""
	for field in ("inv_coletivo", "gest_inv_coletivo"):
		with pytest.raises(ValueError, match="do not exist in CDA V3"):
			CdaV3InvExt.model_validate({field: "S"})
