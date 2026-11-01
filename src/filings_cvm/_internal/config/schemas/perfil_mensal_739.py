"""Pydantic models for the CVM Monthly Profile (Perfil Mensal) ICVM 739 XML standard.

The 739 standard
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfil739.asp, in force
from 01/07/2012) shares the V3/V4 tag order and every other block with
:mod:`filings_cvm._internal.config.schemas.perfil_mensal`, which is reused here. The
deltas, measured against the V3 and V4 pages, are:

* ``DISTR_PATRIM`` and its 16 ``PR_*`` tags are mandatory (as in V3);
* the sensitivity tags ``VAR_DIAR_PERC_PATRIM_FDO_VAR_N_TAXA_ANUAL``,
  ``VAR_DIAR_PERC_PATRIM_FDO_VAR_N_TAXA_CAMBIO``, ``VAR_PATRIM_FDO_N_PRECO_ACOES`` and
  ``VAL_PERCENT_OUTROS`` carry two decimal places (V3/V4: four);
* ``MONTANTE_DISTRIB`` and ``INF_COMPL_PERFIL`` do not exist yet.
"""

from pydantic import BaseModel, Field

from filings_cvm._internal.config.schemas.perfil_mensal import (
	DocumentHeader,
	PatrimonyDistribution,
	PercentField,
	PerfilMensalDocument,
	PerfilMensalRow,
	TwoDecimalField,
	VarOutros,
)


# ``BaseModel`` is repeated in each base list so bin/check_schemas.py (which only sees
# in-file bases) accepts the subclasses; it is a no-op for the MRO.
class PatrimonyDistribution739(PatrimonyDistribution, BaseModel):
	"""DISTR_PATRIM - patrimony percentage by client type (all 16 tags mandatory in 739)."""

	pr_pf_priv_bank: PercentField
	pr_pf_varj: PercentField
	pr_pj_n_financ_priv_bank: PercentField
	pr_pj_n_financ_varj: PercentField
	pr_bnc_comerc: PercentField
	pr_pj_corr_dist: PercentField
	pr_pj_outr_financ: PercentField
	pr_inv_n_res: PercentField
	pr_ent_ab_prev_compl: PercentField
	pr_ent_fc_prev_compl: PercentField
	pr_reg_prev_serv_pub: PercentField
	pr_soc_seg_reseg: PercentField
	pr_soc_captlz_arrendm_merc: PercentField
	pr_fdos_club_inv: PercentField
	pr_cotst_distr_fdo: PercentField
	pr_outros_n_relac: PercentField


class VarOutros739(VarOutros, BaseModel):
	"""VARIACAO_DIAR_PERC_PATRIM_FDO_VAR_N_OUTROS - ``VAL_PERCENT_OUTROS`` has 2 decimals."""

	val_percent_outros: TwoDecimalField


class PerfilMensal739Row(PerfilMensalRow, BaseModel):
	"""ROW_PERFIL (739) - V4 row with the 739 deltas applied."""

	distr_patrim: PatrimonyDistribution739
	var_diar_perc_patrim_fdo_var_n_taxa_anual: TwoDecimalField | None = None
	var_diar_perc_patrim_fdo_var_n_taxa_cambio: TwoDecimalField | None = None
	var_patrim_fdo_n_preco_acoes: TwoDecimalField | None = None
	variacao_diar_perc_patrim_fdo_var_n_outros: VarOutros739 | None = None
	# Typed None-only so a tag the 739 page lacks is rejected, not serialised.
	montante_distrib: None = Field(default=None, exclude=True)
	inf_compl_perfil: None = Field(default=None, exclude=True)


class PerfilMensal739Document(PerfilMensalDocument, BaseModel):
	"""DOC_ARQ (739) - complete CVM Monthly Profile ICVM 739 XML document."""

	header: DocumentHeader
	rows: list[PerfilMensal739Row]  # type: ignore[assignment]


__all__ = [
	"PatrimonyDistribution739",
	"PerfilMensal739Document",
	"PerfilMensal739Row",
	"VarOutros739",
]
