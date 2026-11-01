"""Pydantic models for the CVM Monthly Profile (Perfil Mensal) V3 XML standard.

V3 (https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfilV3.asp) shares
the V4 tag order, decimal scales and cardinalities exactly, so everything is reused from
:mod:`filings_cvm._internal.config.schemas.perfil_mensal`. The one structural delta,
measured against both pages, is ``DISTR_PATRIM``: V3 marks the whole block (and each of
its 16 ``PR_*`` tags) as mandatory, while V4 makes it optional for classes with
subclasses.
"""

from pydantic import BaseModel, field_validator

from filings_cvm._internal.config.schemas.perfil_mensal import (
	DocumentHeader,
	PatrimonyDistribution,
	PercentField,
	PerfilMensalDocument,
	PerfilMensalRow,
)


# ``BaseModel`` is repeated in each base list so bin/check_schemas.py (which only sees
# in-file bases) accepts the subclasses; it is a no-op for the MRO.
class PatrimonyDistributionV3(PatrimonyDistribution, BaseModel):
	"""DISTR_PATRIM - patrimony percentage by client type (all 16 tags mandatory in V3)."""

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


class PerfilMensalV3Row(PerfilMensalRow, BaseModel):
	"""ROW_PERFIL (V3) - same as V4 but with a mandatory DISTR_PATRIM block."""

	distr_patrim: PatrimonyDistributionV3


class PerfilMensalV3Document(PerfilMensalDocument, BaseModel):
	"""DOC_ARQ (V3) - complete CVM Monthly Profile V3 XML document."""

	header: DocumentHeader
	# The narrowed element type is deliberate, so the V4 serializer still accepts V3 documents.
	rows: list[PerfilMensalV3Row]  # type: ignore[assignment]

	@field_validator("header")
	@classmethod
	def _pin_header_versao(cls, v: DocumentHeader) -> DocumentHeader:
		"""Pin the header version to 3.0, leaving the shared V4 default untouched.

		Parameters
		----------
		v : DocumentHeader
			Header as supplied; ``versao`` is the V4 default ``4.0`` unless set.

		Returns
		-------
		DocumentHeader
			A copy of the header with ``versao`` normalised to ``3.0``.

		Raises
		------
		ValueError
			If ``versao`` is neither ``3.0`` nor the shared ``4.0`` default.
		"""
		if v.versao not in {"3.0", DocumentHeader.model_fields["versao"].default}:
			raise ValueError("a V3 document header must carry versao 3.0.")
		return v.model_copy(update={"versao": "3.0"})


__all__ = [
	"PatrimonyDistributionV3",
	"PerfilMensalV3Document",
	"PerfilMensalV3Row",
]
