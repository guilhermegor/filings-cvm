"""Pydantic models for the CVM Daily Report (Informe Diário) XML standard — V2.

Direction-neutral schema for ``PadraoXMLInfoDiarioNet739``, in force from 2012-07-01 to
2015-09-30 (https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiarioNet739.asp).

The delta against V4 (``schemas/informe_diario.py``), measured from the page: ``VERSAO``
is ``2.0``; the fund is identified by ``CNPJ_FDO`` alone (no ``COD_SUBCLASSE``); there is
no ``DATA_PROX_PL``. Scales, the shareholder block and the 100-fund cap are unchanged, so
those pieces are imported from the V4 schema, never copied. ``NOME_FUNDO``,
``RESG_NAO_PROCES`` and ``LIQ_DIA_DISPON`` appear on the page only inside HTML comments
and are therefore not part of the standard.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from filings_cvm._internal.config.schemas._fields import validated_cnpj
from filings_cvm._internal.config.schemas.informe_diario import (
	InformeDiarioHeader,
	QuotaValueField,
	SignificantShareholder,
	TwoDecimalField,
)


class InformeDiarioV2Header(InformeDiarioHeader, BaseModel):
	"""CAB_INFORM — V2 header; ``VERSAO`` is pinned to ``2.0``."""

	versao: Literal["2.0"] = "2.0"


class InformeDiarioV2Inform(BaseModel):
	"""INFORM — one fund's daily movement in V2, keyed by ``CNPJ_FDO``."""

	cnpj_fdo: str
	vl_total: TwoDecimalField
	vl_quota: QuotaValueField
	patrim_liq: TwoDecimalField
	captc_dia: TwoDecimalField
	resg_dia: TwoDecimalField
	vl_total_sai: TwoDecimalField
	vl_total_atv: TwoDecimalField
	nr_cotst: int = Field(ge=0)
	lista_cotst_signif: list[SignificantShareholder] | None = None

	@field_validator("cnpj_fdo")
	@classmethod
	def _check_cnpj(cls, v: str) -> str:
		"""Validate and normalise the fund CNPJ (check-digit aware).

		Parameters
		----------
		v : str
			The fund CNPJ in any shape.

		Returns
		-------
		str
			The unmasked (bare) CNPJ.
		"""
		return validated_cnpj(v)


class InformeDiarioV2Document(BaseModel):
	"""DOC_ARQ — complete V2 Daily Report document (up to 100 funds)."""

	header: InformeDiarioV2Header
	informs: list[InformeDiarioV2Inform] = Field(max_length=100)
