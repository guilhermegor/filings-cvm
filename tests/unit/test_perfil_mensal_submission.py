"""Unit tests for the Perfil Mensal submission writer.

Cover the money/validation paths: XML structure, comma-decimal formatting,
ROUND_DOWN truncation, and check-digit CNPJ rejection.
"""

from pathlib import Path

from pydantic import ValidationError
import pytest

from filings_cvm.submission import (
	ClientCount,
	DocumentHeader,
	NominalRiskBlock,
	NominalRiskFactor,
	OtcOperation,
	PatrimonyDistribution,
	PerfilMensal,
	PerfilMensalDocument,
	PerfilMensalRow,
	PerformanceFeeDetails,
	PrimitiveRiskFactor,
	PrivateCreditIssuer,
	VarOutros,
	VarPercValCota,
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


def test_export_minimal_document_renders_expected_structure() -> None:
	"""Emit the CVM document envelope, the row block, and the fund CNPJ."""
	xml = PerfilMensal().export(_document(_minimal_row()))

	assert xml is not None
	assert "<DOC_ARQ" in xml
	assert "<CAB_INFORM>" in xml
	assert "<ROW_PERFIL>" in xml
	assert f"<CNPJ_FDO>{VALID_CNPJ}</CNPJ_FDO>" in xml
	# Monetary fields render with a comma decimal separator at two places.
	assert "<TOTAL_RECURS_BR>0,00</TOTAL_RECURS_BR>" in xml


def test_export_truncates_excess_precision_round_down() -> None:
	"""A value with excess precision is truncated toward zero, never rounded up."""
	xml = PerfilMensal().export(_document(_minimal_row(total_recurs_br="10.999")))

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


def _full_row() -> PerfilMensalRow:
	"""Build a row populating every optional block, exercising all writer branches."""
	return PerfilMensalRow(
		cnpj_fdo=VALID_CNPJ,
		nr_client=_zero_client_count(),
		distr_patrim=PatrimonyDistribution(pr_pf_priv_bank="10.5", pr_pf_varj="20.0"),
		resm_teor_vt_profrd="voto resumido <ok>",
		just_sum_vt_profrd="justificativa",
		var_perc_pl="1.2345",
		mod_var_utiliz="1",
		praz_med_cart_tit="12.3456",
		res_delib="resolucao",
		total_recurs_exter="0",
		total_recurs_br="0",
		variacao_perc_val_cota=VarPercValCota(
			val_percent="5.5",
			lista_fator_primit_risco=[
				PrimitiveRiskFactor(nome_fator_primit_risco="IBOVESPA", cen_util="teste"),
			],
		),
		var_diar_perc_cota_fdo_pior_cen_estress="1.1",
		var_diar_perc_patrim_fdo_var_n_taxa_anual="2.2",
		var_diar_perc_patrim_fdo_var_n_taxa_cambio="3.3",
		var_patrim_fdo_n_preco_acoes="4.4",
		variacao_diar_perc_patrim_fdo_var_n_outros=VarOutros(
			fator_risco_outros="fator", val_percent_outros="6.6"
		),
		valor_noc_tot_contrat_deriv_mant_fdo=NominalRiskBlock(
			val_colateral="7.7",
			lista_fator_risco_noc=[
				NominalRiskFactor(
					nome_fator_noc="DOLAR",
					val_fator_risco_noc_long=1,
					val_fator_risco_noc_short=2,
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
		tot_ativos_p_relac="0",
		lista_emissores_tit_cred_priv=[
			PrivateCreditIssuer(
				tp_pessoa_emissor="PJ",
				nr_pf_pj_emissor=VALID_CNPJ,
				parte_relacionada="S",
				valor_parte="9.9",
			),
		],
		tot_ativos_cred_priv="0",
		ved_regul_cobr_taxa_perform="S",
		resp_ved_regul_cobr_taxa_perform=PerformanceFeeDetails(
			data_cota_fundo="01/01/2025", val_cota_fundo="1.23456"
		),
		montante_distrib="100.50",
		inf_compl_perfil="info complementar",
	)


def test_export_full_row_renders_all_optional_blocks() -> None:
	"""A fully populated row emits every optional block with escaping and comma decimals."""
	xml = PerfilMensal().export(_document(_full_row()))

	assert xml is not None
	assert "<DISTR_PATRIM>" in xml
	assert "<VARIACAO_PERC_VAL_COTA>" in xml
	assert "<VALOR_NOC_TOT_CONTRAT_DERIV_MANT_FDO>" in xml
	assert "<LISTA_OPER_CURS_MERC_BALCAO>" in xml
	assert "<LISTA_EMISSORES_TIT_CRED_PRIV>" in xml
	assert "<RESP_VED_REGUL_COBR_TAXA_PERFORM>" in xml
	assert "<MONTANTE_DISTRIB>100,50</MONTANTE_DISTRIB>" in xml
	# The '<' in the vote summary is XML-escaped, never emitted raw.
	assert "voto resumido &lt;ok&gt;" in xml


def test_export_writes_file_in_windows_1252(tmp_path: Path) -> None:
	"""With an output path, export returns None and writes a windows-1252 file.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest-provided throwaway directory for the output file.
	"""
	out = tmp_path / "perfil_mensal.xml"
	result = PerfilMensal().export(_document(_minimal_row()), output_path=str(out))

	assert result is None
	assert f"<CNPJ_FDO>{VALID_CNPJ}</CNPJ_FDO>" in out.read_text(encoding="windows-1252")


def test_export_rejects_wrong_argument_type() -> None:
	"""The TypeChecker metaclass rejects a mistyped argument at call time."""
	with pytest.raises(TypeError):
		PerfilMensal().export("not a document")
