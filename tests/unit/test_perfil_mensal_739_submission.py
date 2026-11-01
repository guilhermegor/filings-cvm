"""Unit tests for the Perfil Mensal ICVM 739 submission writer.

The expected tag order, header and decimal scales are pinned to the CVM page
``PadraoXMLPerfil739.asp`` (XML sample and tag table), not to the V4 writer.
"""

from pathlib import Path
import re

from pydantic import ValidationError
import pytest

from filings_cvm.submission import (
	ClientCount,
	DocumentHeader,
	NominalRiskBlock,
	NominalRiskFactor,
	OtcOperation,
	PatrimonyDistribution739,
	PerfilMensal,
	PerfilMensal739,
	PerfilMensal739Document,
	PerfilMensal739Row,
	PerfilMensalDocument,
	PerformanceFeeDetails,
	PrimitiveRiskFactor,
	PrivateCreditIssuer,
	VarOutros739,
	VarPercValCota,
)


VALID_CNPJ = "11222333000181"

# First-occurrence tag order of the ROW_PERFIL sample on the 739 page (79 tags).
# Unlike V3/V4 the sample ends at VAL_COTA_FUNDO: no MONTANTE_DISTRIB, no INF_COMPL_PERFIL.
PAGE_TAG_ORDER = (
	"CNPJ_FDO",
	"NR_CLIENT",
	"NR_PF_PRIV_BANK",
	"NR_PF_VARJ",
	"NR_PJ_N_FINANC_PRIV_BANK",
	"NR_PJ_N_FINANC_VARJ",
	"NR_BNC_COMERC",
	"NR_PJ_CORR_DIST",
	"NR_PJ_OUTR_FINANC",
	"NR_INV_N_RES",
	"NR_ENT_AB_PREV_COMPL",
	"NR_ENT_FC_PREV_COMPL",
	"NR_REG_PREV_SERV_PUB",
	"NR_SOC_SEG_RESEG",
	"NR_SOC_CAPTLZ_ARRENDM_MERC",
	"NR_FDOS_CLUB_INV",
	"NR_COTST_DISTR_FDO",
	"NR_OUTROS_N_RELAC",
	"DISTR_PATRIM",
	"PR_PF_PRIV_BANK",
	"PR_PF_VARJ",
	"PR_PJ_N_FINANC_PRIV_BANK",
	"PR_PJ_N_FINANC_VARJ",
	"PR_BNC_COMERC",
	"PR_PJ_CORR_DIST",
	"PR_PJ_OUTR_FINANC",
	"PR_INV_N_RES",
	"PR_ENT_AB_PREV_COMPL",
	"PR_ENT_FC_PREV_COMPL",
	"PR_REG_PREV_SERV_PUB",
	"PR_SOC_SEG_RESEG",
	"PR_SOC_CAPTLZ_ARRENDM_MERC",
	"PR_FDOS_CLUB_INV",
	"PR_COTST_DISTR_FDO",
	"PR_OUTROS_N_RELAC",
	"RESM_TEOR_VT_PROFRD",
	"JUST_SUM_VT_PROFRD",
	"VAR_PERC_PL",
	"MOD_VAR_UTILIZ",
	"PRAZ_MED_CART_TIT",
	"RES_DELIB",
	"TOTAL_RECURS_EXTER",
	"TOTAL_RECURS_BR",
	"VARIACAO_PERC_VAL_COTA",
	"VAL_PERCENT",
	"LISTA_FATOR_PRIMIT_RISCO",
	"FATOR_PRIMIT_RISCO",
	"NOME_FATOR_PRIMIT_RISCO",
	"CEN_UTIL",
	"VAR_DIAR_PERC_COTA_FDO_PIOR_CEN_ESTRESS",
	"VAR_DIAR_PERC_PATRIM_FDO_VAR_N_TAXA_ANUAL",
	"VAR_DIAR_PERC_PATRIM_FDO_VAR_N_TAXA_CAMBIO",
	"VAR_PATRIM_FDO_N_PRECO_ACOES",
	"VARIACAO_DIAR_PERC_PATRIM_FDO_VAR_N_OUTROS",
	"FATOR_RISCO_OUTROS",
	"VAL_PERCENT_OUTROS",
	"VALOR_NOC_TOT_CONTRAT_DERIV_MANT_FDO",
	"VAL_COLATERAL",
	"LISTA_FATOR_RISCO_NOC",
	"FATOR_RISCO_NOC",
	"NOME_FATOR_NOC",
	"VAL_FATOR_RISCO_NOC_LONG",
	"VAL_FATOR_RISCO_NOC_SHORT",
	"LISTA_OPER_CURS_MERC_BALCAO",
	"OPER_CURS_MERC_BALCAO",
	"TP_PESSOA",
	"NR_PF_PJ_COMITENTE",
	"PARTE_RELACIONADA",
	"VALOR_PARTE",
	"TOT_ATIVOS_P_RELAC",
	"LISTA_EMISSORES_TIT_CRED_PRIV",
	"EMISSORES_TIT_CRED_PRIV",
	"TP_PESSOA_EMISSOR",
	"NR_PF_PJ_EMISSOR",
	"TOT_ATIVOS_CRED_PRIV",
	"VED_REGUL_COBR_TAXA_PERFORM",
	"RESP_VED_REGUL_COBR_TAXA_PERFORM",
	"DATA_COTA_FUNDO",
	"VAL_COTA_FUNDO",
)

_PR_FIELDS = tuple(PatrimonyDistribution739.model_fields)


def _row(**overrides: object) -> PerfilMensal739Row:
	"""Build a minimal valid 739 row; ``overrides`` replace or add row fields."""
	fields: dict[str, object] = {
		"cnpj_fdo": VALID_CNPJ,
		"nr_client": ClientCount(**dict.fromkeys(ClientCount.model_fields, 0)),
		"distr_patrim": PatrimonyDistribution739(**dict.fromkeys(_PR_FIELDS, "0")),
		"total_recurs_exter": "0",
		"total_recurs_br": "0",
		"tot_ativos_p_relac": "0",
		"tot_ativos_cred_priv": "0",
	}
	return PerfilMensal739Row(**(fields | overrides))


def _full_row() -> PerfilMensal739Row:
	"""Build a row that fills every block the 739 page defines."""
	return _row(
		resm_teor_vt_profrd="resumo",
		just_sum_vt_profrd="justificativa",
		var_perc_pl="1.5",
		mod_var_utiliz="1",
		praz_med_cart_tit="2.5",
		res_delib="deliberacao",
		variacao_perc_val_cota=VarPercValCota(
			val_percent="5.5",
			lista_fator_primit_risco=[
				PrimitiveRiskFactor(nome_fator_primit_risco="IBOVESPA", cen_util="scenario"),
			],
		),
		var_diar_perc_cota_fdo_pior_cen_estress="1.1",
		var_diar_perc_patrim_fdo_var_n_taxa_anual="2.2",
		var_diar_perc_patrim_fdo_var_n_taxa_cambio="3.3",
		var_patrim_fdo_n_preco_acoes="4.4",
		variacao_diar_perc_patrim_fdo_var_n_outros=VarOutros739(
			fator_risco_outros="fator", val_percent_outros="6.6"
		),
		valor_noc_tot_contrat_deriv_mant_fdo=NominalRiskBlock(
			val_colateral="7.7",
			lista_fator_risco_noc=[
				NominalRiskFactor(
					nome_fator_noc="DOLAR", val_fator_risco_noc_long=1, val_fator_risco_noc_short=2
				),
			],
		),
		lista_oper_curs_merc_balcao=[
			OtcOperation(
				tp_pessoa="PJ",
				nr_pf_pj_comitente=VALID_CNPJ,
				parte_relacionada="N",
				valor_parte="8.8",
			),
		],
		lista_emissores_tit_cred_priv=[
			PrivateCreditIssuer(
				tp_pessoa_emissor="PJ",
				nr_pf_pj_emissor=VALID_CNPJ,
				parte_relacionada="S",
				valor_parte="9.9",
			),
		],
		ved_regul_cobr_taxa_perform="S",
		resp_ved_regul_cobr_taxa_perform=PerformanceFeeDetails(
			data_cota_fundo="01/01/2025", val_cota_fundo="1.23456"
		),
	)


def _document(row: PerfilMensal739Row) -> PerfilMensal739Document:
	"""Wrap one row in a 739 document."""
	header = DocumentHeader(dt_compt="01/2013", dt_gerac_arq="15/01/2013")
	return PerfilMensal739Document(header=header, rows=[row])


def _xml(row: PerfilMensal739Row) -> str:
	"""Serialize a one-row 739 document."""
	xml = PerfilMensal739().export(_document(row))
	assert xml is not None
	return xml


def _row_tags(xml: str) -> list[str]:
	"""Return the first occurrence of every tag inside ROW_PERFIL, in emission order."""
	tags = re.findall(r"<([A-Z_0-9]+)>", xml.split("<ROW_PERFIL>")[1])
	return list(dict.fromkeys(tags))


def test_export_declaration_is_windows_1252() -> None:
	"""The XML declaration names windows-1252, as the page's sample does."""
	assert _xml(_row()).startswith('<?xml version="1.0" encoding="windows-1252"?>')


def test_export_root_namespace_is_urn_perf() -> None:
	"""The root element carries the page's ``urn:perf`` namespace."""
	assert '<DOC_ARQ xmlns="urn:perf">' in _xml(_row())


def test_export_versao_is_one() -> None:
	"""VERSAO is 1.0, as the page's tag table requires, never the V4 value."""
	assert "<VERSAO>1.0</VERSAO>" in _xml(_row())


def test_export_cod_doc_is_forty() -> None:
	"""COD_DOC is 40 with no leading zeros."""
	assert "<COD_DOC>40</COD_DOC>" in _xml(_row())


def test_export_full_row_tag_order_matches_the_page_exactly() -> None:
	"""A row with every block filled emits exactly the page's tags, in the page's order."""
	assert tuple(_row_tags(_xml(_full_row()))) == PAGE_TAG_ORDER


def test_export_minimal_row_tags_are_an_ordered_subsequence_of_the_page() -> None:
	"""Omitted optional blocks leave the remaining tags in page order."""
	order = iter(PAGE_TAG_ORDER)

	assert all(tag in order for tag in _row_tags(_xml(_row())))


@pytest.mark.parametrize(
	"tag",
	[
		"VAR_DIAR_PERC_PATRIM_FDO_VAR_N_TAXA_ANUAL",
		"VAR_DIAR_PERC_PATRIM_FDO_VAR_N_TAXA_CAMBIO",
		"VAR_PATRIM_FDO_N_PRECO_ACOES",
		"VAL_PERCENT_OUTROS",
	],
)
def test_export_sensitivity_tags_have_two_decimals(tag: str) -> None:
	"""The 739 tag table says two decimals where V3/V4 say four."""
	xml = _xml(_full_row())

	assert re.search(rf"<{tag}>\d+,\d{{2}}</{tag}>", xml) is not None


def test_sensitivity_value_is_truncated_not_rounded_to_two_decimals() -> None:
	"""Excess digits are cut toward zero at the 739 scale of two."""
	xml = _xml(_row(var_patrim_fdo_n_preco_acoes="-1.239"))

	assert "<VAR_PATRIM_FDO_N_PRECO_ACOES>-1,23</VAR_PATRIM_FDO_N_PRECO_ACOES>" in xml


def test_v4_writer_keeps_four_decimals_for_the_same_tags() -> None:
	"""Parametrising the scale for 739 must not change the V4 writer."""
	row = _row().model_dump() | {"var_patrim_fdo_n_preco_acoes": "1.2345"}
	header = {"dt_compt": "01/2025", "dt_gerac_arq": "15/01/2025"}
	doc = PerfilMensalDocument.model_validate({"header": header, "rows": [row]})

	xml = PerfilMensal().export(doc) or ""

	assert "<VAR_PATRIM_FDO_N_PRECO_ACOES>1,2345</VAR_PATRIM_FDO_N_PRECO_ACOES>" in xml


def _xml_with_pr_pf_varj(value: str) -> str:
	"""Serialize a row whose PR_PF_VARJ is ``value`` and the other PR_* tags are zero."""
	distr = PatrimonyDistribution739(**(dict.fromkeys(_PR_FIELDS, "0") | {"pr_pf_varj": value}))
	return _xml(_row(distr_patrim=distr))


def test_export_distr_patrim_emits_all_sixteen_tags() -> None:
	"""All 16 PR_* tags are emitted."""
	assert _xml_with_pr_pf_varj("0").count("<PR_") == 16


def test_export_distr_patrim_truncates_to_one_decimal() -> None:
	"""PR_* carries one decimal, truncated, with a comma separator."""
	assert "<PR_PF_VARJ>12,3</PR_PF_VARJ>" in _xml_with_pr_pf_varj("12.34")


def test_row_without_distr_patrim_is_rejected() -> None:
	"""DISTR_PATRIM is mandatory in 739."""
	fields = _row().model_dump(exclude={"distr_patrim"})

	with pytest.raises(ValidationError):
		PerfilMensal739Row.model_validate(fields)


def test_distr_patrim_missing_one_tag_is_rejected() -> None:
	"""Each of the 16 PR_* tags is individually mandatory."""
	with pytest.raises(ValidationError):
		PatrimonyDistribution739(**dict.fromkeys(_PR_FIELDS[1:], "0"))


def test_distr_patrim_above_hundred_is_rejected() -> None:
	"""PR_* values are capped at 100."""
	with pytest.raises(ValidationError):
		PatrimonyDistribution739(**(dict.fromkeys(_PR_FIELDS, "0") | {"pr_pf_varj": "100.1"}))


@pytest.mark.parametrize("field", ["montante_distrib", "inf_compl_perfil"])
def test_row_rejects_tags_the_739_page_does_not_define(field: str) -> None:
	"""MONTANTE_DISTRIB and INF_COMPL_PERFIL are post-739 tags and must not reach the file."""
	with pytest.raises(ValidationError):
		_row(**{field: "1"})


def test_row_invalid_cnpj_is_rejected() -> None:
	"""A CNPJ with wrong check digits is rejected."""
	with pytest.raises(ValidationError):
		_row(cnpj_fdo="11222333000182")


def test_export_with_output_path_returns_none(tmp_path: Path) -> None:
	"""With an output path, export writes the file and returns None.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest-provided throwaway directory for the output file.
	"""
	out = tmp_path / "perfil_739.xml"

	assert PerfilMensal739().export(_document(_row()), str(out)) is None


def test_export_writes_file_in_windows_1252(tmp_path: Path) -> None:
	"""The file holds windows-1252 bytes, not UTF-8.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest-provided throwaway directory for the output file.
	"""
	out = tmp_path / "perfil_739.xml"
	PerfilMensal739().export(_document(_row(res_delib="Ação aprovada")), str(out))

	assert "Ação aprovada".encode("windows-1252") in out.read_bytes()


def test_export_rejects_wrong_argument_type() -> None:
	"""The TypeChecker metaclass rejects a mistyped argument at call time."""
	with pytest.raises(TypeError):
		PerfilMensal739().export("not a document")
