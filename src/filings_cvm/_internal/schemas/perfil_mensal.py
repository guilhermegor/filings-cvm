"""Pydantic models for the CVM Monthly Profile (Perfil Mensal) XML standard.

This is the *shared schema* — the direction-neutral contract for one CVM XML
standard. The ``submission`` section builds these models and serialises them to
XML; the future ``ingestion`` section will parse CVM XML back into them. It ships
inside the wheel under ``_internal`` but is **not** part of the public API on its
own — the ``submission``/``ingestion`` packages re-export the names consumers need.

Per-field decimal scales mirror the CVM XML standard ``PadrãoXMLPerfil`` (V4,
https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfilV4.asp).
Values carrying more decimal places than the standard permits are truncated toward
zero (``ROUND_DOWN``) instead of rounded, so a reported value is never inflated
past what the standard allows.

CNPJ/CPF fields are validated with this library's own check-digit validators
(``_internal.utils.br_identifiers``) and stored in bare, unmasked form — the shape
CVM expects in the XML — rather than a format-only regex.
"""

from decimal import Decimal
import re
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, Field, ValidationInfo, field_validator

from filings_cvm._internal.schemas._fields import (
	truncate_to_scale,
	validate_person_doc,
	validated_cnpj,
)


# Decimal field types with the scale pinned to the CVM Perfil standard.
# Fields where the standard states only the number of decimal places.
OneDecimalField = Annotated[
	Decimal, BeforeValidator(truncate_to_scale(1)), Field(decimal_places=1)
]
TwoDecimalField = Annotated[
	Decimal, BeforeValidator(truncate_to_scale(2)), Field(decimal_places=2)
]
FiveDecimalField = Annotated[
	Decimal, BeforeValidator(truncate_to_scale(5)), Field(decimal_places=5)
]

# Fields where the standard also bounds the integer-digit count.
# VAR_PERC_PL: "valor com até 10 casas inteiras e 4 decimais".
VarPercentPlField = Annotated[
	Decimal, BeforeValidator(truncate_to_scale(4)), Field(max_digits=14, decimal_places=4)
]
# PRAZ_MED_CART_TIT: "valor com até 4 casas inteiras e 4 decimais".
AvgTermField = Annotated[
	Decimal, BeforeValidator(truncate_to_scale(4)), Field(max_digits=8, decimal_places=4)
]
# PR_* patrimony distribution: "até 3 casas inteiras e 1 decimal. Valor máximo 100".
PercentField = Annotated[
	Decimal,
	BeforeValidator(truncate_to_scale(1)),
	Field(ge=Decimal("0"), le=Decimal("100"), max_digits=4, decimal_places=1),
]


class DocumentHeader(BaseModel):
	"""CAB_INFORM - document-level header block."""

	cod_doc: int = 40
	dt_compt: str
	dt_gerac_arq: str
	versao: str = "4.0"

	@field_validator("dt_compt")
	@classmethod
	def _check_dt_compt(cls, v: str) -> str:
		"""Validate dt_compt format.

		Parameters
		----------
		v : str
			Value to validate.

		Returns
		-------
		str
			Validated value.

		Raises
		------
		ValueError
			If value does not follow MM/AAAA format.
		"""
		if not re.match(r"^\d{2}/\d{4}$", v):
			raise ValueError("dt_compt must follow MM/AAAA format.")
		return v

	@field_validator("dt_gerac_arq")
	@classmethod
	def _check_dt_gerac_arq(cls, v: str) -> str:
		"""Validate dt_gerac_arq format.

		Parameters
		----------
		v : str
			Value to validate.

		Returns
		-------
		str
			Validated value.

		Raises
		------
		ValueError
			If value does not follow DD/MM/AAAA format.
		"""
		if not re.match(r"^\d{2}/\d{2}/\d{4}$", v):
			raise ValueError("dt_gerac_arq must follow DD/MM/AAAA format.")
		return v


class ClientCount(BaseModel):
	"""NR_CLIENT - count of clients by investor type (all mandatory, non-negative)."""

	nr_pf_priv_bank: int = Field(ge=0)
	nr_pf_varj: int = Field(ge=0)
	nr_pj_n_financ_priv_bank: int = Field(ge=0)
	nr_pj_n_financ_varj: int = Field(ge=0)
	nr_bnc_comerc: int = Field(ge=0)
	nr_pj_corr_dist: int = Field(ge=0)
	nr_pj_outr_financ: int = Field(ge=0)
	nr_inv_n_res: int = Field(ge=0)
	nr_ent_ab_prev_compl: int = Field(ge=0)
	nr_ent_fc_prev_compl: int = Field(ge=0)
	nr_reg_prev_serv_pub: int = Field(ge=0)
	nr_soc_seg_reseg: int = Field(ge=0)
	nr_soc_captlz_arrendm_merc: int = Field(ge=0)
	nr_fdos_club_inv: int = Field(ge=0)
	nr_cotst_distr_fdo: int = Field(ge=0)
	nr_outros_n_relac: int = Field(ge=0)


class PatrimonyDistribution(BaseModel):
	"""DISTR_PATRIM - patrimony percentage by client type (entire block is optional)."""

	pr_pf_priv_bank: PercentField | None = None
	pr_pf_varj: PercentField | None = None
	pr_pj_n_financ_priv_bank: PercentField | None = None
	pr_pj_n_financ_varj: PercentField | None = None
	pr_bnc_comerc: PercentField | None = None
	pr_pj_corr_dist: PercentField | None = None
	pr_pj_outr_financ: PercentField | None = None
	pr_inv_n_res: PercentField | None = None
	pr_ent_ab_prev_compl: PercentField | None = None
	pr_ent_fc_prev_compl: PercentField | None = None
	pr_reg_prev_serv_pub: PercentField | None = None
	pr_soc_seg_reseg: PercentField | None = None
	pr_soc_captlz_arrendm_merc: PercentField | None = None
	pr_fdos_club_inv: PercentField | None = None
	pr_cotst_distr_fdo: PercentField | None = None
	pr_outros_n_relac: PercentField | None = None


class PrimitiveRiskFactor(BaseModel):
	"""FATOR_PRIMIT_RISCO - one BM&FBOVESPA primitive risk factor entry."""

	nome_fator_primit_risco: Literal["IBOVESPA", "JUROS-PRE", "CUPOM CAMBIAL", "DOLAR", "OUTROS"]
	cen_util: str = Field(max_length=150)


class VarPercValCota(BaseModel):
	"""VARIACAO_PERC_VAL_COTA - stress scenario block with primitive risk factors."""

	val_percent: TwoDecimalField
	lista_fator_primit_risco: list[PrimitiveRiskFactor] = Field(max_length=5)


class VarOutros(BaseModel):
	"""VARIACAO_DIAR_PERC_PATRIM_FDO_VAR_N_OUTROS - sensitivity to a non-standard risk factor."""

	fator_risco_outros: str = Field(max_length=400)
	val_percent_outros: TwoDecimalField


class NominalRiskFactor(BaseModel):
	"""FATOR_RISCO_NOC - one notional derivatives risk factor (long and short legs)."""

	nome_fator_noc: Literal["IBOVESPA", "JUROS-PRE", "CUPOM CAMBIAL", "DOLAR", "OUTROS"]
	val_fator_risco_noc_long: int = Field(ge=0)
	val_fator_risco_noc_short: int = Field(ge=0)


class NominalRiskBlock(BaseModel):
	"""VALOR_NOC_TOT_CONTRAT_DERIV_MANT_FDO - OTC derivatives notional exposure block."""

	val_colateral: TwoDecimalField
	lista_fator_risco_noc: list[NominalRiskFactor] = Field(max_length=5)


class OtcOperation(BaseModel):
	"""OPER_CURS_MERC_BALCAO - one top-3 OTC counterparty without central clearing."""

	tp_pessoa: Literal["PF", "PJ"]
	nr_pf_pj_comitente: str
	parte_relacionada: Literal["S", "N"]
	valor_parte: OneDecimalField

	@field_validator("nr_pf_pj_comitente")
	@classmethod
	def _check_comitente_doc(cls, v: str, info: ValidationInfo) -> str:
		"""Validate and normalise the counterparty document against its person type.

		Parameters
		----------
		v : str
			The counterparty document (CPF or CNPJ) in any shape.
		info : ValidationInfo
			Validation context; ``tp_pessoa`` (declared first) is read from it.

		Returns
		-------
		str
			The document in bare, unmasked form.

		Raises
		------
		ValueError
			If the document is not a valid CPF (PF) or CNPJ (PJ).
		"""
		return validate_person_doc(info.data.get("tp_pessoa", ""), v)


class PrivateCreditIssuer(BaseModel):
	"""EMISSORES_TIT_CRED_PRIV - one top-3 private credit issuer held by the fund class."""

	tp_pessoa_emissor: Literal["PF", "PJ"]
	nr_pf_pj_emissor: str
	parte_relacionada: Literal["S", "N"]
	valor_parte: OneDecimalField

	@field_validator("nr_pf_pj_emissor")
	@classmethod
	def _check_emissor_doc(cls, v: str, info: ValidationInfo) -> str:
		"""Validate and normalise the issuer document against its person type.

		Parameters
		----------
		v : str
			The issuer document (CPF or CNPJ) in any shape.
		info : ValidationInfo
			Validation context; ``tp_pessoa_emissor`` (declared first) is read from it.

		Returns
		-------
		str
			The document in bare, unmasked form.

		Raises
		------
		ValueError
			If the document is not a valid CPF (PF) or CNPJ (PJ).
		"""
		return validate_person_doc(info.data.get("tp_pessoa_emissor", ""), v)


class PerformanceFeeDetails(BaseModel):
	"""RESP_VED_REGUL_COBR_TAXA_PERFORM - date and NAV of the last performance fee charge."""

	data_cota_fundo: str
	val_cota_fundo: FiveDecimalField

	@field_validator("data_cota_fundo")
	@classmethod
	def _check_date(cls, v: str) -> str:
		"""Validate date format.

		Parameters
		----------
		v : str
			Value to validate.

		Returns
		-------
		str
			Validated value.

		Raises
		------
		ValueError
			If value does not follow DD/MM/AAAA format.
		"""
		if not re.match(r"^\d{2}/\d{2}/\d{4}$", v):
			raise ValueError("data_cota_fundo must follow DD/MM/AAAA format.")
		return v


class PerfilMensalRow(BaseModel):
	"""ROW_PERFIL - one fund-class monthly profile entry."""

	cnpj_fdo: str
	nr_client: ClientCount
	distr_patrim: PatrimonyDistribution | None = None
	resm_teor_vt_profrd: str | None = Field(default=None, max_length=4000)
	just_sum_vt_profrd: str | None = Field(default=None, max_length=4000)
	var_perc_pl: VarPercentPlField | None = None
	mod_var_utiliz: Literal["1", "2", "3"] | None = None
	praz_med_cart_tit: AvgTermField | None = None
	res_delib: str | None = Field(default=None, max_length=4000)
	total_recurs_exter: TwoDecimalField
	total_recurs_br: TwoDecimalField
	variacao_perc_val_cota: VarPercValCota | None = None
	var_diar_perc_cota_fdo_pior_cen_estress: TwoDecimalField | None = None
	var_diar_perc_patrim_fdo_var_n_taxa_anual: TwoDecimalField | None = None
	var_diar_perc_patrim_fdo_var_n_taxa_cambio: TwoDecimalField | None = None
	var_patrim_fdo_n_preco_acoes: TwoDecimalField | None = None
	variacao_diar_perc_patrim_fdo_var_n_outros: VarOutros | None = None
	valor_noc_tot_contrat_deriv_mant_fdo: NominalRiskBlock | None = None
	lista_oper_curs_merc_balcao: list[OtcOperation] | None = Field(default=None, max_length=3)
	tot_ativos_p_relac: OneDecimalField
	lista_emissores_tit_cred_priv: list[PrivateCreditIssuer] | None = Field(
		default=None, max_length=3
	)
	tot_ativos_cred_priv: OneDecimalField
	ved_regul_cobr_taxa_perform: Literal["S", "N"] | None = None
	resp_ved_regul_cobr_taxa_perform: PerformanceFeeDetails | None = None
	# MONTANTE_DISTRIB is absent from older Perfil versions; 2dp is inferred from its
	# monetary nature and the serializer default, pending confirmation against the spec.
	montante_distrib: TwoDecimalField | None = None
	inf_compl_perfil: str | None = Field(default=None, max_length=500)

	@field_validator("cnpj_fdo")
	@classmethod
	def _check_cnpj(cls, v: str) -> str:
		"""Validate and normalise the fund-class CNPJ (check-digit aware).

		Parameters
		----------
		v : str
			Value to validate.

		Returns
		-------
		str
			The unmasked (bare) CNPJ.

		Raises
		------
		ValueError
			If value is not a valid CNPJ.
		"""
		return validated_cnpj(v)


class PerfilMensalDocument(BaseModel):
	"""DOC_ARQ - complete CVM Monthly Profile XML document."""

	header: DocumentHeader
	rows: list[PerfilMensalRow]
