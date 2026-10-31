"""Pydantic models for the CVM Informe Sintético XML standards (four fund-type variants).

Direction-neutral schema for the four pages under
``https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/``:

====== =========================== ======== ===========================================
Prefix Page                        COD_DOC  Fund types
====== =========================== ======== ===========================================
Fcce   ``PadraoXMLSintFCCE.asp``   5        FCCE, FCCE-AI
Fitvm  ``PadraoXMLSintFITVM.asp``  7        FITVM, FMP-FGTS CL, FIIM
Fic    ``PadraoXMLSintFIC.asp``    8        FIC-FITVM
Outros ``PadraoXMLSintOutros.asp`` 9        FICE, FMP-FGTS, FMAI
====== =========================== ======== ===========================================

The four are **not versions** of one layout: the portfolio blocks, the tag names and the
``COD_DOC`` all differ, so each variant has its own header, ``Aplicacoes`` / ``Outras`` blocks,
inform row and document. A block that belongs to one variant therefore cannot be given to
another (``extra="forbid"``, and the document types differ).

**Field order is the XML order.** The writer walks ``model_fields`` in declaration order and
names each element ``<FIELD_NAME.upper()>``, so a field is the lower-cased tag from the page and
sits where the page's sample file puts it. Every field is required: the page says all fields
must be filled.

What the pages leave unsaid is decided here and stated on ``docs/submission/informe_sintetico.md``.
Integer fields are whole thousands of reais ("R$1000") and non-negative except the net equity
(``PATRIM_LIQ``), which may be negative. The quota value is the only decimal field; the pages give
it no scale, so it follows the repository money policy (2 places, truncated toward zero).
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
	model_validator,
)

from filings_cvm._internal.config.schemas._fields import validated_cnpj
from filings_cvm._internal.utils.xml_fields import (
	check_br_date,
	check_cnpj_shape,
	check_month_year,
	require_unique_funds,
	strict_decimal,
)


# The pages state no scale for the quota value; this is the repository money policy.
_QUOTA_SCALE = 2
_QUOTA_DIGITS = 18
_INT_MAX = 9223372036854775807

# Whole thousands of reais (R$1000) or a count: a signed 64-bit "long", never negative.
Thousands = Annotated[int, Field(strict=True, ge=0, le=_INT_MAX)]
# Net equity may be negative for an insolvent fund.
SignedThousands = Annotated[int, Field(strict=True, ge=-_INT_MAX, le=_INT_MAX)]
Count = Annotated[int, Field(strict=True, ge=0, le=_INT_MAX)]
QuotaValue = Annotated[
	Decimal,
	BeforeValidator(strict_decimal(_QUOTA_SCALE)),
	Field(ge=Decimal(0), max_digits=_QUOTA_DIGITS, decimal_places=_QUOTA_SCALE),
]

CompetenceField = Annotated[str, AfterValidator(check_month_year)]
DateField = Annotated[str, AfterValidator(check_br_date)]
CnpjField = Annotated[str, AfterValidator(check_cnpj_shape), AfterValidator(validated_cnpj)]


class SinteticoBlock(BaseModel):
	"""Base of every Informe Sintético block: closed (no unknown fields) and immutable."""

	model_config = ConfigDict(extra="forbid", frozen=True)


class SinteticoMercATermo(SinteticoBlock):
	"""MERC_A_TERMO — forward market positions."""

	pos_comprd: Thousands
	pos_vend: Thousands


class SinteticoMercOpcao(SinteticoBlock):
	"""MERC_OPCAO — option market premiums."""

	premio_pago: Thousands
	premio_receb: Thousands


class SinteticoContrFuturo(SinteticoBlock):
	"""CONTR_FUTURO — futures contracts (FITVM only)."""

	tot_margem_requerida: Thousands


class SinteticoDebt(SinteticoBlock):
	"""DEBT — debentures (FITVM only; Outros carries the same two tags without the wrapper)."""

	simples: Thousands
	conversiveis: Thousands


# --- FCCE (COD_DOC 5) -------------------------------------------------------------------------


class FcceHeader(SinteticoBlock):
	"""DESC_ADM of the FCCE variant."""

	cod_doc: Literal[5] = 5
	cnpj_adm: CnpjField
	dt_compt: CompetenceField
	dt_gerac_arq: DateField


class FcceAplicacoes(SinteticoBlock):
	"""APLICACOES of the FCCE variant."""

	acoes: Thousands
	quota_fdo_renda_fixa: Thousands
	tit_divida_public_fed: Thousands
	outro_vl_mobili_emiss_cia_aber: Thousands
	outra_aplic: Thousands


class FcceOutras(SinteticoBlock):
	"""OUTRAS of the FCCE variant."""

	vl_contr_futuro_mantido_aber: Thousands
	nr_tot_quotst_ult_dia_mes: Count
	vl_quota_ult_dia_mes: QuotaValue
	patrim_liq: SignedThousands
	quota_emitida_mes: Thousands
	quota_resg_mes: Thousands


class FcceAplicacoesPosFinal(SinteticoBlock):
	"""APLICACOES_POS_FINAL of the FCCE variant."""

	aplicacoes: FcceAplicacoes
	outras: FcceOutras


class FcceInform(SinteticoBlock):
	"""ROW_INFORME of the FCCE variant — one fund."""

	cnpj_fundo: CnpjField
	aplicacoes_pos_final: FcceAplicacoesPosFinal


# --- FITVM / FMP-FGTS CL / FIIM (COD_DOC 7) ---------------------------------------------------


class FitvmHeader(SinteticoBlock):
	"""DESC_ADM of the FITVM variant."""

	cod_doc: Literal[7] = 7
	cnpj_adm: CnpjField
	dt_compt: CompetenceField
	dt_gerac_arq: DateField


class FitvmAplicacoes(SinteticoBlock):
	"""APLICACOES of the FITVM variant."""

	acao: Thousands
	merc_a_termo: SinteticoMercATermo
	contr_futuro: SinteticoContrFuturo
	merc_opcao: SinteticoMercOpcao
	debt: SinteticoDebt
	certf_recibo_depos_outro_vl_mobili: Thousands
	tit_public: Thousands
	tit_renda_fixa_emiss_instit_financ: Thousands
	cota_fdo_invest_financ: Thousands
	outra_aplic: Thousands


class FitvmOutras(SinteticoBlock):
	"""OUTRAS of the FITVM variant."""

	nr_tot_quotst_ult_dia_mes: Count
	vl_quota_ult_dia_mes: QuotaValue
	patrim_liq: SignedThousands
	quota_emitida_mes: Thousands
	quota_resg_mes: Thousands


class FitvmAplicacoesPosFinal(SinteticoBlock):
	"""APLICACOES_POS_FINAL of the FITVM variant."""

	aplicacoes: FitvmAplicacoes
	outras: FitvmOutras


class FitvmInform(SinteticoBlock):
	"""ROW_INFORME of the FITVM variant — one fund."""

	cnpj_fundo: CnpjField
	aplicacoes_pos_final: FitvmAplicacoesPosFinal


# --- FIC-FITVM (COD_DOC 8) --------------------------------------------------------------------


class FicHeader(SinteticoBlock):
	"""DESC_ADM of the FIC-FITVM variant."""

	cod_doc: Literal[8] = 8
	cnpj_adm: CnpjField
	dt_compt: CompetenceField
	dt_gerac_arq: DateField


class FicAplicacoes(SinteticoBlock):
	"""APLICACOES of the FIC-FITVM variant."""

	cotas: Thousands
	tit_public: Thousands
	tit_renda_fixa_emiss_instit_financ: Thousands
	cota_fdo_invest_financ: Thousands
	outra_aplic: Thousands


class FicOutras(SinteticoBlock):
	"""OUTRAS of the FIC-FITVM variant."""

	nr_tot_quotst_ult_dia_mes: Count
	vl_quota_ult_dia_mes: QuotaValue
	patrim_liq: SignedThousands
	quota_emitida_mes: Thousands
	quota_resg_mes: Thousands


class FicAplicacoesPosFinal(SinteticoBlock):
	"""APLICACOES_POS_FINAL of the FIC-FITVM variant."""

	aplicacoes: FicAplicacoes
	outras: FicOutras


class FicInform(SinteticoBlock):
	"""ROW_INFORME of the FIC-FITVM variant — one fund."""

	cnpj_fundo: CnpjField
	aplicacoes_pos_final: FicAplicacoesPosFinal


# --- FICE / FMP-FGTS / FMAI (COD_DOC 9) -------------------------------------------------------


class OutrosHeader(SinteticoBlock):
	"""DESC_ADM of the Outros variant."""

	cod_doc: Literal[9] = 9
	cnpj_adm: CnpjField
	dt_compt: CompetenceField
	dt_gerac_arq: DateField


class OutrosAplicacoes(SinteticoBlock):
	"""APLICACOES of the Outros variant (debentures sit directly in the block, no ``DEBT``)."""

	acao: Thousands
	merc_opcao: SinteticoMercOpcao
	merc_a_termo: SinteticoMercATermo
	conversiveis: Thousands
	simples: Thousands
	tit_public: Thousands
	moeda_privat: Thousands
	outra_aplic: Thousands


class OutrosOutras(SinteticoBlock):
	"""OUTRAS of the Outros variant."""

	vl_contr_futuro_mantido_aberto: Thousands
	nr_tot_quotst_ult_dia_mes: Count
	vl_quota_ult_dia_mes: QuotaValue
	patrim_liq: SignedThousands
	quota_emitida_mes: Thousands
	quota_resg_mes: Thousands


class OutrosAplicacoesPosFinal(SinteticoBlock):
	"""APLICACOES_POS_FINAL of the Outros variant."""

	aplicacoes: OutrosAplicacoes
	outras: OutrosOutras


class OutrosInform(SinteticoBlock):
	"""ROW_INFORME of the Outros variant — one fund."""

	cnpj_fundo: CnpjField
	aplicacoes_pos_final: OutrosAplicacoesPosFinal


# --- Documents --------------------------------------------------------------------------------


class InformeSinteticoFcceDocument(SinteticoBlock):
	"""A whole FCCE file: one administrator, one competence, one or more funds."""

	header: FcceHeader
	informs: Annotated[list[FcceInform], Field(min_length=1)]

	@model_validator(mode="after")
	def _unique_funds(self) -> InformeSinteticoFcceDocument:
		"""Require each fund once per file.

		Returns
		-------
		InformeSinteticoFcceDocument
			The validated document.
		"""
		require_unique_funds([row.cnpj_fundo for row in self.informs])
		return self


class InformeSinteticoFitvmDocument(SinteticoBlock):
	"""A whole FITVM / FMP-FGTS CL / FIIM file."""

	header: FitvmHeader
	informs: Annotated[list[FitvmInform], Field(min_length=1)]

	@model_validator(mode="after")
	def _unique_funds(self) -> InformeSinteticoFitvmDocument:
		"""Require each fund once per file.

		Returns
		-------
		InformeSinteticoFitvmDocument
			The validated document.
		"""
		require_unique_funds([row.cnpj_fundo for row in self.informs])
		return self


class InformeSinteticoFicDocument(SinteticoBlock):
	"""A whole FIC-FITVM file."""

	header: FicHeader
	informs: Annotated[list[FicInform], Field(min_length=1)]

	@model_validator(mode="after")
	def _unique_funds(self) -> InformeSinteticoFicDocument:
		"""Require each fund once per file.

		Returns
		-------
		InformeSinteticoFicDocument
			The validated document.
		"""
		require_unique_funds([row.cnpj_fundo for row in self.informs])
		return self


class InformeSinteticoOutrosDocument(SinteticoBlock):
	"""A whole FICE / FMP-FGTS / FMAI file."""

	header: OutrosHeader
	informs: Annotated[list[OutrosInform], Field(min_length=1)]

	@model_validator(mode="after")
	def _unique_funds(self) -> InformeSinteticoOutrosDocument:
		"""Require each fund once per file.

		Returns
		-------
		InformeSinteticoOutrosDocument
			The validated document.
		"""
		require_unique_funds([row.cnpj_fundo for row in self.informs])
		return self
