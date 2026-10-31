"""Unit tests for the CDA V4 submission writer.

Expectations come from the CVM page PadraoXMLCDANetV4.aspx (tag names and order,
comma decimals, Table A/B, block x application-type table), not from the writer.
"""
# ruff: noqa: S314  (parses the writer's own output, not untrusted input)

from decimal import Decimal
from xml.etree import ElementTree as ET

from pydantic import ValidationError
import pytest

from filings_cvm.submission import (
	Cda,
	CdaAplic,
	CdaCotas,
	CdaDemaisCodif,
	CdaDemaisNCodif,
	CdaDocument,
	CdaEmitter,
	CdaHeader,
	CdaInform,
	CdaNegoc,
	CdaPosFim,
	CdaSwap,
	CdaSwapAplic,
	CdaTitPub,
)


VALID_CNPJ = "11222333000181"
NS = {"c": "urn:cda"}


def _aplic_acao() -> CdaAplic:
	"""Application type 37 (Ações): every Table A column is required."""
	return CdaAplic(
		cod_tp_aplic=37,
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
	)


def _doc(**inform_kwargs: object) -> CdaDocument:
	"""One fund, header 03/2024."""
	return CdaDocument(
		header=CdaHeader(dt_compt="03/2024", dt_gerac_arq="05/04/2024"),
		informs=[CdaInform(cnpj_fdo=VALID_CNPJ, vl_pl="1000000.129", **inform_kwargs)],
	)


def test_export_header_and_namespace() -> None:
	"""COD_DOC=3, VERSAO=4.0, urn:cda namespace, windows-1252 declaration."""
	xml = Cda().export(_doc())
	assert xml.startswith('<?xml version="1.0" encoding="windows-1252"?>')
	root = ET.fromstring(xml.split("\n", 1)[1])
	assert root.tag == "{urn:cda}DOC_ARQ"
	head = root.find("c:CAB_INFORM", NS)
	assert [e.text for e in head] == ["3", "4.0", "03/2024", "05/04/2024"]


def test_export_vl_pl_truncated_with_comma() -> None:
	"""VL_PL has 2 decimals, truncated (not rounded), comma separator."""
	root = ET.fromstring(Cda().export(_doc()).split("\n", 1)[1])
	assert root.find(".//c:VL_PL", NS).text == "1000000,12"


def test_export_demais_codif_tag_order() -> None:
	"""Tag order inside DEMAIS_CODIF/APLIC follows the page."""
	node_block = CdaDemaisCodif(
		cod_ativ="PETR4",
		cod_tp_ativ=1,
		dt_ini_vigen="01/01/2020",
		aplic=_aplic_acao(),
	)
	root = ET.fromstring(Cda().export(_doc(demais_codif=[node_block])).split("\n", 1)[1])
	node = root.find(".//c:DEMAIS_CODIF", NS)
	assert [e.tag.split("}")[1] for e in node] == [
		"COD_ATIV",
		"COD_TP_ATIV",
		"DT_INI_VIGEN",
		"APLIC",
	]
	aplic = node.find("c:APLIC", NS)
	assert [e.tag.split("}")[1] for e in aplic] == [
		"COD_TP_APLIC",
		"EMPR_LIGADA",
		"QTDE_DIAS_CONFID",
		"NEGOC",
		"POS_FIM",
	]
	negoc = {e.tag.split("}")[1]: e.text for e in aplic.find("c:NEGOC", NS)}
	assert negoc == {
		"TP_NEGOC": "1",
		"QTDE_VENDAS_NEGOC": "1,000000",
		"VL_VENDAS_NEGOC": "10,00",
		"QTDE_AQUIS_NEGOC": "2,500000",
		"VL_AQUIS_NEGOC": "20,99",
	}
	assert aplic.find("c:POS_FIM/c:MERC_POS_FIM", NS).text == "1234,50"


def test_export_blocks_in_mandated_order() -> None:
	"""SWAP precedes DEMAIS_CODIF regardless of construction order; zeros not padded."""
	swap = CdaSwap(
		cod_swap="SWPSDI",
		aplic=CdaSwapAplic(cod_tp_aplic=183, merc_pos_fim="5"),
	)
	codif = CdaDemaisCodif(
		cod_ativ="X", cod_tp_ativ=1, dt_ini_vigen="01/01/2020", aplic=_aplic_acao()
	)
	root = ET.fromstring(Cda().export(_doc(demais_codif=[codif], swap=[swap])).split("\n", 1)[1])
	tags = [e.tag.split("}")[1] for e in root.find(".//c:LISTA_ATIV", NS)]
	assert tags == ["SWAP", "DEMAIS_CODIF"]


def test_export_strips_leading_zeros_from_cnpj() -> None:
	"""The page forbids zero fillers on the left of the CNPJ."""
	doc = CdaDocument(
		header=CdaHeader(dt_compt="03/2024", dt_gerac_arq="05/04/2024"),
		informs=[CdaInform(cnpj_fdo="00.000.000/0001-91", vl_pl="1")],
	)
	root = ET.fromstring(Cda().export(doc).split("\n", 1)[1])
	assert root.find(".//c:CNPJ_FDO", NS).text == "191"


def test_export_writes_windows_1252_file(tmp_path: object) -> None:
	"""With output_path the file is written and None returned."""
	out = tmp_path / "cda.xml"
	assert Cda().export(_doc(), str(out)) is None
	assert out.read_bytes().startswith(b'<?xml version="1.0" encoding="windows-1252"?>')


def test_cotas_requires_exactly_one_identifier() -> None:
	"""COTAS identifies the fund by CNPJ_FDO xor COD_SUBCLASSE."""
	aplic = CdaAplic(
		empr_ligada="N",
		pos_fim=CdaPosFim(qtde_pos_fim="1", merc_pos_fim="1"),
	)
	with pytest.raises(ValidationError):
		CdaCotas(aplic=aplic)
	with pytest.raises(ValidationError):
		CdaCotas(cnpj_fdo=VALID_CNPJ, cod_subclasse="X", aplic=aplic)
	assert CdaCotas(cod_subclasse="X", aplic=aplic).cnpj_fdo is None


def test_table_a_forbidden_field_rejected() -> None:
	"""Type 94 (Disponibilidades): quantity of the final position is forbidden (N)."""
	aplic = CdaAplic(cod_tp_aplic=94, pos_fim=CdaPosFim(qtde_pos_fim="1", merc_pos_fim="1"))
	with pytest.raises(ValidationError, match="posicao final"):
		CdaDemaisNCodif(
			cod_tp_ativ=999,
			desc="x",
			emis=CdaEmitter(tp_pf_pj_emis="PJ", nr_pf_pj_emis=VALID_CNPJ, nm_emis="n"),
			aplic=aplic,
		)


def test_table_a_required_field_missing_rejected() -> None:
	"""Type 37 requires EMPR_LIGADA and the sales/acquisition columns."""
	aplic = CdaAplic(cod_tp_aplic=37, pos_fim=CdaPosFim(qtde_pos_fim="1", merc_pos_fim="1"))
	with pytest.raises(ValidationError, match="empr_ligada"):
		CdaDemaisCodif(cod_ativ="X", cod_tp_ativ=1, dt_ini_vigen="01/01/2020", aplic=aplic)


def test_application_type_not_allowed_in_block() -> None:
	"""Debêntures are not allowed in TIT_PUB (only 75 and 147)."""
	aplic = CdaAplic(
		cod_tp_aplic=193,
		empr_ligada="N",
		pos_fim=CdaPosFim(qtde_pos_fim="1", merc_pos_fim="1"),
	)
	with pytest.raises(ValidationError, match="not allowed in TIT_PUB"):
		CdaTitPub(cod_selic="1", dt_venc="01/01/2030", aplic=aplic)


def test_table_b_asset_type_mismatch_rejected() -> None:
	"""Ações (37) accept asset types 1, 2, 13 only."""
	with pytest.raises(ValidationError, match="COD_TP_ATIV 6"):
		CdaDemaisCodif(cod_ativ="X", cod_tp_ativ=6, dt_ini_vigen="01/01/2020", aplic=_aplic_acao())


def test_negoc_quantity_without_value_rejected() -> None:
	"""When 'Quant.' or 'R$' is filled the other must be too."""
	with pytest.raises(ValidationError, match="together"):
		CdaNegoc(qtde_vendas_negoc="1")


def test_invalid_cnpj_rejected() -> None:
	"""CNPJ check digits are validated."""
	with pytest.raises(ValidationError):
		CdaInform(cnpj_fdo="11222333000182", vl_pl="1")


@pytest.mark.parametrize("dt", ["2024-03", "3/2024", "13/2024", "01/03/2024"])
def test_header_competence_must_be_mm_aaaa(dt: str) -> None:
	"""DT_COMPT is MM/AAAA."""
	with pytest.raises(ValidationError):
		CdaHeader(dt_compt=dt, dt_gerac_arq="05/04/2024")


def test_vl_pl_beyond_21_integer_digits_rejected() -> None:
	"""VL_PL allows at most 21 integer digits."""
	with pytest.raises(ValidationError):
		CdaInform(cnpj_fdo=VALID_CNPJ, vl_pl=Decimal(10) ** 21)
