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
# (is a derivative code, notional omitted) -> what is wrong; absent keys are valid.
_NOTIONAL_PROBLEMS = {
	(True, True): "vl_nocion_aplic is required for Tabela A codes 15 to 24",
	(False, False): "vl_nocion_aplic must be omitted outside Tabela A codes 15 to 24",
}

# Flows, transfers and notionals cannot be negative; market value and net worth can.
_AmountField = Annotated[
	int, BeforeValidator(whole_amount), Field(strict=True, ge=0, le=_MAX_DIGITS_VALUE)
]
_SignedAmountField = Annotated[
	int,
	BeforeValidator(whole_amount),
	Field(strict=True, ge=-_MAX_DIGITS_VALUE, le=_MAX_DIGITS_VALUE),
]
_CompetenceField = Annotated[str, AfterValidator(check_month_year)]
_DateField = Annotated[str, AfterValidator(check_br_date)]
_CvmCodeField = Annotated[str, AfterValidator(check_cvm_code)]
_ParticipantCodeField = Annotated[str, AfterValidator(check_participant_code)]
_ApplicationCodeField = Annotated[int, Field(strict=True, ge=_TABLE_A_MIN, le=_TABLE_A_MAX)]


class _InrBlock(BaseModel):
	"""Base of every block: closed (no unknown fields) and immutable."""

	model_config = ConfigDict(extra="forbid", frozen=True)


class InrMensalHeader(_InrBlock):
	"""CAB_INFORM — document header."""

	cod_doc: Literal[477] = 477
	versao: Literal["1.0"] = "1.0"
	cd_cvm: _CvmCodeField
	dt_compt: _CompetenceField
	dt_gerac_arq: _DateField


class EntradaSaida(_InrBlock):
	"""ENTRADA_SAIDA — resources in and out during the period (reais)."""

	vl_entr: _AmountField
	vl_saida: _AmountField


class TransfRecursos(_InrBlock):
	"""TRANSF_RECURSOS — transfers between investment modalities (reais)."""

	vl_invest_carteira_haver_nres: _AmountField
	vl_haver_nres_invest_carteira: _AmountField
	vl_invest_carteira_adr: _AmountField
	vl_adr_invest_carteira: _AmountField
	vl_invest_carteira_estrang_direta: _AmountField
	vl_estrang_direta_invest_carteira: _AmountField


class RecursosRecebMesmoInvest(_InrBlock):
	"""RECURSOS_RECEB_MESMO_INVEST — one resource received from the same investor."""

	cd_partic_origem: _ParticipantCodeField
	vl_recebido: _AmountField


class RecursosEnvMesmoInvest(_InrBlock):
	"""RECURSOS_ENV_MESMO_INVEST — one resource sent to the same investor."""

	cd_partic_dest: _ParticipantCodeField
	vl_enviado: _AmountField


class RecursosRecebOutroInvest(_InrBlock):
	"""RECURSOS_RECEB_OUTRO_INVEST — one resource received from a different investor."""

	cd_partic_origem: _ParticipantCodeField
	vl_recebido: _AmountField


class RecursosEnvOutroInvest(_InrBlock):
	"""RECURSOS_ENV_OUTRO_INVEST — one resource sent to a different investor."""

	cd_partic_dest: _ParticipantCodeField
	vl_enviado: _AmountField


class RecursosMesmoInvest(_InrBlock):
	"""RECURSOS_MESMO_INVEST — optional container; omit it when there is nothing to report."""

	recursos_receb_mesmo_invest: list[RecursosRecebMesmoInvest] = Field(default_factory=list)
	recursos_env_mesmo_invest: list[RecursosEnvMesmoInvest] = Field(default_factory=list)

	@model_validator(mode="after")
	def _not_empty(self) -> RecursosMesmoInvest:
		"""Refuse an empty container: the page says to omit it instead."""
		if not (self.recursos_receb_mesmo_invest or self.recursos_env_mesmo_invest):
			raise ValueError("omit RECURSOS_MESMO_INVEST when there is no data to report")
		return self


class RecursosOutroInvest(_InrBlock):
	"""RECURSOS_OUTRO_INVEST — optional container; omit it when there is nothing to report."""

	recursos_receb_outro_invest: list[RecursosRecebOutroInvest] = Field(default_factory=list)
	recursos_env_outro_invest: list[RecursosEnvOutroInvest] = Field(default_factory=list)

	@model_validator(mode="after")
	def _not_empty(self) -> RecursosOutroInvest:
		"""Refuse an empty container: the page says to omit it instead."""
		if not (self.recursos_receb_outro_invest or self.recursos_env_outro_invest):
			raise ValueError("omit RECURSOS_OUTRO_INVEST when there is no data to report")
		return self


class MovRecursos(_InrBlock):
	"""MOV_RECURSOS — resource movement during the period."""

	transf_recursos: TransfRecursos
	recursos_mesmo_invest: RecursosMesmoInvest | None = None
	recursos_outro_invest: RecursosOutroInvest | None = None


class Aplicacoes(_InrBlock):
	"""APLICACOES — one application (Tabela A code) held by the participant."""

	cd_aplic: _ApplicationCodeField
	vl_mercado_aplic: _SignedAmountField
	vl_nocion_aplic: _AmountField | None = None

	@model_validator(mode="after")
	def _notional_only_for_derivatives(self) -> Aplicacoes:
		"""Require the notional for codes 15-24 (derivatives) and forbid it elsewhere."""
		is_derivative = _DERIVATIVE_MIN <= self.cd_aplic <= _DERIVATIVE_MAX
		problem = _NOTIONAL_PROBLEMS.get((is_derivative, self.vl_nocion_aplic is None))
		if problem:
			raise ValueError(problem)
		return self


class Participante(_InrBlock):
	"""PARTICIPANTE — the monthly report of one participant."""

	cod_partic: _ParticipantCodeField
	entrada_saida: EntradaSaida
	mov_recursos: MovRecursos
	aplicacoes: list[Aplicacoes] = Field(default_factory=list)
	patrim_liq: _SignedAmountField


class InrMensalDocument(_InrBlock):
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

	@model_validator(mode="after")
	def _codes_belong_to_the_representative(self) -> InrMensalDocument:
		"""Require every participant's AAAAA (representative) to equal the header ``CD_CVM``."""
		prefix = self.header.cd_cvm
		stray = [p.cod_partic for p in self.participantes if p.cod_partic.split(".")[0] != prefix]
		if stray:
			raise ValueError(f"participant code prefix must equal header CD_CVM: {stray[0]}")
		return self
