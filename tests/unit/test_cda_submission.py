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
	CdaAtivoExt,
	CdaBankEmitter,
	CdaCotas,
	CdaDemaisCodif,
	CdaDemaisNCodif,
	CdaDepPrazoTitIf,
	CdaDocument,
	CdaEmitter,
	CdaHeader,
	CdaInform,
	CdaInvExt,
	CdaNegoc,
	CdaPosFim,
	CdaPosFixIndex,
	CdaRiskRating,
	CdaSwap,
	CdaSwapAplic,
	CdaSwapPosFim,
	CdaTitAgroCredPriv,
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
		aplic=CdaSwapAplic(cod_tp_aplic=183, pos_fim=CdaSwapPosFim(merc_pos_fim="5")),
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


def _tags(node: ET.Element) -> list[str]:
	"""Child tag names without the namespace."""
	return [e.tag.split("}")[1] for e in node]


def _export_block(block: str, **inform_kwargs: object) -> ET.Element:
	"""Export a one-block fund and return that block's element."""
	root = ET.fromstring(Cda().export(_doc(**inform_kwargs)).split("\n", 1)[1])
	return root.find(f".//c:{block}", NS)


def _pos(code: int | None = None, **extra: object) -> CdaAplic:
	"""Minimal APLIC for types whose Table A needs only EMPR_LIGADA + final position."""
	return CdaAplic(
		cod_tp_aplic=code,
		empr_ligada="N",
		pos_fim=CdaPosFim(qtde_pos_fim="1", merc_pos_fim="2"),
		**extra,
	)


def test_swap_nests_merc_pos_fim_inside_pos_fim() -> None:
	"""The page puts SWAP's MERC_POS_FIM inside POS_FIM, like every other block."""
	swap = CdaSwap(
		cod_swap="SWPSDI",
		aplic=CdaSwapAplic(cod_tp_aplic=183, pos_fim=CdaSwapPosFim(merc_pos_fim="5")),
	)
	node = _export_block("SWAP", swap=[swap])
	assert _tags(node) == ["COD_SWAP", "APLIC"]
	assert _tags(node.find("c:APLIC", NS)) == ["COD_TP_APLIC", "POS_FIM"]
	assert node.find("c:APLIC/c:POS_FIM/c:MERC_POS_FIM", NS).text == "5,00"


def test_tit_pub_tag_order() -> None:
	"""TIT_PUB: COD_SELIC, DT_VENC, APLIC."""
	aplic = CdaAplic(
		cod_tp_aplic=147,
		empr_ligada="N",
		pos_fim=CdaPosFim(qtde_pos_fim="1", merc_pos_fim="2"),
	)
	node = _export_block(
		"TIT_PUB", tit_pub=[CdaTitPub(cod_selic="1", dt_venc="01/01/2030", aplic=aplic)]
	)
	assert _tags(node) == ["COD_SELIC", "DT_VENC", "APLIC"]


def test_cotas_has_no_cod_tp_aplic() -> None:
	"""COTAS: CNPJ_FDO, APLIC; the APLIC has no COD_TP_APLIC tag."""
	node = _export_block("COTAS", cotas=[CdaCotas(cnpj_fdo=VALID_CNPJ, aplic=_pos())])
	assert _tags(node) == ["CNPJ_FDO", "APLIC"]
	assert _tags(node.find("c:APLIC", NS)) == ["EMPR_LIGADA", "POS_FIM"]


def test_dep_prazo_tit_if_tag_order() -> None:
	"""DEP_PRAZO_TIT_IF: post-fixed index nests, rating nests, APLIC last."""
	block = CdaDepPrazoTitIf(
		cod_tp_ativ=50,
		emis=CdaBankEmitter(cnpj_emis=VALID_CNPJ, nm_emis="Banco"),
		dt_venc="01/01/2030",
		st_tit_pos_fix="S",
		tit_pos_fix_index=CdaPosFixIndex(
			tit_pos_fix_cod_index="DI1", tit_pos_fix_pr_index="102", tit_pos_fix_cupom="3"
		),
		st_classif_risco="S",
		classif_risco=CdaRiskRating(
			ag_classif_risco="Ag", dt_classif_risco="01/01/2024", grau_classif_risco="AAA"
		),
		aplic=_pos(),
	)
	node = _export_block("DEP_PRAZO_TIT_IF", dep_prazo_tit_if=[block])
	assert _tags(node) == [
		"COD_TP_ATIV",
		"EMIS",
		"DT_VENC",
		"ST_TIT_POS_FIX",
		"TIT_POS_FIX_INDEX",
		"ST_CLASSIF_RISCO",
		"CLASSIF_RISCO",
		"APLIC",
	]
	assert _tags(node.find("c:TIT_POS_FIX_INDEX", NS)) == [
		"TIT_POS_FIX_COD_INDEX",
		"TIT_POS_FIX_PR_INDEX",
		"TIT_POS_FIX_CUPOM",
	]
	assert node.find("c:TIT_POS_FIX_INDEX/c:TIT_POS_FIX_PR_INDEX", NS).text == "102,000000"


def test_tit_agro_cred_priv_tag_order() -> None:
	"""TIT_AGRO_CRED_PRIV: pre-fixed rate, CETIP/guarantee flags, optional co-obligor CNPJ."""
	block = CdaTitAgroCredPriv(
		cod_tp_ativ=31,
		emis=CdaEmitter(tp_pf_pj_emis="PJ", nr_pf_pj_emis=VALID_CNPJ, nm_emis="Emissor"),
		dt_venc="01/01/2030",
		st_tit_pos_fix="N",
		tit_pre_fix_taxa_contr="15",
		st_tit_reg_cetip="S",
		st_tit_garant_seguro="S",
		cnpj_instit_financ=VALID_CNPJ,
		aplic=_pos(195),
	)
	node = _export_block("TIT_AGRO_CRED_PRIV", tit_agro_cred_priv=[block])
	assert _tags(node) == [
		"COD_TP_ATIV",
		"EMIS",
		"DT_VENC",
		"ST_TIT_POS_FIX",
		"TIT_PRE_FIX_TAXA_CONTR",
		"ST_TIT_REG_CETIP",
		"ST_TIT_GARANT_SEGURO",
		"CNPJ_INSTIT_FINANC",
		"APLIC",
	]
	assert _tags(node.find("c:EMIS", NS)) == ["TP_PF_PJ_EMIS", "NR_PF_PJ_EMIS", "NM_EMIS"]


def test_inv_ext_tag_order_and_ativo_ext_after_pos_fim() -> None:
	"""INV_EXT: ATIVO_EXT closes APLIC, after POS_FIM; VALOR_AT_EXT keeps its own scale."""
	ext = CdaAtivoExt(desc_at_ext="Ativo", qtde_at_ext=3, valor_at_ext="12.3456789")
	block = CdaInvExt(
		cod_tp_ativ=1,
		inv_coletivo="N",
		gest_inv_coletivo="N",
		nm_emis="Emissor",
		cod_pais=1,
		cod_bv_merc="NYSE",
		cod_ativo_bv_merc="X",
		st_classif_risco="N",
		aplic=_pos(ativo_ext=ext),
	)
	node = _export_block("INV_EXT", inv_ext=[block])
	assert _tags(node) == [
		"COD_TP_ATIV",
		"INV_COLETIVO",
		"GEST_INV_COLETIVO",
		"NM_EMIS",
		"COD_PAIS",
		"COD_BV_MERC",
		"COD_ATIVO_BV_MERC",
		"ST_CLASSIF_RISCO",
		"APLIC",
	]
	aplic = node.find("c:APLIC", NS)
	assert _tags(aplic) == ["EMPR_LIGADA", "POS_FIM", "ATIVO_EXT"]
	assert _tags(aplic.find("c:ATIVO_EXT", NS)) == ["DESC_AT_EXT", "QTDE_AT_EXT", "VALOR_AT_EXT"]
	assert aplic.find("c:ATIVO_EXT/c:VALOR_AT_EXT", NS).text == "12,3456789"


def test_export_non_cp1252_text_rejected_and_file_untouched(tmp_path: object) -> None:
	"""A character windows-1252 cannot hold is refused at validation, never at write time."""
	out = tmp_path / "cda.xml"
	out.write_bytes(b"previous export")
	with pytest.raises(ValidationError, match="windows-1252"):
		CdaEmitter(tp_pf_pj_emis="PJ", nr_pf_pj_emis=VALID_CNPJ, nm_emis="seta \u2192")
	assert out.read_bytes() == b"previous export"


def test_export_failure_does_not_truncate_existing_file(tmp_path: object) -> None:
	"""Even if unencodable text got past validation, the old file survives."""
	doc = _doc()
	object.__setattr__(doc.header, "dt_gerac_arq", "\u2192")  # bypass validation on purpose
	out = tmp_path / "cda.xml"
	out.write_bytes(b"previous export")
	with pytest.raises(UnicodeEncodeError):
		Cda().export(doc, str(out))
	assert out.read_bytes() == b"previous export"


def test_export_accepts_cp1252_accents() -> None:
	"""Accents are encodable and round-trip through the file."""
	node = CdaEmitter(tp_pf_pj_emis="PJ", nr_pf_pj_emis=VALID_CNPJ, nm_emis="Açúcar S/A")
	assert node.nm_emis == "Açúcar S/A"


@pytest.mark.parametrize(
	"dt", ["31/02/2024", "99/99/2024", "00/01/2024", "29/02/2023", "01/01/2024\n"]
)
def test_impossible_dates_rejected_everywhere(dt: str) -> None:
	"""Every DD/MM/AAAA field shares one real-calendar check."""
	with pytest.raises(ValidationError):
		CdaHeader(dt_compt="03/2024", dt_gerac_arq=dt)
	with pytest.raises(ValidationError):
		CdaRiskRating(ag_classif_risco="a", dt_classif_risco=dt, grau_classif_risco="A")
	with pytest.raises(ValidationError):
		CdaDemaisCodif(cod_ativ="X", cod_tp_ativ=1, dt_ini_vigen=dt, aplic=_aplic_acao())
	with pytest.raises(ValidationError):
		CdaTitPub(cod_selic="1", dt_venc=dt, aplic=_pos(147))


def test_leap_day_accepted() -> None:
	"""29/02/2024 exists."""
	assert CdaHeader(dt_compt="03/2024", dt_gerac_arq="29/02/2024").dt_gerac_arq == "29/02/2024"


def test_valor_at_ext_rejects_float_and_nan() -> None:
	"""A monetary value is never a binary float; NaN is not a number the file can carry."""
	with pytest.raises(ValidationError, match="never a float"):
		CdaAtivoExt(desc_at_ext="a", qtde_at_ext=1, valor_at_ext=0.1)
	with pytest.raises(ValidationError):
		CdaAtivoExt(desc_at_ext="a", qtde_at_ext=1, valor_at_ext="NaN")
	assert CdaAtivoExt(desc_at_ext="a", qtde_at_ext=1, valor_at_ext="0.1").valor_at_ext == Decimal(
		"0.1"
	)


def test_float_rejected_on_scaled_fields() -> None:
	"""The no-float rule covers VL_PL and the quantity/value fields too."""
	with pytest.raises(ValidationError, match="never a float"):
		CdaInform(cnpj_fdo=VALID_CNPJ, vl_pl=1.1)
	with pytest.raises(ValidationError, match="never a float"):
		CdaPosFim(qtde_pos_fim=1.5, merc_pos_fim="1")


def test_ativo_ext_outside_inv_ext_rejected() -> None:
	"""ATIVO_EXT exists only in INV_EXT."""
	ext = CdaAtivoExt(desc_at_ext="a", qtde_at_ext=1, valor_at_ext="1")
	with pytest.raises(ValidationError, match="only valid in INV_EXT"):
		CdaDemaisCodif(
			cod_ativ="X",
			cod_tp_ativ=1,
			dt_ini_vigen="01/01/2020",
			aplic=_aplic_acao().model_copy(update={"ativo_ext": ext}),
		)


def test_empty_negoc_rejected() -> None:
	"""An empty NEGOC would be written as <NEGOC />."""
	with pytest.raises(ValidationError, match="at least one field"):
		CdaNegoc()


def test_negative_traded_quantity_rejected() -> None:
	"""Sales/acquisition totals are non-negative, like their VL_* fields."""
	with pytest.raises(ValidationError):
		CdaNegoc(qtde_vendas_negoc="-5", vl_vendas_negoc="10")
	with pytest.raises(ValidationError):
		CdaNegoc(qtde_aquis_negoc="-5", vl_aquis_negoc="10")


def test_swap_code_rejects_trailing_newline() -> None:
	"""fullmatch, not match: no trailing newline in the XML."""
	aplic = CdaSwapAplic(cod_tp_aplic=183, pos_fim=CdaSwapPosFim(merc_pos_fim="1"))
	with pytest.raises(ValidationError):
		CdaSwap(cod_swap="SWPABC\n", aplic=aplic)
	with pytest.raises(ValidationError):
		CdaHeader(dt_compt="03/2024\n", dt_gerac_arq="05/04/2024")


@pytest.mark.parametrize("code", ["", "a\x00b"])
def test_empty_or_control_code_rejected(code: str) -> None:
	"""Code/text fields must be non-empty and XML-legal."""
	with pytest.raises(ValidationError):
		CdaTitPub(cod_selic=code, dt_venc="01/01/2030", aplic=_pos(147))
	with pytest.raises(ValidationError):
		CdaCotas(cod_subclasse=code, aplic=_pos())
