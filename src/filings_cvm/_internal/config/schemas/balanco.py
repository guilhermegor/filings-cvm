"""Pydantic models for the CVM Balanço, COFI 4016 standard.

The shared, direction-neutral shape of the document the ``submission`` section writes. The
CVM page ``PadraoXMLBalanco.asp`` defines no XML for the Balanço: it is sent as a COS 4016
or COFI 4016 upload, and this module models the COFI 4016 one (layout on the CVM page
``PadraoCOFI.aspx``): per fund a control header (CNPJ, competence ``MMAAAA``), one record
per account with three amount columns (total, até 90 dias, após 90 dias), and one file
footer.

A file may carry the balanços of several funds of one competence and one administrator
(the page's rule); the administrator is not a field of the file, so that half cannot be
checked here. Amounts are exact ``Decimal`` — a ``float`` is refused — truncated to two
places (an assumption: the page states no scale). The CVM's mechanical consistency checks
run when the document is built, so a document that CVM would refuse cannot be constructed;
the checks live in ``_internal.utils.balanco_checks``.
"""

from __future__ import annotations

import calendar
from datetime import date
from decimal import Decimal
import re
from typing import Annotated

from pydantic import (
	BaseModel,
	BeforeValidator,
	Field,
	field_validator,
	model_validator,
)

from filings_cvm._internal.config.schemas._fields import validated_cnpj
from filings_cvm._internal.utils.balanco_checks import check_fund_accounts
from filings_cvm._internal.utils.cofi_records import (
	AMOUNT_DIGITS,
	AMOUNT_SCALE,
	MAX_RECORD_COUNT,
	decimal_amount_input,
	is_valid_account_code,
)


_CNPJ_SHAPE = re.compile(r"[0-9]{14}|[0-9]{2}\.[0-9]{3}\.[0-9]{3}/[0-9]{4}-[0-9]{2}")
_COMPETENCE_SHAPE = re.compile(r"(0[1-9]|1[0-2])[0-9]{4}")
_MIN_YEAR = 1900

# Amount column: exact decimal, 18 digits of which AMOUNT_SCALE are fractional.
AmountField = Annotated[
	Decimal,
	BeforeValidator(decimal_amount_input),
	Field(max_digits=AMOUNT_DIGITS, decimal_places=AMOUNT_SCALE),
]


class BalancoAccount(BaseModel):
	"""One account record of a fund's Balanço.

	Attributes
	----------
	conta : str
		8-character COFI account code (7-digit body + valid check digit).
	total : Decimal
		Total column.
	ate_90 : Decimal
		Realizável/Exigível até 90 dias column.
	apos_90 : Decimal
		Realizável/Exigível após 90 dias column.
	"""

	conta: str
	total: AmountField
	ate_90: AmountField
	apos_90: AmountField

	@field_validator("conta")
	@classmethod
	def _check_conta(cls, value: str) -> str:
		"""Require a well-formed code with a correct check digit.

		Parameters
		----------
		value : str
			The account code.

		Returns
		-------
		str
			The unchanged code.

		Raises
		------
		ValueError
			If the code is not 8 digits or its check digit is wrong.
		"""
		if not is_valid_account_code(value):
			raise ValueError(f"invalid account code or check digit: {value!r}")
		return value


class BalancoFund(BaseModel):
	"""The Balanço of one fund: its CNPJ and account records.

	Attributes
	----------
	cnpj : str
		Fund CNPJ, stored as 14 bare digits (the layout field is numeric).
	contas : list[BalancoAccount]
		Account records; an account may appear only once (CVM check D5).
	"""

	cnpj: str
	contas: Annotated[list[BalancoAccount], Field(min_length=1)]

	@field_validator("cnpj")
	@classmethod
	def _check_cnpj(cls, value: str) -> str:
		"""Check the CNPJ shape, then its check digits.

		Parameters
		----------
		value : str
			A bare or punctuated numeric CNPJ.

		Returns
		-------
		str
			The 14 bare digits.

		Raises
		------
		ValueError
			If the shape is wrong or the check digits do not validate.
		"""
		if _CNPJ_SHAPE.fullmatch(value) is None:
			raise ValueError(f"CNPJ must be 14 digits, bare or punctuated: {value!r}")
		return validated_cnpj(value)

	@model_validator(mode="after")
	def _check_unique_accounts(self) -> BalancoFund:
		"""Reject an account informed more than once (CVM check D5).

		Returns
		-------
		BalancoFund
			The validated model.

		Raises
		------
		ValueError
			If an account code repeats.
		"""
		codes = [account.conta for account in self.contas]
		repeated = sorted({code for code in codes if codes.count(code) > 1})
		if repeated:
			raise ValueError(f"[D5] account informed more than once: {repeated}")
		return self


class BalancoDocument(BaseModel):
	"""A COFI 4016 Balanço file: one competence, one or more funds.

	Attributes
	----------
	competencia : str
		Competence as ``MMAAAA``.
	fundos : list[BalancoFund]
		The funds' balanços; each CNPJ may appear once.
	"""

	competencia: str
	fundos: Annotated[list[BalancoFund], Field(min_length=1)]

	@field_validator("competencia")
	@classmethod
	def _check_competencia(cls, value: str) -> str:
		"""Require a real ``MMAAAA`` month.

		Parameters
		----------
		value : str
			Competence text.

		Returns
		-------
		str
			The unchanged competence.

		Raises
		------
		ValueError
			If the shape is wrong or the year is before 1900.
		"""
		if _COMPETENCE_SHAPE.fullmatch(value) is None or int(value[2:]) < _MIN_YEAR:
			raise ValueError(f"competencia must be a real MMAAAA month, got {value!r}")
		return value

	@property
	def reference_date(self) -> date:
		"""Last day of the competence month, the date the plan validity is judged on.

		Returns
		-------
		date
			The last calendar day of the competence month.
		"""
		month, year = int(self.competencia[:2]), int(self.competencia[2:])
		return date(year, month, calendar.monthrange(year, month)[1])

	@model_validator(mode="after")
	def _check_consistency(self) -> BalancoDocument:
		"""Reject repeated funds, an oversized file, and any failed CVM check.

		Returns
		-------
		BalancoDocument
			The validated model.

		Raises
		------
		ValueError
			Listing every violation found.
		"""
		errors: list[str] = []
		cnpjs = [fund.cnpj for fund in self.fundos]
		errors.extend(
			f"fund {cnpj} informed more than once"
			for cnpj in sorted(set(cnpjs))
			if cnpjs.count(cnpj) > 1
		)
		records = 1 + sum(1 + len(fund.contas) for fund in self.fundos)
		if records > MAX_RECORD_COUNT:
			errors.append(
				f"file would hold {records} records, the footer counts up to {MAX_RECORD_COUNT}"
			)
		for fund in self.fundos:
			accounts = {a.conta: (a.total, a.ate_90, a.apos_90) for a in fund.contas}
			errors.extend(
				f"fund {fund.cnpj}: {message}"
				for message in check_fund_accounts(accounts, self.reference_date)
			)
		if errors:
			raise ValueError("; ".join(errors))
		return self
