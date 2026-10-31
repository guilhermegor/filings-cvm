"""Pydantic models for the CVM FAR (Demonstrativo de Fontes e Aplicações de Recursos) standard.

Direction-neutral schema for ``PadraoXMLFAR.asp``
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLFAR.asp). The ``submission``
section builds these models and serialises them to XML.

Field order is the XML order. What the page states is enforced here: the three quota decimals
carry 10 places (truncated, never rounded, never a float), ``VL_ENTR``/``VL_SAIDA`` are integers
in R$ mil, the three distribution fields appear together or not at all, and every movement code
of Table A appears exactly once with the Entrada/Saída columns Table A marks as fillable.
Decisions on what the page leaves open are stated on ``docs/submission/far.md``.
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
	field_validator,
	model_validator,
)

from filings_cvm._internal.config.schemas._fields import validated_cnpj
from filings_cvm._internal.utils.typing import type_checker
from filings_cvm._internal.utils.xml_fields import (
	check_br_date,
	check_cnpj_shape,
	check_month_year,
	strict_decimal,
)


_QUOTA_SCALE = 10
_QUOTA_DIGITS = 28
_BARE_CNPJ_DIGITS = 14
# R$ mil integer: 19 digits is the width of a signed 64-bit integer.
_AMOUNT_MAX = 9223372036854775807

# Table A: movement code -> (Entrada fillable, Saída fillable). The page's "S" is True and its
# "N" ("não pode ser preenchido") is False. The page requires every code in the file.
MOVEMENT_TABLE: dict[int, tuple[bool, bool]] = {
	37: (True, True),
	48: (True, True),
	53: (True, False),
	54: (False, True),
	55: (True, True),
	56: (True, False),
	57: (True, False),
	58: (True, False),
	60: (True, False),
	61: (False, True),
	62: (False, True),
	63: (False, True),
	64: (False, True),
	65: (False, True),
	66: (False, True),
	67: (True, False),
	68: (False, True),
	69: (False, True),
	70: (True, True),
	71: (True, False),
	72: (False, True),
	73: (False, True),
	74: (True, True),
	75: (True, True),
	77: (True, True),
	78: (True, True),
	144: (True, False),
	145: (True, True),
	150: (False, True),
}


@type_checker
def _check_digits_only_cnpj(value: str) -> str:
	"""Require the CNPJ to be numeric (the page says "somente dígitos"), not alphanumeric.

	Parameters
	----------
	value : str
		The bare CNPJ already returned by ``validated_cnpj``.

	Returns
	-------
	str
		The same text.

	Raises
	------
	ValueError
		If the CNPJ holds a letter.
	"""
	if not value.isascii() or not value.isdigit() or len(value) != _BARE_CNPJ_DIGITS:
		raise ValueError("FAR CNPJ must be digits only")
	return value


# Shape check first (the library's unmasking drops every non-alphanumeric character), then the
# check digits, then the page's digits-only rule. Stored bare, 14 digits.
CnpjField = Annotated[
	str,
	AfterValidator(check_cnpj_shape),
	AfterValidator(validated_cnpj),
	AfterValidator(_check_digits_only_cnpj),
]
CompetenceField = Annotated[str, AfterValidator(check_month_year)]
DateField = Annotated[str, AfterValidator(check_br_date)]
QuotaDecimalField = Annotated[
	Decimal,
	BeforeValidator(strict_decimal(_QUOTA_SCALE)),
	Field(ge=Decimal(0), max_digits=_QUOTA_DIGITS, decimal_places=_QUOTA_SCALE),
]
# Quotista count and R$ mil amounts: integers, never negative, no bool/float/str.
CountField = Annotated[int, Field(strict=True, ge=0, le=_AMOUNT_MAX)]


class FarBlock(BaseModel):
	"""Base of every FAR block: closed (no unknown fields) and immutable."""

	model_config = ConfigDict(extra="forbid", frozen=True)


class FarHeader(FarBlock):
	"""DESC_ADM — administrator data, shared by every fund in the file."""

	cod_doc: Literal[4] = 4
	cnpj_adm: CnpjField
	dt_compt: CompetenceField
	dt_gerac_arq: DateField


class FarMovement(FarBlock):
	"""ROW_MOV_POR_FUNDO — one Table A movement (amounts in R$ mil)."""

	cd_mov: int = Field(strict=True)
	vl_entr: CountField | None = None
	vl_saida: CountField | None = None

	@model_validator(mode="after")
	def _check_table_a(self) -> FarMovement:
		"""Enforce Table A: known code, fillable columns filled, the others empty.

		Returns
		-------
		FarMovement
			The same model.

		Raises
		------
		ValueError
			If the code is not in Table A, or a column is filled/empty against Table A.
		"""
		if self.cd_mov not in MOVEMENT_TABLE:
			raise ValueError(f"CD_MOV {self.cd_mov} is not in Table A")
		entr_ok, saida_ok = MOVEMENT_TABLE[self.cd_mov]
		for name, allowed, value in (
			("VL_ENTR", entr_ok, self.vl_entr),
			("VL_SAIDA", saida_ok, self.vl_saida),
		):
			if allowed and value is None:
				raise ValueError(f"CD_MOV {self.cd_mov}: {name} is required")
			if not allowed and value is not None:
				raise ValueError(f"CD_MOV {self.cd_mov}: {name} must not be filled")
		return self


class FarFund(FarBlock):
	"""ROW_REGISTRO_MOVIMENTO — one fund's report."""

	cnpj_fundo: CnpjField
	nr_quota_circul_ult_dia_mes: QuotaDecimalField
	vl_quota_ult_dia_mes: QuotaDecimalField
	nr_total_quotst_ult_dia_mes: CountField
	vl_ult_distr_quota: QuotaDecimalField | None = None
	dt_distr: DateField | None = None
	vl_quota_dt_ult_distr: QuotaDecimalField | None = None
	movements: list[FarMovement]

	@model_validator(mode="after")
	def _check_distribution_and_movements(self) -> FarFund:
		"""Distribution fields come together; every Table A code appears exactly once.

		Returns
		-------
		FarFund
			The same model.

		Raises
		------
		ValueError
			If the distribution fields are partially filled, or Table A is not covered.
		"""
		distribution = (self.vl_ult_distr_quota, self.dt_distr, self.vl_quota_dt_ult_distr)
		if any(item is not None for item in distribution) and any(
			item is None for item in distribution
		):
			raise ValueError(
				"VL_ULT_DISTR_QUOTA, DT_DISTR and VL_QUOTA_DT_ULT_DISTR must all be given or "
				"all omitted"
			)
		codes = [movement.cd_mov for movement in self.movements]
		if sorted(codes) != sorted(MOVEMENT_TABLE):
			missing = sorted(set(MOVEMENT_TABLE) - set(codes))
			repeated = sorted({code for code in codes if codes.count(code) > 1})
			raise ValueError(
				f"every Table A code must appear exactly once (missing={missing}, "
				f"repeated={repeated})"
			)
		return self


class FarDocument(FarBlock):
	"""DOC_ARQ — header plus one report per fund (same competence, same administrator)."""

	header: FarHeader
	funds: list[FarFund] = Field(min_length=1)

	@field_validator("funds")
	@classmethod
	def _unique_funds(cls, funds: list[FarFund]) -> list[FarFund]:
		"""Reject the same fund reported twice in one file.

		Parameters
		----------
		funds : list[FarFund]
			The reports.

		Returns
		-------
		list[FarFund]
			The same list.

		Raises
		------
		ValueError
			If a CNPJ_FUNDO repeats.
		"""
		cnpjs = [fund.cnpj_fundo for fund in funds]
		if len(set(cnpjs)) != len(cnpjs):
			raise ValueError("CNPJ_FUNDO must be unique within one FAR file")
		return funds
