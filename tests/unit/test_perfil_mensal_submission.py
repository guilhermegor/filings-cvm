"""Unit tests for the Perfil Mensal submission writer.

Cover the money/validation paths: XML structure, comma-decimal formatting,
ROUND_DOWN truncation, and check-digit CNPJ rejection.
"""

from pydantic import ValidationError
import pytest

from filings_cvm.submission import (
	ClientCount,
	DocumentHeader,
	PerfilMensal,
	PerfilMensalDocument,
	PerfilMensalRow,
)


# A CNPJ whose check digits are valid under the repo's ASCII-48 mod-11 routine.
VALID_CNPJ = "11222333000181"


def _zero_client_count() -> ClientCount:
	"""Build a ClientCount with every mandatory investor-type count set to zero."""
	return ClientCount(
		nr_pf_priv_bank=0,
		nr_pf_varj=0,
		nr_pj_n_financ_priv_bank=0,
		nr_pj_n_financ_varj=0,
		nr_bnc_comerc=0,
		nr_pj_corr_dist=0,
		nr_pj_outr_financ=0,
		nr_inv_n_res=0,
		nr_ent_ab_prev_compl=0,
		nr_ent_fc_prev_compl=0,
		nr_reg_prev_serv_pub=0,
		nr_soc_seg_reseg=0,
		nr_soc_captlz_arrendm_merc=0,
		nr_fdos_club_inv=0,
		nr_cotst_distr_fdo=0,
		nr_outros_n_relac=0,
	)


def _minimal_row(total_recurs_br: str = "0") -> PerfilMensalRow:
	"""Build a minimal valid row exercising only the mandatory fields."""
	return PerfilMensalRow(
		cnpj_fdo=VALID_CNPJ,
		nr_client=_zero_client_count(),
		total_recurs_exter="0",
		total_recurs_br=total_recurs_br,
		tot_ativos_p_relac="0",
		tot_ativos_cred_priv="0",
	)


def _document(row: PerfilMensalRow) -> PerfilMensalDocument:
	"""Wrap a row in a document with a valid header."""
	header = DocumentHeader(dt_compt="01/2025", dt_gerac_arq="15/01/2025")
	return PerfilMensalDocument(header=header, rows=[row])


def test_to_xml_minimal_document_renders_expected_structure() -> None:
	"""to_xml emits the CVM document envelope, the row block, and the fund CNPJ."""
	xml = PerfilMensal().to_xml(_document(_minimal_row()))

	assert xml is not None
	assert "<DOC_ARQ" in xml
	assert "<CAB_INFORM>" in xml
	assert "<ROW_PERFIL>" in xml
	assert f"<CNPJ_FDO>{VALID_CNPJ}</CNPJ_FDO>" in xml
	# Monetary fields render with a comma decimal separator at two places.
	assert "<TOTAL_RECURS_BR>0,00</TOTAL_RECURS_BR>" in xml


def test_to_xml_truncates_excess_precision_round_down() -> None:
	"""A value with excess precision is truncated toward zero, never rounded up."""
	xml = PerfilMensal().to_xml(_document(_minimal_row(total_recurs_br="10.999")))

	assert xml is not None
	assert "<TOTAL_RECURS_BR>10,99</TOTAL_RECURS_BR>" in xml
	assert "11,00" not in xml


def test_invalid_cnpj_is_rejected() -> None:
	"""A CNPJ that fails the check digits raises a validation error."""
	with pytest.raises(ValidationError):
		_minimal_row_with_cnpj("12345678000100")


def _minimal_row_with_cnpj(cnpj: str) -> PerfilMensalRow:
	"""Build a minimal row overriding only the fund CNPJ (for the reject test)."""
	return PerfilMensalRow(
		cnpj_fdo=cnpj,
		nr_client=_zero_client_count(),
		total_recurs_exter="0",
		total_recurs_br="0",
		tot_ativos_p_relac="0",
		tot_ativos_cred_priv="0",
	)
