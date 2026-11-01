"""Pydantic models for the CVM Informe Trimestral XML standard — V1 (valid until 2017-06).

Direction-neutral schema for ``PadraoXMLInfoTrim.asp``
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoTrim.asp), the first version
of the report that ``informe_quadrimestral`` (V2) replaced. The ``submission`` section builds
these models and serialises them to XML.

**Field order is the XML order.** The writer walks ``model_fields`` in declaration order and
names each element ``<FIELD_NAME.upper()>``, so every field is the lower-cased tag from the
page's sample file. Nothing is shared with V2's models: the page lists five fields per
fund (CNPJ, net worth, subscriber count, quota count, quota value), none of V2's lists.

Scales come from the page: net worth has 2 decimal places, quota value 12, the counts are
integers. Excess decimal places are truncated toward zero, never rounded. What the page leaves
unsaid is decided here and stated on ``docs/submission/informe_trimestral_v1.md``.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from filings_cvm._internal.config.schemas._fields import validated_cnpj
from filings_cvm._internal.utils.xml_fields import (
	check_br_date,
	check_cnpj_shape,
	check_month_year,
	strict_decimal,
)


_NET_WORTH_PLACES = 2
_QUOTA_VALUE_PLACES = 12
_INTEGER_DIGITS = 18  # the page states no width; 18 keeps every value inside a signed 64-bit long
_INT_MAX = 999_999_999_999
_MAX_INFORMS = 100
# The page: the month closes the civil quarter of the competence.
_QUARTER_END_MONTHS = frozenset({"03", "06", "09", "12"})

_NetWorth = Annotated[
	Decimal,
	BeforeValidator(strict_decimal(_NET_WORTH_PLACES)),
	Field(max_digits=_INTEGER_DIGITS + _NET_WORTH_PLACES, decimal_places=_NET_WORTH_PLACES),
]
_QuotaValue = Annotated[
	Decimal,
	BeforeValidator(strict_decimal(_QUOTA_VALUE_PLACES)),
	Field(max_digits=_INTEGER_DIGITS + _QUOTA_VALUE_PLACES, decimal_places=_QUOTA_VALUE_PLACES),
]
_Count = Annotated[int, Field(strict=True, ge=0, le=_INT_MAX)]
_Competence = Annotated[str, AfterValidator(check_month_year)]
_Date = Annotated[str, AfterValidator(check_br_date)]
_Cnpj = Annotated[str, AfterValidator(check_cnpj_shape), AfterValidator(validated_cnpj)]


class _Block(BaseModel):
	"""Base of every block: closed (no unknown fields) and immutable."""

	model_config = ConfigDict(extra="forbid", frozen=True)


class InformeTrimestralV1Header(_Block):
	"""CAB_INFORM — document header."""

	cod_doc: Literal[51] = 51
	dt_compt: _Competence
	dt_gerac_arq: _Date
	versao: Literal["1.0"] = "1.0"

	@model_validator(mode="after")
	def _check_quarter(self) -> InformeTrimestralV1Header:
		"""Require the competence month to close a civil quarter (03, 06, 09 or 12).

		Returns
		-------
		InformeTrimestralV1Header
			The validated header.

		Raises
		------
		ValueError
			If the month does not close a quarter.
		"""
		if self.dt_compt[:2] not in _QUARTER_END_MONTHS:
			raise ValueError("dt_compt month must close a quarter: 03, 06, 09 or 12")
		return self


class InformeTrimestralV1Inform(_Block):
	"""INFORM — the quarterly report of one fund."""

	cnpj_fdo: _Cnpj
	patrim_liq: _NetWorth
	qt_cotistas: _Count
	qt_quota: _Count
	vl_patrim_quota: _QuotaValue


class InformeTrimestralV1Document(_Block):
	"""DOC_ARQ — a whole file: one competence, 1 to 100 funds."""

	header: InformeTrimestralV1Header
	informs: list[InformeTrimestralV1Inform] = Field(min_length=1, max_length=_MAX_INFORMS)

	@model_validator(mode="after")
	def _check_unique_funds(self) -> InformeTrimestralV1Document:
		"""Reject the same fund twice in one file.

		Returns
		-------
		InformeTrimestralV1Document
			The validated document.

		Raises
		------
		ValueError
			If a CNPJ repeats.
		"""
		cnpjs = [i.cnpj_fdo for i in self.informs]
		if len(set(cnpjs)) != len(cnpjs):
			raise ValueError("a fund appears twice in the file")
		return self
