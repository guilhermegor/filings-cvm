"""Pydantic models for the Informe Mensal de Investidor Não Residente XML standard.

Direction-neutral schema for ``PadraoXMLInfoMensalINR.asp``
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoMensalINR.asp). The
``submission`` section builds these models and serialises them to XML.

**Field order is the XML order.** The writer walks ``model_fields`` in declaration order and
names each element ``<FIELD_NAME.upper()>``; a list field repeats its element and a nested model
is a block, exactly as in the page's sample file.

Every amount is a whole number (the page says "numérico e inteiro" for each one), held as
``int`` and written with no decimal part and no zero filler. Validators live in
``_internal/utils/inr_mensal_fields.py`` (this directory holds only models).
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import (
	AfterValidator,
	BaseModel,
	BeforeValidator,
	ConfigDict,
	Field,
	model_validator,
)

from filings_cvm._internal.utils.inr_mensal_fields import (
	check_br_date,
	check_cvm_code,
	check_month_year,
	check_participant_code,
	whole_amount,
)


_MAX_DIGITS_VALUE = 10**18 - 1
_MAX_PARTICIPANTS = 1000
_TABLE_A_MIN = 1
_TABLE_A_MAX = 30
# "APENAS para aplicações com código entre 15 e 24 da Tabela A" (derivatives).
_DERIVATIVE_MIN = 15
_DERIVATIVE_MAX = 24

# Flows, transfers and notionals cannot be negative; market value and net worth can.
AmountField = Annotated[
	int, BeforeValidator(whole_amount), Field(strict=True, ge=0, le=_MAX_DIGITS_VALUE)
]
SignedAmountField = Annotated[
	int,
	BeforeValidator(whole_amount),
	Field(strict=True, ge=-_MAX_DIGITS_VALUE, le=_MAX_DIGITS_VALUE),
]
CompetenceField = Annotated[str, AfterValidator(check_month_year)]
DateField = Annotated[str, AfterValidator(check_br_date)]
CvmCodeField = Annotated[str, AfterValidator(check_cvm_code)]
ParticipantCodeField = Annotated[str, AfterValidator(check_participant_code)]
ApplicationCodeField = Annotated[int, Field(strict=True, ge=_TABLE_A_MIN, le=_TABLE_A_MAX)]


class InrBlock(BaseModel):
	"""Base of every block: closed (no unknown fields) and immutable."""

	model_config = ConfigDict(extra="forbid", frozen=True)


class InrMensalHeader(InrBlock):
	"""CAB_INFORM — document header."""

	cod_doc: Literal[477] = 477
	versao: Literal["1.0"] = "1.0"
	cd_cvm: CvmCodeField
	dt_compt: CompetenceField
	dt_gerac_arq: DateField


class EntradaSaida(InrBlock):
	"""ENTRADA_SAIDA — resources in and out during the period (reais)."""

	vl_entr: AmountField
	vl_saida: AmountField


class TransfRecursos(InrBlock):
	"""TRANSF_RECURSOS — transfers between investment modalities (reais)."""

	vl_invest_carteira_haver_nres: AmountField
	vl_haver_nres_invest_carteira: AmountField
	vl_invest_carteira_adr: AmountField
	vl_adr_invest_carteira: AmountField
	vl_invest_carteira_estrang_direta: AmountField
	vl_estrang_direta_invest_carteira: AmountField


class RecursosRecebMesmoInvest(InrBlock):
	"""RECURSOS_RECEB_MESMO_INVEST — one resource received from the same investor."""

	cd_partic_origem: ParticipantCodeField
	vl_recebido: AmountField


class RecursosEnvMesmoInvest(InrBlock):
	"""RECURSOS_ENV_MESMO_INVEST — one resource sent to the same investor."""

	cd_partic_dest: ParticipantCodeField
	vl_enviado: AmountField


class RecursosRecebOutroInvest(InrBlock):
	"""RECURSOS_RECEB_OUTRO_INVEST — one resource received from a different investor."""

	cd_partic_origem: ParticipantCodeField
	vl_recebido: AmountField


class RecursosEnvOutroInvest(InrBlock):
	"""RECURSOS_ENV_OUTRO_INVEST — one resource sent to a different investor."""

	cd_partic_dest: ParticipantCodeField
	vl_enviado: AmountField


class RecursosMesmoInvest(InrBlock):
	"""RECURSOS_MESMO_INVEST — optional container; omit it when there is nothing to report."""

	recursos_receb_mesmo_invest: list[RecursosRecebMesmoInvest] = Field(default_factory=list)
	recursos_env_mesmo_invest: list[RecursosEnvMesmoInvest] = Field(default_factory=list)

	@model_validator(mode="after")
	def _not_empty(self) -> RecursosMesmoInvest:
		"""Refuse an empty container: the page says to omit it instead."""
		if not (self.recursos_receb_mesmo_invest or self.recursos_env_mesmo_invest):
			raise ValueError("omit RECURSOS_MESMO_INVEST when there is no data to report")
		return self


class RecursosOutroInvest(InrBlock):
	"""RECURSOS_OUTRO_INVEST — optional container; omit it when there is nothing to report."""

	recursos_receb_outro_invest: list[RecursosRecebOutroInvest] = Field(default_factory=list)
	recursos_env_outro_invest: list[RecursosEnvOutroInvest] = Field(default_factory=list)

	@model_validator(mode="after")
	def _not_empty(self) -> RecursosOutroInvest:
		"""Refuse an empty container: the page says to omit it instead."""
		if not (self.recursos_receb_outro_invest or self.recursos_env_outro_invest):
			raise ValueError("omit RECURSOS_OUTRO_INVEST when there is no data to report")
		return self


class MovRecursos(InrBlock):
	"""MOV_RECURSOS — resource movement during the period."""

	transf_recursos: TransfRecursos
	recursos_mesmo_invest: RecursosMesmoInvest | None = None
	recursos_outro_invest: RecursosOutroInvest | None = None


class Aplicacoes(InrBlock):
	"""APLICACOES — one application (Tabela A code) held by the participant."""

	cd_aplic: ApplicationCodeField
	vl_mercado_aplic: SignedAmountField
	vl_nocion_aplic: AmountField | None = None

	@model_validator(mode="after")
	def _notional_only_for_derivatives(self) -> Aplicacoes:
		"""Require the notional for codes 15-24 (derivatives) and forbid it elsewhere."""
		is_derivative = _DERIVATIVE_MIN <= self.cd_aplic <= _DERIVATIVE_MAX
		if is_derivative and self.vl_nocion_aplic is None:
			raise ValueError("vl_nocion_aplic is required for Tabela A codes 15 to 24")
		if not is_derivative and self.vl_nocion_aplic is not None:
			raise ValueError("vl_nocion_aplic must be omitted outside Tabela A codes 15 to 24")
		return self


class Participante(InrBlock):
	"""PARTICIPANTE — the monthly report of one participant."""

	cod_partic: ParticipantCodeField
	entrada_saida: EntradaSaida
	mov_recursos: MovRecursos
	aplicacoes: list[Aplicacoes] = Field(default_factory=list)
	patrim_liq: SignedAmountField


class InrMensalDocument(InrBlock):
	"""DOC_ARQ — a complete file: header plus 1 to 1000 participants of one competence."""

	header: InrMensalHeader
	participantes: Annotated[list[Participante], Field(min_length=1, max_length=_MAX_PARTICIPANTS)]

	@model_validator(mode="after")
	def _unique_participants(self) -> InrMensalDocument:
		"""Reject the same participant code listed twice."""
		codes = [p.cod_partic for p in self.participantes]
		if len(set(codes)) != len(codes):
			raise ValueError("each participant code may appear only once per file")
		return self
