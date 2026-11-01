"""Unit tests for the Perfil Mensal V3 submission writer.

The expected tag order and decimal scales are pinned to the CVM page
``PadraoXMLPerfilV3.asp`` (XML sample), not to the V4 writer.
"""

import re

from pydantic import ValidationError
import pytest

from filings_cvm.submission import (
	ClientCount,
	DocumentHeader,
	PatrimonyDistributionV3,
	PerfilMensalV3,
	PerfilMensalV3Document,
	PerfilMensalV3Row,
)


VALID_CNPJ = "11222333000181"

# First-occurrence tag order of the ROW_PERFIL sample on the V3 page (80 tags).
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
	"MONTANTE_DISTRIB",
	"INF_COMPL_PERFIL",
)

_PR_FIELDS = tuple(f for f in PatrimonyDistributionV3.model_fields)


def _row(**distr_overrides: str) -> PerfilMensalV3Row:
	"""Build a minimal V3 row; ``distr_overrides`` replace PR_* values."""
	zero_clients = {f: 0 for f in ClientCount.model_fields}
	distr = dict.fromkeys(_PR_FIELDS, "0") | distr_overrides
	return PerfilMensalV3Row(
		cnpj_fdo=VALID_CNPJ,
		nr_client=ClientCount(**zero_clients),
		distr_patrim=PatrimonyDistributionV3(**distr),
		total_recurs_exter="0",
		total_recurs_br="0",
		tot_ativos_p_relac="0",
		tot_ativos_cred_priv="0",
	)


def _xml(row: PerfilMensalV3Row) -> str:
	"""Serialize a one-row V3 document."""
	header = DocumentHeader(dt_compt="01/2025", dt_gerac_arq="15/01/2025")
	xml = PerfilMensalV3().export(PerfilMensalV3Document(header=header, rows=[row]))
	assert xml is not None
	return xml


def test_export_declaration_is_windows_1252() -> None:
	"""The XML declaration names windows-1252, as the page's sample does."""
	xml = _xml(_row())

	assert xml.startswith('<?xml version="1.0" encoding="windows-1252"?>')


def test_export_versao_is_three() -> None:
	"""VERSAO is 3.0, never the V4 value."""
	assert "<VERSAO>3.0</VERSAO>" in _xml(_row())


def test_export_cod_doc_is_forty() -> None:
	"""COD_DOC stays 40 with no leading zeros."""
	assert "<COD_DOC>40</COD_DOC>" in _xml(_row())


def test_export_tag_order_follows_the_v3_page() -> None:
	"""Emitted ROW_PERFIL tags are an ordered subsequence of the page's sample."""
	body = _xml(_row()).split("<ROW_PERFIL>")[1]
	emitted = re.findall(r"<([A-Z_0-9]+)>", body)
	order = iter(PAGE_TAG_ORDER)

	assert all(tag in order for tag in emitted)


def test_export_distr_patrim_emits_all_sixteen_tags_one_decimal() -> None:
	"""All 16 PR_* tags are emitted with one decimal and a comma separator."""
	xml = _xml(_row(pr_pf_varj="12.34"))

	assert xml.count("<PR_") == 16
	assert "<PR_PF_VARJ>12,3</PR_PF_VARJ>" in xml


def test_row_without_distr_patrim_is_rejected() -> None:
	"""DISTR_PATRIM is mandatory in V3 (optional in V4)."""
	with pytest.raises(ValidationError):
		PerfilMensalV3Row(
			cnpj_fdo=VALID_CNPJ,
			nr_client=ClientCount(**{f: 0 for f in ClientCount.model_fields}),
			total_recurs_exter="0",
			total_recurs_br="0",
			tot_ativos_p_relac="0",
			tot_ativos_cred_priv="0",
		)


def test_distr_patrim_missing_one_tag_is_rejected() -> None:
	"""Each of the 16 PR_* tags is individually mandatory."""
	fields = dict.fromkeys(_PR_FIELDS[1:], "0")

	with pytest.raises(ValidationError):
		PatrimonyDistributionV3(**fields)


def test_distr_patrim_above_hundred_is_rejected() -> None:
	"""PR_* values are capped at 100."""
	with pytest.raises(ValidationError):
		_row(pr_pf_varj="100.1")


def test_row_invalid_cnpj_is_rejected() -> None:
	"""A CNPJ with wrong check digits is rejected."""
	with pytest.raises(ValidationError):
		PerfilMensalV3Row.model_validate({**_row().model_dump(), "cnpj_fdo": "11222333000182"})


def test_v3_writer_is_not_a_v4_writer() -> None:
	"""The V3 writer must not masquerade as the V4 one (its export signature differs)."""
	from filings_cvm.submission import PerfilMensal

	assert not isinstance(PerfilMensalV3(), PerfilMensal)


def test_v3_document_header_versao_is_pinned() -> None:
	"""A V3 document normalises the shared V4 default to 3.0 and keeps V4 untouched."""
	header = DocumentHeader(dt_compt="10/2015", dt_gerac_arq="15/11/2015")
	doc = PerfilMensalV3Document(header=header, rows=[_row()])

	assert doc.header.versao == "3.0"
	assert header.versao == "4.0"


def test_v3_document_header_rejects_foreign_versao() -> None:
	"""A header claiming some other version is refused, not silently rewritten."""
	import pytest

	header = DocumentHeader(versao="9.9", dt_compt="10/2015", dt_gerac_arq="15/11/2015")

	with pytest.raises(ValueError, match="versao 3.0"):
		PerfilMensalV3Document(header=header, rows=[_row()])
