"""Pydantic models for the CVM Balancete in the fixed-width COFI 4010 standard.

``PadraoXMLBalancete.asp`` defines no XML: the Balancete is uploaded as a COS 4010 (BACEN)
or COFI 4010 (CVM) file. These models describe the COFI 4010 document, laid out in
``PadraoCOFI.aspx`` as 71-position records. One file holds the balancetes of one or more
funds, all of the same competence (and administrator).

Amounts are truncated toward zero to 2 decimal places (the page states no scale; this is
an assumption) and ``float`` is refused. Every shape rule the writer relies on is enforced
here, so a document that validates always serialises.
"""

from __future__ import annotations

from decimal import Decimal
import re
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field, field_validator, model_validator

from filings_cvm._internal.config.schemas._fields import validated_cnpj
from filings_cvm._internal.utils.cofi_records import MAX_RECORDS, parse_cofi_amount


# Account code: the page gives 10 positions for "código e dígito verificador"; digits only.
_COD_CONTA_RE = re.compile(r"[0-9]{10}")
_CNPJ_SHAPE_RE = re.compile(r"[0-9]{2}\.?[0-9]{3}\.?[0-9]{3}/?[0-9]{4}-?[0-9]{2}")
_COMPETENCE_RE = re.compile(r"(0[1-9]|1[0-2])[0-9]{4}")

CofiAmount = Annotated[Decimal, BeforeValidator(parse_cofi_amount)]


class BalanceteConta(BaseModel):
	"""One account line: code and the three balance columns.

	Attributes
	----------
	cod_conta : str
		Account code with check digit (10 digits).
	vl_total : Decimal
		Total column.
	vl_ate_90 : Decimal
		Realizável/Exigível up to 90 days column.
	vl_apos_90 : Decimal
		Realizável/Exigível after 90 days column.
	"""

	cod_conta: str
	vl_total: CofiAmount
	vl_ate_90: CofiAmount = Decimal("0.00")
	vl_apos_90: CofiAmount = Decimal("0.00")

	@field_validator("cod_conta", mode="before")
	@classmethod
	def _check_cod_conta(cls, value: object) -> str:
		"""Require exactly 10 ASCII digits (no mask; the page states 10 positions).

		Parameters
		----------
		value : object
			Raw account code.

		Returns
		-------
		str
			The validated code.

		Raises
		------
		ValueError
			If the value is not a string or is not 10 digits.
		"""
		if not isinstance(value, str) or not _COD_CONTA_RE.fullmatch(value):
			raise ValueError(f"cod_conta must be a string of 10 digits, got {value!r}")
		return value


class BalanceteFundo(BaseModel):
	"""The balancete of one fund: its CNPJ and account lines.

	Attributes
	----------
	cnpj_fdo : str
		Fund CNPJ, validated by check digit and stored bare (14 characters).
	contas : list[BalanceteConta]
		Account lines; at least one, no repeated account code (CVM check D5).
	"""

	cnpj_fdo: str
	contas: list[BalanceteConta] = Field(min_length=1)

	@field_validator("cnpj_fdo", mode="before")
	@classmethod
	def _check_cnpj(cls, value: object) -> str:
		"""Check the CNPJ shape, then its check digits.

		Parameters
		----------
		value : object
			Raw CNPJ.

		Returns
		-------
		str
			The bare 14-digit CNPJ.

		Raises
		------
		ValueError
			If the value is not a CNPJ-shaped string or fails the check digits.
		"""
		if not isinstance(value, str) or not _CNPJ_SHAPE_RE.fullmatch(value):
			raise ValueError(f"cnpj_fdo is not CNPJ-shaped: {value!r}")
		return validated_cnpj(value)

	@model_validator(mode="after")
	def _unique_accounts(self) -> BalanceteFundo:
		"""Reject an account code informed more than once.

		Returns
		-------
		BalanceteFundo
			The validated model.

		Raises
		------
		ValueError
			If any account code repeats.
		"""
		codes = [conta.cod_conta for conta in self.contas]
		if len(set(codes)) != len(codes):
			raise ValueError("duplicate account code (CVM check D5)")
		return self


class BalanceteDocument(BaseModel):
	"""A COFI 4010 file: one competence and one or more fund balancetes.

	Attributes
	----------
	competence : str
		Competence in ``MMAAAA`` form (month 01-12).
	fundos : list[BalanceteFundo]
		Fund balancetes; at least one, no repeated CNPJ, and the whole file within the
		6-digit footer record count.
	"""

	competence: str
	fundos: list[BalanceteFundo] = Field(min_length=1)

	@field_validator("competence", mode="before")
	@classmethod
	def _check_competence(cls, value: object) -> str:
		"""Require ``MMAAAA`` with a real month.

		Parameters
		----------
		value : object
			Raw competence.

		Returns
		-------
		str
			The validated competence.

		Raises
		------
		ValueError
			If it is not six digits with a month from 01 to 12.
		"""
		if not isinstance(value, str) or not _COMPETENCE_RE.fullmatch(value):
			raise ValueError(f"competence must be MMAAAA, got {value!r}")
		return value

	@model_validator(mode="after")
	def _check_unique_funds(self) -> BalanceteDocument:
		"""Reject a fund CNPJ informed more than once.

		Returns
		-------
		BalanceteDocument
			The validated model.

		Raises
		------
		ValueError
			If a CNPJ repeats.
		"""
		cnpjs = [fundo.cnpj_fdo for fundo in self.fundos]
		if len(set(cnpjs)) != len(cnpjs):
			raise ValueError("duplicate fund CNPJ in one file")
		return self

	@model_validator(mode="after")
	def _check_record_count(self) -> BalanceteDocument:
		"""Reject files too long for the footer count.

		Returns
		-------
		BalanceteDocument
			The validated model.

		Raises
		------
		ValueError
			If the total record count exceeds the footer field.
		"""
		n_records = sum(1 + len(fundo.contas) for fundo in self.fundos) + 1
		if n_records > MAX_RECORDS:
			raise ValueError(f"{n_records} records exceed the 6-digit footer count")
		return self
