"""Pydantic models for the CVM Informe de Portabilidade XML standard (COD_DOC 478, V1.0).

Direction-neutral contract for ``PadraoXMLInfoPortabilidade.asp``
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoPortabilidade.asp).
The ``submission`` section builds these models and serialises them to XML.

The page states no decimal field: every ``QTDE_*``/``ATEND_*`` value is a request count, so
it is a strict non-negative ``int`` (a ``float``, ``bool`` or numeric string is refused, not
converted). The page does not state the format of ``DT_EVENT`` ("mês das solicitações"); it is
modelled as ``MM/AAAA``, the format of the header competence. The page does not state how many
``INFORM`` blocks a file may hold; at least one is required and there is no upper bound.
"""

from __future__ import annotations

from datetime import datetime
import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from filings_cvm._internal.config.schemas._fields import validated_cnpj
from filings_cvm._internal.utils.typing import type_checker


# fullmatch + [0-9]: ``$`` accepts a trailing newline and ``\d`` accepts non-ASCII digits.
_DATE_BR_RE = re.compile(r"[0-9]{2}/[0-9]{2}/[0-9]{4}")
_MONTH_YEAR_RE = re.compile(r"[0-9]{2}/[0-9]{4}")
# Bare or masked CNPJ (letters allowed for the 2026 alphanumeric form). The library's unmasking
# drops every non-alphanumeric character, so the shape is checked before it runs.
_CNPJ_SHAPE_RE = re.compile(
	r"[0-9A-Z]{12}[0-9]{2}|[0-9A-Z]{2}\.[0-9A-Z]{3}\.[0-9A-Z]{3}/[0-9A-Z]{4}-[0-9]{2}"
)
# Earliest year a CVM filing can plausibly carry; rejects 0001-style typos.
_MIN_YEAR = 1900

# A request count: strict (no float/bool/str coercion) and never negative.
_CountField = Annotated[int, Field(strict=True, ge=0)]


class PortabilidadeHeader(BaseModel):
	"""CAB_INFORM — document-level header block."""

	model_config = ConfigDict(validate_assignment=True)

	cod_doc: Literal[478] = 478
	versao: Literal["1.0"] = "1.0"
	dt_compt: Annotated[str, Field(strict=True)]
	dt_gerac_arq: Annotated[str, Field(strict=True)]

	@field_validator("dt_compt")
	@classmethod
	def _check_dt_compt(cls, v: str) -> str:
		"""Require a real ``MM/AAAA`` month.

		Parameters
		----------
		v : str
			Value to validate.

		Returns
		-------
		str
			The unchanged value.

		Raises
		------
		ValueError
			If the shape is wrong, the month is not 01-12 or the year is before 1900.
		"""
		return _check_month_year(v)

	@field_validator("dt_gerac_arq")
	@classmethod
	def _check_dt_gerac_arq(cls, v: str) -> str:
		"""Require a real ``DD/MM/AAAA`` calendar date.

		Parameters
		----------
		v : str
			Value to validate.

		Returns
		-------
		str
			The unchanged value.

		Raises
		------
		ValueError
			If the shape is wrong, the date does not exist or the year is before 1900.
		"""
		if not _DATE_BR_RE.fullmatch(v):
			raise ValueError("date must follow DD/MM/AAAA")
		_check_min_year(v, "%d/%m/%Y")
		return v


class PortabilidadeInform(BaseModel):
	"""INFORM — portability requests of one regulated entity for one month."""

	model_config = ConfigDict(validate_assignment=True)

	cnpj_partic: Annotated[str, Field(strict=True)]
	dt_event: Annotated[str, Field(strict=True)]
	qtde_solicit_orig: _CountField
	qtde_solicit_dest: _CountField
	qtde_canc: _CountField
	atend_prazo_regul: _CountField
	atend_prazo_estend: _CountField
	qtde_recus: _CountField

	@field_validator("cnpj_partic")
	@classmethod
	def _check_cnpj(cls, v: str) -> str:
		"""Check the CNPJ shape, then its check digits; store the bare form.

		Parameters
		----------
		v : str
			Value to validate, bare or masked.

		Returns
		-------
		str
			The bare 14-character CNPJ.

		Raises
		------
		ValueError
			If the shape or the check digits are wrong.
		"""
		if not _CNPJ_SHAPE_RE.fullmatch(v):
			raise ValueError("CNPJ must be 14 characters, bare or NN.NNN.NNN/NNNN-NN")
		return validated_cnpj(v)

	@field_validator("dt_event")
	@classmethod
	def _check_dt_event(cls, v: str) -> str:
		"""Require a real ``MM/AAAA`` month.

		Parameters
		----------
		v : str
			Value to validate.

		Returns
		-------
		str
			The unchanged value.

		Raises
		------
		ValueError
			If the shape is wrong, the month is not 01-12 or the year is before 1900.
		"""
		return _check_month_year(v)


class InformePortabilidadeDocument(BaseModel):
	"""DOC_ARQ — one header plus one INFORM block per regulated entity and month."""

	header: PortabilidadeHeader
	informs: Annotated[list[PortabilidadeInform], Field(min_length=1)]


@type_checker
def _check_min_year(value: str, fmt: str) -> None:
	"""Reject a date whose year is before ``_MIN_YEAR`` (shared by both validators).

	Parameters
	----------
	value : str
		The date text, already shape-checked.
	fmt : str
		The ``strptime`` format of ``value``.

	Raises
	------
	ValueError
		If the date does not exist or its year is before ``_MIN_YEAR``.
	"""
	if datetime.strptime(value, fmt).year < _MIN_YEAR:  # noqa: DTZ007
		raise ValueError(f"year must be >= {_MIN_YEAR}")


@type_checker
def _check_month_year(value: str) -> str:
	"""Validate a ``MM/AAAA`` string (private helper shared by two models of this module).

	Parameters
	----------
	value : str
		The month text.

	Returns
	-------
	str
		The same text.

	Raises
	------
	ValueError
		If the shape is wrong, the month is not 01-12 or the year is before 1900.
	"""
	if not _MONTH_YEAR_RE.fullmatch(value):
		raise ValueError("month must follow MM/AAAA")
	_check_min_year(value, "%m/%Y")
	return value
