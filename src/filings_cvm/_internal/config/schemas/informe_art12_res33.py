"""Pydantic models for the CVM Informe Art. 12 Res. CVM 33 (escriturador) XML standard.

Direction-neutral schema for ``PadraoXMLPrest.asp``
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPrest.asp). The ``submission``
section builds these models and serialises them to XML.

The page has no decimal field, so no decimal scale applies. What it leaves unsaid or
contradicts is decided here and stated on ``docs/submission/informe_art12_res33.md``:

- the sample closes ``LISTA_PREST`` as ``LISTA_APREST``; the opening tag is used;
- the page does not say how many prestadores, emissores or ativos a file holds; each list needs
  at least one entry and no upper bound is invented;
- codes 42, 52 and 65 "were migrated to 41 from 01/07/2014", so they are accepted only for a
  competence before 07/2014.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from filings_cvm._internal.config.schemas._fields import validated_cnpj
from filings_cvm._internal.utils.xml_fields_art12 import (
	check_br_date,
	check_cnpj_shape,
	check_month_year,
	parse_br_date,
	parse_month_year,
)


CompetenceField = Annotated[str, AfterValidator(check_month_year)]
DateField = Annotated[str, AfterValidator(check_br_date)]
CnpjField = Annotated[str, AfterValidator(check_cnpj_shape), AfterValidator(validated_cnpj)]

# Tabela A: 41 is current; 42/52/65 were folded into 41 from this month on.
_LEGACY_PROVIDER_CODES = (42, 52, 65)
_LEGACY_CUTOFF_MONTH = parse_month_year("07/2014")


class _Block(BaseModel):
	"""Base of every block: closed (no unknown fields) and immutable."""

	model_config = ConfigDict(extra="forbid", frozen=True)


class PrestHeader(_Block):
	"""DS_INFORM — competence and generation date of the file."""

	dt_compt: CompetenceField
	dt_gerac_arq: DateField

	@model_validator(mode="after")
	def _generated_not_before_competence(self) -> PrestHeader:
		"""Reject a generation date earlier than the competence month.

		Returns
		-------
		PrestHeader
			The validated model.

		Raises
		------
		ValueError
			If the file claims to be generated before its competence month began.
		"""
		if parse_br_date(self.dt_gerac_arq) < parse_month_year(self.dt_compt):
			raise ValueError("dt_gerac_arq must not precede the competence month")
		return self


class PrestAtivo(_Block):
	"""ATIVO — one escriturado asset type and its contract dates (Tabela B)."""

	ativo_escriturado: Literal["A1", "A2", "A3", "A4"]
	dt_inicio_contrato: DateField
	dt_fim_contrato: DateField | None = None

	@model_validator(mode="after")
	def _contract_ends_after_start(self) -> PrestAtivo:
		"""Reject a contract that ends before it starts.

		Returns
		-------
		PrestAtivo
			The validated model.

		Raises
		------
		ValueError
			If ``dt_fim_contrato`` is earlier than ``dt_inicio_contrato``.
		"""
		if self.dt_fim_contrato is None:
			return self
		if parse_br_date(self.dt_fim_contrato) < parse_br_date(self.dt_inicio_contrato):
			raise ValueError("dt_fim_contrato must not precede dt_inicio_contrato")
		return self


class PrestEmissor(_Block):
	"""EMISSOR — one issuer and the assets escriturados for it (at least one)."""

	cnpj_emissor: CnpjField
	ativos: Annotated[tuple[PrestAtivo, ...], Field(min_length=1)]


class PrestDados(_Block):
	"""DS_PREST — identification of the service provider."""

	cnpj_escriturador: CnpjField
	cd_tp_prest: Literal[41, 42, 52, 65]


class PrestInform(_Block):
	"""INFORM_PREST — one provider with its issuers (at least one, no repeated CNPJ)."""

	ds_prest: PrestDados
	emissores: Annotated[tuple[PrestEmissor, ...], Field(min_length=1)]

	@model_validator(mode="after")
	def _unique_emissores(self) -> PrestInform:
		"""Reject the same issuer listed twice under one provider.

		Returns
		-------
		PrestInform
			The validated model.

		Raises
		------
		ValueError
			If a ``cnpj_emissor`` repeats.
		"""
		cnpjs = [emissor.cnpj_emissor for emissor in self.emissores]
		if len(set(cnpjs)) != len(cnpjs):
			raise ValueError("cnpj_emissor repeats within one prestador")
		return self


class PrestDocument(_Block):
	"""DOC_ARQ — the whole file: header plus one or more prestadores of one competence."""

	ds_inform: PrestHeader
	prestadores: Annotated[tuple[PrestInform, ...], Field(min_length=1)]

	@model_validator(mode="after")
	def _check_prestadores(self) -> PrestDocument:
		"""Enforce one entry per provider and the provider-code window.

		Returns
		-------
		PrestDocument
			The validated model.

		Raises
		------
		ValueError
			If a provider repeats, or a legacy code (42/52/65) is used from 07/2014 on.
		"""
		cnpjs = [p.ds_prest.cnpj_escriturador for p in self.prestadores]
		if len(set(cnpjs)) != len(cnpjs):
			raise ValueError("cnpj_escriturador repeats within the file")
		if parse_month_year(self.ds_inform.dt_compt) < _LEGACY_CUTOFF_MONTH:
			return self
		for prestador in self.prestadores:
			if prestador.ds_prest.cd_tp_prest in _LEGACY_PROVIDER_CODES:
				raise ValueError("cd_tp_prest 42, 52 and 65 ended on 07/2014; use 41")
		return self
