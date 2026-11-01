"""Unit tests for the Informe Semestral de INR writers (Parte I and Parte II)."""

import contextlib
from decimal import Decimal
from pathlib import Path
import re

from pydantic import ValidationError
import pytest

from filings_cvm._internal.utils.inr_semestral_fields import write_xml_file
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


COTAS = {"cnpj_fdo": CNPJ_A, "pos_fim": POS}
SWAP = {"cod_swap": "SWPSAB", "cod_tp_aplic": "183", "pos_fim": POS_M}
DEMAIS = {
	"cod_ativ": "PETR4",
	"cod_tp_ativ": "1",
	"dt_ini_vigen": "01/01/2020",
	"cod_tp_aplic": "37",
	"pos_fim": POS,
}
DEMAIS_OPT = {
	**DEMAIS,
	"cod_tp_ativ": "3",
	"cod_tp_aplic": "39",
	"pos_fim": {**POS, "nocion_pos_fim": "1"},
}
DEP_BASE = {
	"cod_tp_ativ": "51",
	"emis": {"cnpj_emis": CNPJ_A, "nm_emis": "Banco X"},
	"dt_venc": "01/01/2030",
	"st_classif_risco": "N",
	"pos_fim": POS,
}
DEP_POST = {
	**DEP_BASE,
	"st_tit_pos_fix": "S",
	"tit_pos_fix_index": {
		"tit_pos_fix_cod_index": "DI1",
		"tit_pos_fix_pr_index": "102",
		"tit_pos_fix_cupom": "0",
	},
}
DEP_PRE = {**DEP_BASE, "st_tit_pos_fix": "N", "tit_pre_fix_taxa_contr": "15"}
DEP_RATED = {
	**DEP_PRE,
	"st_classif_risco": "S",
	"classif_risco": {
		"ag_classif_risco": "Agency",
		"dt_classif_risco": "01/02/2026",
		"grau_classif_risco": "AAA",
	},
}
AGRO = {
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
AGRO_PF = {
	**AGRO,
	"emis": {"tp_pf_pj_emis": "PF", "nr_pf_pj_emis": CPF, "nm_emis": "Pessoa"},
}
INV_EXT = {
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
N_CODIF = {
	"cod_tp_ativ": "999",
	"desc": "Disponibilidade",
	"emis": {"tp_pf_pj_emis": "PJ", "nr_pf_pj_emis": CNPJ_A, "nm_emis": "Banco"},
	"cod_tp_aplic": "94",
	"pos_fim": POS_M,
}
BLOCK = {
	"recebidos": [{"cd_partic_origem": PART_2, "vl_recebido": 7}],
	"enviados": [{"cd_partic_dest": PART_2, "vl_enviado": 8}],
}


def _x1(**participant: object) -> str:
	"""Export a Parte I document built from ``_p1``."""
	return InrSemestralParte1().export(InrParte1Document(**_p1(**participant)))


def _x2(**blocks: object) -> str:
	"""Export a Parte II document built from ``_p2``."""
	return InrSemestralParte2().export(InrParte2Document(**_p2(**blocks)))


def test_parte1_declaration_and_namespace() -> None:
	"""Test parte1 declaration and namespace."""
	assert _x1().startswith(
		'<?xml version="1.0" encoding="windows-1252"?>\n<DOC_ARQ xmlns="urn:infmensal">'
	)


def test_parte1_minimal_xml_tags_follow_spec() -> None:
	"""Test parte1 minimal xml tags follow spec."""
	assert _tags(_x1()) == [
		"COD_DOC", "VERSAO", "CD_CVM", "DT_COMPT", "DT_GERAC_ARQ", "COD_PARTIC",
		"VL_ENTR", "VL_SAIDA", "VL_INVEST_CARTEIRA_HAVER_NRES",
		"VL_HAVER_NRES_INVEST_CARTEIRA", "VL_INVEST_CARTEIRA_ADR", "VL_ADR_INVEST_CARTEIRA",
		"VL_INVEST_CARTEIRA_ESTRANG_DIRETA", "VL_ESTRANG_DIRETA_INVEST_CARTEIRA", "PATRIM_LIQ",
	]  # fmt: skip


def test_parte1_cod_doc_is_69() -> None:
	"""Test parte1 cod doc is 69."""
	assert "<COD_DOC>69</COD_DOC>" in _x1()


@pytest.mark.parametrize(
	"needle",
	[
		"<RECURSOS_RECEB_MESMO_INVEST>",
		"<RECURSOS_ENV_MESMO_INVEST>",
		"<RECURSOS_RECEB_OUTRO_INVEST>",
		"<RECURSOS_ENV_OUTRO_INVEST>",
	],
)
def test_parte1_resource_blocks_are_emitted_when_present(needle: str) -> None:
	"""Test parte1 resource blocks are emitted when present."""
	assert needle in _x1(recursos_mesmo_invest=BLOCK, recursos_outro_invest=BLOCK)


@pytest.mark.parametrize("tag", ["CD_PARTIC_ORIGEM", "CD_PARTIC_DEST"])
def test_parte1_resource_entries_appear_once_per_block(tag: str) -> None:
	"""Test parte1 resource entries appear once per block."""
	xml = _x1(recursos_mesmo_invest=BLOCK, recursos_outro_invest=BLOCK)
	assert _all_tags(xml).count(tag) == 2


def test_parte1_resource_blocks_keep_spec_order() -> None:
	"""Test parte1 resource blocks keep spec order."""
	tags = _all_tags(_x1(recursos_mesmo_invest=BLOCK, recursos_outro_invest=BLOCK))
	assert tags.index("RECURSOS_MESMO_INVEST") < tags.index("RECURSOS_OUTRO_INVEST")


def test_parte1_patrim_liq_closes_the_participant() -> None:
	"""Test parte1 patrim liq closes the participant."""
	tags = _all_tags(_x1(recursos_mesmo_invest=BLOCK, recursos_outro_invest=BLOCK))
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


@pytest.mark.parametrize("copies", [2, 0])
def test_parte1_rejects_duplicate_participant_and_empty_list(copies: int) -> None:
	"""Test parte1 rejects duplicate participant and empty list."""
	data = _p1()
	data["participantes"] = data["participantes"] * copies
	with pytest.raises(ValidationError):
		InrParte1Document(**data)


@pytest.mark.parametrize(
	"needle",
	['<DOC_ARQ xmlns="urn:cda">', "<COD_DOC>70</COD_DOC>"],
)
def test_parte2_header_and_namespace(needle: str) -> None:
	"""Test parte2 header and namespace."""
	assert needle in _x2(cotas=[COTAS])


def test_parte2_header_tags_come_first() -> None:
	"""Test parte2 header tags come first."""
	assert _tags(_x2(cotas=[COTAS]))[:4] == ["COD_DOC", "VERSAO", "DT_COMPT", "DT_GERAC_ARQ"]


@pytest.mark.parametrize(
	"needle",
	[
		f"<CNPJ_FDO>{CNPJ_A_BARE}</CNPJ_FDO>",
		"<QTDE_POS_FIM>1,500000</QTDE_POS_FIM>",
		"<MERC_POS_FIM>10,99</MERC_POS_FIM>",
	],
)
def test_parte2_cotas_and_decimal_scales_are_truncated_with_comma(needle: str) -> None:
	"""Test parte2 cotas and decimal scales are truncated with comma."""
	assert needle in _x2(cotas=[COTAS])


def test_parte2_cotas_tag_order() -> None:
	"""Test parte2 cotas tag order."""
	assert _tags(_x2(cotas=[COTAS]))[-3:] == ["CNPJ_FDO", "QTDE_POS_FIM", "MERC_POS_FIM"]


TIT_PUB = {
	"cod_selic": "100000",
	"dt_venc": "15/08/2030",
	"cod_tp_aplic": "75",
	"pos_fim": POS,
}


def test_parte2_tit_pub_tags() -> None:
	"""Test parte2 tit pub tags."""
	assert _tags(_x2(tit_pub=[TIT_PUB]))[-5:] == [
		"COD_SELIC",
		"DT_VENC",
		"COD_TP_APLIC",
		"QTDE_POS_FIM",
		"MERC_POS_FIM",
	]


@pytest.mark.parametrize("tag", ["TIT_PUB", "COD_SELIC", "DT_VENC", "COD_TP_APLIC"])
def test_parte2_tit_pub_containers(tag: str) -> None:
	"""Test parte2 tit pub containers."""
	assert f"<{tag}>" in _x2(tit_pub=[TIT_PUB])


def test_parte2_swap_requires_notional() -> None:
	"""Test parte2 swap requires notional."""
	with pytest.raises(ValidationError):
		InrParte2Document(**_p2(swap=[SWAP]))


def test_parte2_swap_emits_notional() -> None:
	"""Test parte2 swap emits notional."""
	assert "<NOCION_SWAP>5,00</NOCION_SWAP>" in _x2(swap=[SWAP], nocion_swap="5")


def test_parte2_swap_notional_follows_swap_block() -> None:
	"""Test parte2 swap notional follows swap block."""
	xml = _x2(swap=[SWAP], nocion_swap="5")
	assert xml.index("</SWAP>") < xml.index("<NOCION_SWAP>")


@pytest.mark.parametrize("bad", ["SAB", "SWPZZZ", "SWPsab"])
def test_parte2_swap_checks_code(bad: str) -> None:
	"""Test parte2 swap checks code."""
	with pytest.raises(ValidationError):
		InrParte2Document(**_p2(swap=[{**SWAP, "cod_swap": bad}], nocion_swap="5"))


def test_parte2_notional_forbidden_without_swap() -> None:
	"""Test parte2 notional forbidden without swap."""
	with pytest.raises(ValidationError):
		InrParte2Document(**_p2(cotas=[COTAS], nocion_swap="5"))


@pytest.mark.parametrize("needle", ["<COD_ATIV>PETR4</COD_ATIV>"])
def test_parte2_demais_codif_emits_asset_code(needle: str) -> None:
	"""Test parte2 demais codif emits asset code."""
	assert needle in _x2(demais_codif=[DEMAIS])


def test_parte2_application_37_has_no_notional() -> None:
	"""Test parte2 application 37 has no notional."""
	assert "NOCION_POS_FIM" not in _x2(demais_codif=[DEMAIS])


def test_parte2_application_39_emits_notional() -> None:
	"""Test parte2 application 39 emits notional."""
	assert "<NOCION_POS_FIM>1,00</NOCION_POS_FIM>" in _x2(demais_codif=[DEMAIS_OPT])


@pytest.mark.parametrize(
	"bad",
	[
		# 37 forbids a notional
		{**DEMAIS, "pos_fim": {**POS, "nocion_pos_fim": "1"}},
		# 39 requires the notional
		{**DEMAIS_OPT, "pos_fim": POS},
		# asset type 3 is an option, which Table B does not relate to application 37
		{**DEMAIS, "cod_tp_ativ": "3"},
		# type 75 does not belong in this block
		{**DEMAIS, "cod_tp_aplic": "75", "cod_tp_ativ": "28"},
	],
)
def test_parte2_demais_codif_table_a_and_b(bad: dict) -> None:
	"""Test parte2 demais codif table a and b."""
	with pytest.raises(ValidationError):
		InrParte2Document(**_p2(demais_codif=[bad]))


@pytest.mark.parametrize(
	"pos_fim",
	[
		{**POS, "qtde_pos_fim": "-1"},
		{**POS, "qtde_pos_fim": 1.5},
		{**POS, "merc_pos_fim": 1.5},
	],
)
def test_parte2_quantity_never_negative_and_no_float(pos_fim: dict) -> None:
	"""Test parte2 quantity never negative and no float."""
	with pytest.raises(ValidationError):
		InrParte2Document(**_p2(cotas=[{"cnpj_fdo": CNPJ_A, "pos_fim": pos_fim}]))


def test_parte2_forbidden_quantity_for_swap() -> None:
	"""Test parte2 forbidden quantity for swap."""
	with pytest.raises(ValidationError):
		InrParte2Document(
			**_p2(
				swap=[{"cod_swap": "SWPSAB", "cod_tp_aplic": "184", "pos_fim": POS}],
				nocion_swap="1",
			)
		)


@pytest.mark.parametrize(
	("item", "needle"),
	[
		(DEP_POST, "<TIT_POS_FIX_PR_INDEX>102,000000</TIT_POS_FIX_PR_INDEX>"),
		(DEP_POST, "<ST_TIT_POS_FIX>S</ST_TIT_POS_FIX>"),
		(DEP_PRE, "<TIT_PRE_FIX_TAXA_CONTR>15,000000</TIT_PRE_FIX_TAXA_CONTR>"),
		(DEP_RATED, "<GRAU_CLASSIF_RISCO>AAA</GRAU_CLASSIF_RISCO>"),
	],
)
def test_parte2_dep_prazo_emits_expected_fields(item: dict, needle: str) -> None:
	"""Test parte2 dep prazo emits expected fields."""
	assert needle in _x2(dep_prazo_tit_if=[item])


@pytest.mark.parametrize(
	("item", "absent"),
	[(DEP_POST, "TIT_PRE_FIX_TAXA_CONTR"), (DEP_PRE, "TIT_POS_FIX_INDEX")],
)
def test_parte2_dep_prazo_omits_the_other_indexation(item: dict, absent: str) -> None:
	"""Test parte2 dep prazo omits the other indexation."""
	assert absent not in _x2(dep_prazo_tit_if=[item])


@pytest.mark.parametrize(
	"bad",
	[
		{**DEP_POST, "tit_pre_fix_taxa_contr": "1"},
		{**DEP_PRE, "tit_pre_fix_taxa_contr": None},
		{**DEP_PRE, "st_classif_risco": "S"},
		{**DEP_POST, "tit_pos_fix_index": None},
	],
)
def test_parte2_dep_prazo_rejects_inconsistent_fields(bad: dict) -> None:
	"""Test parte2 dep prazo rejects inconsistent fields."""
	with pytest.raises(ValidationError):
		InrParte2Document(**_p2(dep_prazo_tit_if=[bad]))


@pytest.mark.parametrize(
	("item", "needle"),
	[
		(AGRO, f"<NR_PF_PJ_EMIS>{CNPJ_A_BARE}</NR_PF_PJ_EMIS>"),
		(AGRO, f"<CNPJ_INSTIT_FINANC>{CNPJ_A_BARE}</CNPJ_INSTIT_FINANC>"),
		(AGRO_PF, "<NR_PF_PJ_EMIS>52998224725</NR_PF_PJ_EMIS>"),
	],
)
def test_parte2_tit_agro_issuer_documents(item: dict, needle: str) -> None:
	"""Test parte2 tit agro issuer documents."""
	assert needle in _x2(tit_agro_cred_priv=[item])


@pytest.mark.parametrize(
	"emis",
	[
		{"tp_pf_pj_emis": "PF", "nr_pf_pj_emis": CNPJ_A, "nm_emis": "x"},
		{"tp_pf_pj_emis": "PJ", "nr_pf_pj_emis": " " + CNPJ_A, "nm_emis": "x"},
		{"tp_pf_pj_emis": "PJ", "nr_pf_pj_emis": "11.222.333/0001-82", "nm_emis": "x"},
	],
)
def test_parte2_tit_agro_rejects_bad_issuer_document(emis: dict) -> None:
	"""Test parte2 tit agro rejects bad issuer document."""
	with pytest.raises(ValidationError):
		InrParte2Document(**_p2(tit_agro_cred_priv=[{**AGRO, "emis": emis}]))


@pytest.mark.parametrize(
	"tag",
	["INV_COLETIVO", "GEST_INV_COLETIVO", "COD_PAIS", "COD_BV_MERC", "DT_APLIC", "ATIVO_EXT"],
)
def test_parte2_inv_ext_tags(tag: str) -> None:
	"""Test parte2 inv ext tags."""
	assert tag in _all_tags(_x2(inv_ext=[INV_EXT]))


def test_parte2_inv_ext_foreign_asset_value_scale() -> None:
	"""Test parte2 inv ext foreign asset value scale."""
	assert "<VALOR_AT_EXT>4,50</VALOR_AT_EXT>" in _x2(inv_ext=[INV_EXT])


def test_parte2_inv_ext_tag_order() -> None:
	"""Test parte2 inv ext tag order."""
	tags = _all_tags(_x2(inv_ext=[INV_EXT]))
	assert tags.index("DT_APLIC") < tags.index("POS_FIM") < tags.index("ATIVO_EXT")


@pytest.mark.parametrize(
	"patch", [{"cod_pais": "9999"}, {"cod_bv_merc": "ZZ"}, {"cod_tp_ativ": "28"}]
)
def test_parte2_inv_ext_checks_tables(patch: dict) -> None:
	"""Test parte2 inv ext checks tables."""
	with pytest.raises(ValidationError):
		InrParte2Document(**_p2(inv_ext=[{**INV_EXT, **patch}]))


def test_parte2_blocks_follow_spec_order() -> None:
	"""Test parte2 blocks follow spec order."""
	tags = _all_tags(_x2(demais_n_codif=[N_CODIF], cotas=[COTAS]))
	assert tags.index("COTAS") < tags.index("DEMAIS_N_CODIF")


def test_parte2_demais_n_codif_rejects_forbidden_quantity() -> None:
	"""Test parte2 demais n codif rejects forbidden quantity."""
	with pytest.raises(ValidationError):
		InrParte2Document(**_p2(demais_n_codif=[{**N_CODIF, "pos_fim": POS}]))


def test_parte2_requires_a_block() -> None:
	"""Test parte2 requires a block."""
	with pytest.raises(ValidationError):
		InrParte2Document(**_p2())


def test_parte2_rejects_duplicate_participants() -> None:
	"""Test parte2 rejects duplicate participants."""
	data = _p2(cotas=[COTAS])
	data["informs"] = data["informs"] * 2
	with pytest.raises(ValidationError):
		InrParte2Document(**data)


def test_unknown_field_is_rejected() -> None:
	"""Test unknown field is rejected."""
	with pytest.raises(ValidationError):
		InrParte1Document(**_p1(bogus=1))


ACAO = {**N_CODIF, "desc": "Ação", "emis": {**N_CODIF["emis"], "nm_emis": "Cia"}}


def test_export_returns_none_when_writing_a_file(tmp_path: Path) -> None:
	"""Test export returns none when writing a file."""
	doc = InrParte2Document(**_p2(demais_n_codif=[ACAO]))
	assert InrSemestralParte2().export(doc, str(tmp_path / "p2.xml")) is None


def test_export_writes_windows_1252(tmp_path: Path) -> None:
	"""Test export writes windows 1252."""
	target = tmp_path / "p2.xml"
	InrSemestralParte2().export(InrParte2Document(**_p2(demais_n_codif=[ACAO])), str(target))
	assert "Ação".encode("windows-1252") in target.read_bytes()


def test_schema_rejects_text_windows_1252_cannot_encode() -> None:
	"""Test schema rejects text windows 1252 cannot encode."""
	with pytest.raises(ValidationError):
		InrParte2Document(**_p2(demais_n_codif=[{**ACAO, "desc": "中"}]))


@pytest.fixture
def kept_file(tmp_path: Path) -> Path:
	"""Return a destination holding ``keep`` after a failed (unencodable) write to it."""
	target = tmp_path / "x.xml"
	target.write_bytes(b"keep")
	with contextlib.suppress(UnicodeEncodeError):
		write_xml_file(str(target), "中")
	return target


def test_writer_encode_failure_raises(tmp_path: Path) -> None:
	"""Test writer encode failure raises."""
	with pytest.raises(UnicodeEncodeError):
		write_xml_file(str(tmp_path / "x.xml"), "中")


def test_writer_encode_failure_leaves_existing_file(kept_file: Path) -> None:
	"""Test writer encode failure leaves existing file."""
	assert kept_file.read_bytes() == b"keep"


def test_parte1_export_to_file_returns_none(tmp_path: Path) -> None:
	"""Test parte1 export to file returns none."""
	assert (
		InrSemestralParte1().export(InrParte1Document(**_p1()), str(tmp_path / "p1.xml")) is None
	)


def test_parte1_export_to_file_writes_declaration(tmp_path: Path) -> None:
	"""Test parte1 export to file writes declaration."""
	target = tmp_path / "p1.xml"
	InrSemestralParte1().export(InrParte1Document(**_p1()), str(target))
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
