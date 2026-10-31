"""Unit tests for the Informe Semestral de INR writers (Parte I and Parte II)."""

from decimal import Decimal
from pathlib import Path
import re

from pydantic import ValidationError
import pytest

from filings_cvm.submission import (
	InrParte1Document,
	InrParte2Document,
	InrSemestralParte1,
	InrSemestralParte2,
)


CNPJ_A = "11.222.333/0001-81"
CNPJ_A_BARE = "11222333000181"
CPF = "529.982.247-25"
PART = "123.456.789.0-1"
PART_2 = "123.456.790.1-2"
TRANSFERS = {
	"vl_invest_carteira_haver_nres": 1,
	"vl_haver_nres_invest_carteira": 2,
	"vl_invest_carteira_adr": 3,
	"vl_adr_invest_carteira": 4,
	"vl_invest_carteira_estrang_direta": 5,
	"vl_estrang_direta_invest_carteira": 6,
}


def _all_tags(xml: str) -> list[str]:
	"""Return every tag, containers included, in document order."""
	return re.findall(r"<([A-Z_0-9]+)>", xml)


def _tags(xml: str) -> list[str]:
	"""Return the leaf tags of ``xml`` in document order."""
	return re.findall(r"<([A-Z_0-9]+)>[^<\s]", xml)


def _p1(**participant: object) -> dict:
	"""P1."""
	base = {
		"cod_partic": PART,
		"entrada_saida": {"vl_entr": 10, "vl_saida": "20"},
		"transf_recursos": TRANSFERS,
		"patrim_liq": 99,
	}
	base.update(participant)
	return {
		"header": {"cd_cvm": "123", "dt_compt": "06/2026", "dt_gerac_arq": "31/07/2026"},
		"participantes": [base],
	}


def _p2(**blocks: object) -> dict:
	"""P2."""
	return {
		"header": {"dt_compt": "06/2026", "dt_gerac_arq": "31/07/2026"},
		"informs": [{"cod_partic": PART, **blocks}],
	}


POS = {"qtde_pos_fim": "1.5", "merc_pos_fim": "10.999"}
POS_M = {"merc_pos_fim": "7"}


def test_parte1_minimal_xml_tags_follow_spec() -> None:
	"""Test parte1 minimal xml tags follow spec."""
	xml = InrSemestralParte1().export(InrParte1Document(**_p1()))
	assert xml.startswith(
		'<?xml version="1.0" encoding="windows-1252"?>\n<DOC_ARQ xmlns="urn:infmensal">'
	)
	assert _tags(xml) == [
		"COD_DOC", "VERSAO", "CD_CVM", "DT_COMPT", "DT_GERAC_ARQ", "COD_PARTIC",
		"VL_ENTR", "VL_SAIDA", "VL_INVEST_CARTEIRA_HAVER_NRES",
		"VL_HAVER_NRES_INVEST_CARTEIRA", "VL_INVEST_CARTEIRA_ADR", "VL_ADR_INVEST_CARTEIRA",
		"VL_INVEST_CARTEIRA_ESTRANG_DIRETA", "VL_ESTRANG_DIRETA_INVEST_CARTEIRA", "PATRIM_LIQ",
	]  # fmt: skip
	assert "<COD_DOC>69</COD_DOC>" in xml


def test_parte1_resource_blocks_are_emitted_when_present() -> None:
	"""Test parte1 resource blocks are emitted when present."""
	block = {
		"recebidos": [{"cd_partic_origem": PART_2, "vl_recebido": 7}],
		"enviados": [{"cd_partic_dest": PART_2, "vl_enviado": 8}],
	}
	xml = InrSemestralParte1().export(
		InrParte1Document(**_p1(recursos_mesmo_invest=block, recursos_outro_invest=block))
	)
	tags = _all_tags(xml)
	assert tags.count("CD_PARTIC_ORIGEM") == 2
	assert tags.count("CD_PARTIC_DEST") == 2
	for name in ("MESMO", "OUTRO"):
		assert f"<RECURSOS_RECEB_{name}_INVEST>" in xml
		assert f"<RECURSOS_ENV_{name}_INVEST>" in xml
	assert tags.index("RECURSOS_MESMO_INVEST") < tags.index("RECURSOS_OUTRO_INVEST")
	assert tags[-1] == "PATRIM_LIQ"


def test_parte1_empty_exchange_block_is_omitted() -> None:
	"""Test parte1 empty exchange block is omitted."""
	xml = InrSemestralParte1().export(InrParte1Document(**_p1(recursos_mesmo_invest={})))
	assert "RECURSOS_MESMO_INVEST" not in xml


@pytest.mark.parametrize(
	"patch",
	[
		{"patrim_liq": 1.5},
		{"patrim_liq": "1.5"},
		{"patrim_liq": -1},
		{"patrim_liq": True},
		{"cod_partic": "0123.456.789.0-1"},
		{"cod_partic": "123.456.789.2-1"},
		{"cod_partic": "999.456.789.0-1"},
	],
)
def test_parte1_rejects_bad_values(patch: dict) -> None:
	"""Test parte1 rejects bad values."""
	with pytest.raises(ValidationError):
		InrParte1Document(**_p1(**patch))


@pytest.mark.parametrize(
	"header",
	[
		{"cd_cvm": "123", "dt_compt": "13/2026", "dt_gerac_arq": "31/07/2026"},
		{"cd_cvm": "123", "dt_compt": "06/2026", "dt_gerac_arq": "31/02/2026"},
		{"cd_cvm": "123", "dt_compt": "06/2026", "dt_gerac_arq": "31/07/2026\n"},
		{"cd_cvm": "0123", "dt_compt": "06/2026", "dt_gerac_arq": "31/07/2026"},
		{"cd_cvm": "123", "dt_compt": "06/1800", "dt_gerac_arq": "31/07/2026"},
	],
)
def test_parte1_rejects_bad_header(header: dict) -> None:
	"""Test parte1 rejects bad header."""
	data = _p1()
	data["header"] = header
	with pytest.raises(ValidationError):
		InrParte1Document(**data)


def test_parte1_rejects_duplicate_participant_and_empty_list() -> None:
	"""Test parte1 rejects duplicate participant and empty list."""
	data = _p1()
	data["participantes"] = data["participantes"] * 2
	with pytest.raises(ValidationError):
		InrParte1Document(**data)
	data["participantes"] = []
	with pytest.raises(ValidationError):
		InrParte1Document(**data)


def test_parte2_header_and_namespace() -> None:
	"""Test parte2 header and namespace."""
	xml = InrSemestralParte2().export(
		InrParte2Document(**_p2(cotas=[{"cnpj_fdo": CNPJ_A, "pos_fim": POS}]))
	)
	assert '<DOC_ARQ xmlns="urn:cda">' in xml
	assert _tags(xml)[:4] == ["COD_DOC", "VERSAO", "DT_COMPT", "DT_GERAC_ARQ"]
	assert "<COD_DOC>70</COD_DOC>" in xml


def test_parte2_cotas_and_decimal_scales_are_truncated_with_comma() -> None:
	"""Test parte2 cotas and decimal scales are truncated with comma."""
	xml = InrSemestralParte2().export(
		InrParte2Document(**_p2(cotas=[{"cnpj_fdo": CNPJ_A, "pos_fim": POS}]))
	)
	assert f"<CNPJ_FDO>{CNPJ_A_BARE}</CNPJ_FDO>" in xml
	assert "<QTDE_POS_FIM>1,500000</QTDE_POS_FIM>" in xml
	assert "<MERC_POS_FIM>10,99</MERC_POS_FIM>" in xml
	assert _tags(xml)[-3:] == ["CNPJ_FDO", "QTDE_POS_FIM", "MERC_POS_FIM"]


def test_parte2_tit_pub_tags() -> None:
	"""Test parte2 tit pub tags."""
	xml = InrSemestralParte2().export(
		InrParte2Document(
			**_p2(
				tit_pub=[
					{
						"cod_selic": "100000",
						"dt_venc": "15/08/2030",
						"cod_tp_aplic": "75",
						"pos_fim": POS,
					}
				]
			)
		)
	)
	assert _tags(xml)[-5:] == [
		"COD_SELIC",
		"DT_VENC",
		"COD_TP_APLIC",
		"QTDE_POS_FIM",
		"MERC_POS_FIM",
	]
	for tag in ("TIT_PUB", "COD_SELIC", "DT_VENC", "COD_TP_APLIC"):
		assert f"<{tag}>" in xml


def test_parte2_swap_requires_notional_and_checks_code() -> None:
	"""Test parte2 swap requires notional and checks code."""
	swap = {"cod_swap": "SWPSAB", "cod_tp_aplic": "183", "pos_fim": POS_M}
	with pytest.raises(ValidationError):
		InrParte2Document(**_p2(swap=[swap]))
	xml = InrSemestralParte2().export(InrParte2Document(**_p2(swap=[swap], nocion_swap="5")))
	assert "<NOCION_SWAP>5,00</NOCION_SWAP>" in xml
	assert xml.index("</SWAP>") < xml.index("<NOCION_SWAP>")
	for bad in ("SAB", "SWPZZZ", "SWPsab"):
		with pytest.raises(ValidationError):
			InrParte2Document(**_p2(swap=[{**swap, "cod_swap": bad}], nocion_swap="5"))
	with pytest.raises(ValidationError):
		InrParte2Document(**_p2(cotas=[{"cnpj_fdo": CNPJ_A, "pos_fim": POS}], nocion_swap="5"))


def test_parte2_demais_codif_table_a_and_b() -> None:
	"""Test parte2 demais codif table a and b."""
	item = {
		"cod_ativ": "PETR4",
		"cod_tp_ativ": "1",
		"dt_ini_vigen": "01/01/2020",
		"cod_tp_aplic": "37",
		"pos_fim": POS,
	}
	xml = InrSemestralParte2().export(InrParte2Document(**_p2(demais_codif=[item])))
	assert "<COD_ATIV>PETR4</COD_ATIV>" in xml
	assert "NOCION_POS_FIM" not in xml
	# 37 forbids notional; 39 requires quantity, market and notional
	with pytest.raises(ValidationError):
		InrParte2Document(
			**_p2(demais_codif=[{**item, "pos_fim": {**POS, "nocion_pos_fim": "1"}}])
		)
	opt = {
		**item,
		"cod_tp_ativ": "3",
		"cod_tp_aplic": "39",
		"pos_fim": {**POS, "nocion_pos_fim": "1"},
	}
	xml = InrSemestralParte2().export(InrParte2Document(**_p2(demais_codif=[opt])))
	assert "<NOCION_POS_FIM>1,00</NOCION_POS_FIM>" in xml
	with pytest.raises(ValidationError):
		InrParte2Document(**_p2(demais_codif=[{**opt, "pos_fim": POS}]))
	# Asset type 3 is an option, which Table B does not relate to application 37.
	with pytest.raises(ValidationError):
		InrParte2Document(**_p2(demais_codif=[{**item, "cod_tp_ativ": "3"}]))
	# type 75 does not belong in this block
	with pytest.raises(ValidationError):
		InrParte2Document(
			**_p2(demais_codif=[{**item, "cod_tp_aplic": "75", "cod_tp_ativ": "28"}])
		)


def test_parte2_quantity_never_negative_and_no_float() -> None:
	"""Test parte2 quantity never negative and no float."""
	for qty in ("-1", 1.5):
		with pytest.raises(ValidationError):
			InrParte2Document(
				**_p2(cotas=[{"cnpj_fdo": CNPJ_A, "pos_fim": {**POS, "qtde_pos_fim": qty}}])
			)
	with pytest.raises(ValidationError):
		InrParte2Document(
			**_p2(cotas=[{"cnpj_fdo": CNPJ_A, "pos_fim": {**POS, "merc_pos_fim": 1.5}}])
		)


def test_parte2_forbidden_quantity_for_swap() -> None:
	"""Test parte2 forbidden quantity for swap."""
	with pytest.raises(ValidationError):
		InrParte2Document(
			**_p2(
				swap=[{"cod_swap": "SWPSAB", "cod_tp_aplic": "184", "pos_fim": POS}],
				nocion_swap="1",
			)
		)


def test_parte2_dep_prazo_post_and_pre_fixed_and_rating() -> None:
	"""Test parte2 dep prazo post and pre fixed and rating."""
	base = {
		"cod_tp_ativ": "51",
		"emis": {"cnpj_emis": CNPJ_A, "nm_emis": "Banco X"},
		"dt_venc": "01/01/2030",
		"st_classif_risco": "N",
		"pos_fim": POS,
	}
	post = {
		**base,
		"st_tit_pos_fix": "S",
		"tit_pos_fix_index": {
			"tit_pos_fix_cod_index": "DI1",
			"tit_pos_fix_pr_index": "102",
			"tit_pos_fix_cupom": "0",
		},
	}
	xml = InrSemestralParte2().export(InrParte2Document(**_p2(dep_prazo_tit_if=[post])))
	assert "<TIT_POS_FIX_PR_INDEX>102,000000</TIT_POS_FIX_PR_INDEX>" in xml
	assert "<ST_TIT_POS_FIX>S</ST_TIT_POS_FIX>" in xml
	assert "TIT_PRE_FIX_TAXA_CONTR" not in xml
	pre = {**base, "st_tit_pos_fix": "N", "tit_pre_fix_taxa_contr": "15"}
	xml = InrSemestralParte2().export(InrParte2Document(**_p2(dep_prazo_tit_if=[pre])))
	assert "<TIT_PRE_FIX_TAXA_CONTR>15,000000</TIT_PRE_FIX_TAXA_CONTR>" in xml
	assert "TIT_POS_FIX_INDEX" not in xml
	for bad in (
		{**post, "tit_pre_fix_taxa_contr": "1"},
		{**pre, "tit_pre_fix_taxa_contr": None},
		{**pre, "st_classif_risco": "S"},
		{**post, "tit_pos_fix_index": None},
	):
		with pytest.raises(ValidationError):
			InrParte2Document(**_p2(dep_prazo_tit_if=[bad]))
	rated = {
		**pre,
		"st_classif_risco": "S",
		"classif_risco": {
			"ag_classif_risco": "Agency",
			"dt_classif_risco": "01/02/2026",
			"grau_classif_risco": "AAA",
		},
	}
	xml = InrSemestralParte2().export(InrParte2Document(**_p2(dep_prazo_tit_if=[rated])))
	assert "<GRAU_CLASSIF_RISCO>AAA</GRAU_CLASSIF_RISCO>" in xml


def test_parte2_tit_agro_issuer_documents() -> None:
	"""Test parte2 tit agro issuer documents."""
	item = {
		"cod_tp_ativ": "36",
		"emis": {"tp_pf_pj_emis": "PJ", "nr_pf_pj_emis": CNPJ_A, "nm_emis": "Emissor"},
		"dt_venc": "01/01/2030",
		"st_tit_pos_fix": "N",
		"tit_pre_fix_taxa_contr": "10",
		"st_tit_reg_cetip": "S",
		"st_tit_garant_seguro": "N",
		"cnpj_instit_financ": CNPJ_A,
		"cod_tp_aplic": "195",
		"pos_fim": POS,
	}
	xml = InrSemestralParte2().export(InrParte2Document(**_p2(tit_agro_cred_priv=[item])))
	assert f"<NR_PF_PJ_EMIS>{CNPJ_A_BARE}</NR_PF_PJ_EMIS>" in xml
	assert f"<CNPJ_INSTIT_FINANC>{CNPJ_A_BARE}</CNPJ_INSTIT_FINANC>" in xml
	pf = {**item, "emis": {"tp_pf_pj_emis": "PF", "nr_pf_pj_emis": CPF, "nm_emis": "Pessoa"}}
	xml = InrSemestralParte2().export(InrParte2Document(**_p2(tit_agro_cred_priv=[pf])))
	assert "<NR_PF_PJ_EMIS>52998224725</NR_PF_PJ_EMIS>" in xml
	for emis in (
		{"tp_pf_pj_emis": "PF", "nr_pf_pj_emis": CNPJ_A, "nm_emis": "x"},
		{"tp_pf_pj_emis": "PJ", "nr_pf_pj_emis": " " + CNPJ_A, "nm_emis": "x"},
		{"tp_pf_pj_emis": "PJ", "nr_pf_pj_emis": "11.222.333/0001-82", "nm_emis": "x"},
	):
		with pytest.raises(ValidationError):
			InrParte2Document(**_p2(tit_agro_cred_priv=[{**item, "emis": emis}]))


def test_parte2_inv_ext_tags_and_tables() -> None:
	"""Test parte2 inv ext tags and tables."""
	item = {
		"cod_tp_ativ": "20",
		"inv_coletivo": "N",
		"gest_inv_coletivo": "N",
		"nm_emis": "Foreign Co",
		"cod_pais": "77",
		"cod_bv_merc": "A11",
		"cod_ativo_bv_merc": "AAPL",
		"st_classif_risco": "N",
		"dt_aplic": "01/03/2026",
		"pos_fim": POS,
		"ativo_ext": {"desc_at_ext": "desc", "qtde_at_ext": 3, "valor_at_ext": "4.5"},
	}
	xml = InrSemestralParte2().export(InrParte2Document(**_p2(inv_ext=[item])))
	tags = _all_tags(xml)
	for tag in (
		"INV_COLETIVO",
		"GEST_INV_COLETIVO",
		"COD_PAIS",
		"COD_BV_MERC",
		"DT_APLIC",
		"ATIVO_EXT",
	):
		assert tag in tags
	assert "<VALOR_AT_EXT>4,50</VALOR_AT_EXT>" in xml
	assert tags.index("DT_APLIC") < tags.index("POS_FIM") < tags.index("ATIVO_EXT")
	for patch in ({"cod_pais": "9999"}, {"cod_bv_merc": "ZZ"}, {"cod_tp_ativ": "28"}):
		with pytest.raises(ValidationError):
			InrParte2Document(**_p2(inv_ext=[{**item, **patch}]))


def test_parte2_demais_n_codif_and_block_order() -> None:
	"""Test parte2 demais n codif and block order."""
	n_item = {
		"cod_tp_ativ": "999",
		"desc": "Disponibilidade",
		"emis": {"tp_pf_pj_emis": "PJ", "nr_pf_pj_emis": CNPJ_A, "nm_emis": "Banco"},
		"cod_tp_aplic": "94",
		"pos_fim": POS_M,
	}
	cot = {"cnpj_fdo": CNPJ_A, "pos_fim": POS}
	xml = InrSemestralParte2().export(
		InrParte2Document(**_p2(demais_n_codif=[n_item], cotas=[cot]))
	)
	tags = _all_tags(xml)
	assert tags.index("COTAS") < tags.index("DEMAIS_N_CODIF")
	with pytest.raises(ValidationError):
		InrParte2Document(**_p2(demais_n_codif=[{**n_item, "pos_fim": POS}]))


def test_parte2_requires_a_block_and_unique_participants() -> None:
	"""Test parte2 requires a block and unique participants."""
	with pytest.raises(ValidationError):
		InrParte2Document(**_p2())
	data = _p2(cotas=[{"cnpj_fdo": CNPJ_A, "pos_fim": POS}])
	data["informs"] = data["informs"] * 2
	with pytest.raises(ValidationError):
		InrParte2Document(**data)


def test_unknown_field_is_rejected() -> None:
	"""Test unknown field is rejected."""
	with pytest.raises(ValidationError):
		InrParte1Document(**_p1(bogus=1))


def test_export_writes_windows_1252_and_never_wipes_on_encoding_error(tmp_path: Path) -> None:
	"""Test export writes windows 1252 and never wipes on encoding error."""
	doc = InrParte2Document(
		**_p2(
			demais_n_codif=[
				{
					"cod_tp_ativ": "999",
					"desc": "Ação",
					"emis": {"tp_pf_pj_emis": "PJ", "nr_pf_pj_emis": CNPJ_A, "nm_emis": "Cia"},
					"cod_tp_aplic": "94",
					"pos_fim": POS_M,
				}
			]
		)
	)
	target = tmp_path / "p2.xml"
	assert InrSemestralParte2().export(doc, str(target)) is None
	assert "Ação".encode("windows-1252") in target.read_bytes()
	target.write_bytes(b"keep")
	with pytest.raises(ValidationError):
		InrParte2Document(
			**_p2(
				demais_n_codif=[
					{
						"cod_tp_ativ": "999",
						"desc": "中",
						"emis": {"tp_pf_pj_emis": "PJ", "nr_pf_pj_emis": CNPJ_A, "nm_emis": "Cia"},
						"cod_tp_aplic": "94",
						"pos_fim": POS_M,
					}
				]
			)
		)
	assert target.read_bytes() == b"keep"


def test_writer_encode_failure_leaves_existing_file(tmp_path: Path) -> None:
	"""Test writer encode failure leaves existing file."""
	from filings_cvm._internal.utils.inr_semestral_fields import write_xml_file

	target = tmp_path / "x.xml"
	target.write_bytes(b"keep")
	with pytest.raises(UnicodeEncodeError):
		write_xml_file(str(target), "中")
	assert target.read_bytes() == b"keep"


def test_parte1_export_to_file_returns_none(tmp_path: Path) -> None:
	"""Test parte1 export to file returns none."""
	target = tmp_path / "p1.xml"
	assert InrSemestralParte1().export(InrParte1Document(**_p1()), str(target)) is None
	assert target.read_bytes().startswith(b"<?xml")


def test_decimal_input_is_accepted() -> None:
	"""Test decimal input is accepted."""
	doc = InrParte2Document(
		**_p2(
			cotas=[
				{"cnpj_fdo": CNPJ_A, "pos_fim": {"qtde_pos_fim": Decimal("2"), "merc_pos_fim": 3}}
			]
		)
	)
	assert "<MERC_POS_FIM>3,00</MERC_POS_FIM>" in InrSemestralParte2().export(doc)
