"""Pydantic models for the CVM Monthly Profile (Perfil Mensal) original XML standard.

Direction-neutral schema for ``PadraoXMLPerfil.asp``
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfil.asp), the first layout of
the standard (``COD_DOC`` 40, Instrução CVM 409). It is **not** a variant of V4: measured against
the V4 page, the original has a 14-tag ``NR_CLIENT`` and ``DISTR_PATRIM`` (V4 has 16; the
pension-fund tags are one merged ``*_ENT_AB_FC_PREV_COMPL`` and there is no
``*_REG_PREV_SERV_PUB``), ``*_NAC`` suffixes on three tags, a different row body
(``PERC_PL_MAIOR_COTST``, ``PRINC_FAT_RISC``, ``DESC_PRINC_ATV_OPER_RISC``,
``PR_PRINC_ATV_OPER_RISC``, ``NR_DIAS_NEGOC``, ``PERC_PL_CONV_CAIXA``) and **no** ``VERSAO`` tag in
the header. Only the decimal field types, which are the same scales, are imported from the V4
schema; every block is declared here from the page's own sample.

Values carrying more decimal places than the page permits are truncated toward zero
(``ROUND_DOWN``), never rounded. The fund CNPJ is check-digit validated and stored bare.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import (
	AfterValidator,
	BaseModel,
	BeforeValidator,
	ConfigDict,
	Field,
	StringConstraints,
	model_validator,
)

from filings_cvm._internal.config.schemas._fields import truncate_to_scale, validated_cnpj
from filings_cvm._internal.config.schemas.perfil_mensal import PercentField
from filings_cvm._internal.utils.xml_fields import (
	check_br_date,
	check_cnpj_shape,
	check_month_year,
	check_xml_text,
)


# The page states "até N casas inteiras e M decimais". ``Field(max_digits=...)`` cannot say that:
# pydantic counts digits after dropping trailing zeros and has no separate integer bound, so
# ``12345.0`` passes ``max_digits=8``. A magnitude bound (|x| < 10**N) states it exactly.
# PR_PRINC_ATV_OPER_RISC: 7 integer digits, 1 decimal.
_RiskAssetPercentField = Annotated[
	Decimal,
	BeforeValidator(truncate_to_scale(1)),
	Field(gt=Decimal("-1e7"), lt=Decimal("1e7"), decimal_places=1),
]
# VAR_PERC_PL: 10 integer digits, 4 decimals.
_VarPercentPlField = Annotated[
	Decimal,
	BeforeValidator(truncate_to_scale(4)),
	Field(gt=Decimal("-1e10"), lt=Decimal("1e10"), decimal_places=4),
]
# ATIV_50_PERC, ATIV_100_PERC and PRAZ_MED_CART_TIT: 4 integer digits, 4 decimals.
_TermField = Annotated[
	Decimal,
	BeforeValidator(truncate_to_scale(4)),
	Field(gt=Decimal("-1e4"), lt=Decimal("1e4"), decimal_places=4),
]

_CompetenceField = Annotated[str, AfterValidator(check_month_year)]
_DateField = Annotated[str, AfterValidator(check_br_date)]

_VOTE_TEXT_MAX = 4000
_RISK_TEXT_MAX = 400
_XML_TEXT = AfterValidator(check_xml_text)
_Text400 = Annotated[str, StringConstraints(max_length=_RISK_TEXT_MAX), _XML_TEXT]
_Text4000 = Annotated[str, StringConstraints(max_length=_VOTE_TEXT_MAX), _XML_TEXT]

_CountField = Annotated[int, Field(ge=0)]
_CnpjField = Annotated[str, AfterValidator(check_cnpj_shape), AfterValidator(validated_cnpj)]


class _PerfilMensalOriginalBlock(BaseModel):
	"""Base of the original-layout blocks: closed (no unknown fields) and immutable."""

	model_config = ConfigDict(extra="forbid", frozen=True)


class PerfilMensalOriginalHeader(_PerfilMensalOriginalBlock):
	"""CAB_INFORM — COD_DOC, DT_COMPT and DT_GERAC_ARQ (the original has no VERSAO)."""

	cod_doc: Literal[40] = 40
	dt_compt: _CompetenceField
	dt_gerac_arq: _DateField


class PerfilMensalOriginalClientCount(_PerfilMensalOriginalBlock):
	"""NR_CLIENT — number of investors by type, 14 mandatory non-negative integers."""

	nr_pf_priv_bank: _CountField
	nr_pf_varj: _CountField
	nr_pj_n_financ_priv_bank: _CountField
	nr_pj_n_financ_varj: _CountField
	nr_bnc_comerc_nac: _CountField
	nr_pj_corr_dist_nac: _CountField
	nr_pj_outr_financ_nac: _CountField
	nr_inv_n_res: _CountField
	nr_ent_ab_fc_prev_compl: _CountField
	nr_soc_seg_reseg: _CountField
	nr_soc_captlz_arrendm_merc: _CountField
	nr_fdos_club_inv: _CountField
	nr_cotst_distr_fdo: _CountField
	nr_outros_n_relac: _CountField


class PerfilMensalOriginalPatrimonyDistribution(_PerfilMensalOriginalBlock):
	"""DISTR_PATRIM — percentage of the net worth by investor type, 14 mandatory tags."""

	pr_pf_priv_bank: PercentField
	pr_pf_varj: PercentField
	pr_pj_n_financ_priv_bank: PercentField
	pr_pj_n_financ_varj: PercentField
	pr_bnc_comerc_nac: PercentField
	pr_pj_corr_dist_nac: PercentField
	pr_pj_outr_financ_nac: PercentField
	pr_inv_n_res: PercentField
	pr_ent_ab_fc_prev_compl: PercentField
	pr_soc_seg_reseg: PercentField
	pr_soc_captlz_arrendm_merc: PercentField
	pr_fdos_club_inv: PercentField
	pr_cotst_distr_fdo: PercentField
	pr_outros_n_relac: PercentField


class PerfilMensalOriginalTradingDays(_PerfilMensalOriginalBlock):
	"""NR_DIAS_NEGOC — optional block: days to sell 50% and 100% of the assets, plus liquidity."""

	ativ_50_perc: _TermField | None = None
	ativ_100_perc: _TermField | None = None
	apres_liqdz: Literal["S", "N"] | None = None

	@model_validator(mode="after")
	def _check_pair(self) -> PerfilMensalOriginalTradingDays:
		"""Apply the page's pairing rule for the 50% and 100% tags.

		Returns
		-------
		PerfilMensalOriginalTradingDays
			The validated block.

		Raises
		------
		ValueError
			If only one of ATIV_50_PERC / ATIV_100_PERC is given.
		"""
		if (self.ativ_50_perc is None) != (self.ativ_100_perc is None):
			raise ValueError("ativ_50_perc and ativ_100_perc must be given together")
		return self

	@model_validator(mode="after")
	def _check_not_empty(self) -> PerfilMensalOriginalTradingDays:
		"""Reject an empty block: the page makes the whole block optional, so omit it.

		Returns
		-------
		PerfilMensalOriginalTradingDays
			The validated block.

		Raises
		------
		ValueError
			If no tag of the block is given.
		"""
		if self.ativ_50_perc is None and self.apres_liqdz is None:
			raise ValueError("an empty NR_DIAS_NEGOC block must be omitted")
		return self


class PerfilMensalOriginalRow(_PerfilMensalOriginalBlock):
	"""ROW_PERFIL — one fund's monthly profile, in the page's sample order."""

	cnpj_fdo: _CnpjField
	nr_client: PerfilMensalOriginalClientCount
	distr_patrim: PerfilMensalOriginalPatrimonyDistribution
	perc_pl_maior_cotst: PercentField
	resm_teor_vt_profrd: _Text4000 | None = None
	just_sum_vt_profrd: _Text4000 | None = None
	# Mandatory on the page except for fundos de investimento em cotas, which this model
	# cannot tell apart, so the FIC exception is the only one honoured.
	princ_fat_risc: _Text400 | None = None
	desc_princ_atv_oper_risc: _Text400 | None = None
	pr_princ_atv_oper_risc: _RiskAssetPercentField | None = None
	var_perc_pl: _VarPercentPlField | None = None
	mod_var_utiliz: Literal["1", "2", "3"] | None = None
	nr_dias_negoc: PerfilMensalOriginalTradingDays | None = None
	perc_pl_conv_caixa: PercentField | None = None
	praz_med_cart_tit: _TermField | None = None
	res_delib: _Text4000 | None = None


class PerfilMensalOriginalDocument(_PerfilMensalOriginalBlock):
	"""DOC_ARQ — a whole original-layout file: one competence, one or more funds."""

	header: PerfilMensalOriginalHeader
	rows: list[PerfilMensalOriginalRow] = Field(min_length=1)

	@model_validator(mode="after")
	def _check_unique_funds(self) -> PerfilMensalOriginalDocument:
		"""Reject the same fund twice in one file.

		Returns
		-------
		PerfilMensalOriginalDocument
			The validated document.

		Raises
		------
		ValueError
			If a CNPJ repeats.
		"""
		cnpjs = [row.cnpj_fdo for row in self.rows]
		if len(set(cnpjs)) != len(cnpjs):
			raise ValueError("a fund appears twice in the file")
		return self
