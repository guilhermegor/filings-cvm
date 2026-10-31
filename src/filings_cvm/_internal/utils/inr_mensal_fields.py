r"""Strict field validators for the Informe Mensal de Investidor Não Residente schema.

Pure functions (no I/O) that ``schemas/inr_mensal.py`` composes into ``Annotated`` field types.
They live here, not in a ``schemas/`` module, because that directory holds only Pydantic models
(``bin/check_schemas.py``).

Every shape check uses ``re.fullmatch`` with ``[0-9]``: a ``$`` anchor accepts a trailing newline
and ``\d`` accepts non-ASCII digits, and either would let a malformed value reach the XML.
"""

from datetime import date, datetime
from decimal import Decimal
import re

from filings_cvm._internal.utils.typing import type_checker


_DATE_BR_RE = re.compile(r"[0-9]{2}/[0-9]{2}/[0-9]{4}")
_MONTH_YEAR_RE = re.compile(r"[0-9]{2}/[0-9]{4}")
_WHOLE_RE = re.compile(r"-?[0-9]+")
# AAAAA.BBBBBB.CCCCCC.T-DV; "no zero filler" means no field starts with 0 (a 0 alone is not a
# CVM code either). T is 0 (own account) or 1 (collective account); DV is one digit.
_PARTICIPANT_RE = re.compile(r"[1-9][0-9]{0,4}\.[1-9][0-9]{0,5}\.[1-9][0-9]{0,5}\.[01]-[0-9]")
_CVM_CODE_RE = re.compile(r"[1-9][0-9]{0,4}")
# Earliest year a CVM filing can plausibly carry; rejects 0001-style typos.
_MIN_YEAR = 1900


@type_checker
def parse_br_date(value: str) -> date:
	"""Parse a ``DD/MM/AAAA`` string into a real calendar date.

	Parameters
	----------
	value : str
		The date text, zero-padded as the page states it.

	Returns
	-------
	date
		The parsed date.

	Raises
	------
	ValueError
		If the shape is wrong, the date does not exist (``31/02``) or the year is before 1900.
	"""
	if not _DATE_BR_RE.fullmatch(value):
		raise ValueError("date must follow DD/MM/AAAA")
	parsed = datetime.strptime(value, "%d/%m/%Y").date()  # noqa: DTZ007
	if parsed.year < _MIN_YEAR:
		raise ValueError(f"year must be >= {_MIN_YEAR}")
	return parsed


@type_checker
def check_br_date(value: str) -> str:
	"""Validate a ``DD/MM/AAAA`` string and return it unchanged.

	Parameters
	----------
	value : str
		The date text.

	Returns
	-------
	str
		The same text, once it names a real date.
	"""
	parse_br_date(value)
	return value


@type_checker
def check_month_year(value: str) -> str:
	"""Validate a ``MM/AAAA`` competence and return it unchanged.

	Parameters
	----------
	value : str
		The competence text.

	Returns
	-------
	str
		The same text, once the month is 01-12 and the year is 1900 or later.

	Raises
	------
	ValueError
		If the shape is wrong, the month is out of range or the year is before 1900.
	"""
	if not _MONTH_YEAR_RE.fullmatch(value):
		raise ValueError("competence must follow MM/AAAA")
	if datetime.strptime(value, "%m/%Y").year < _MIN_YEAR:  # noqa: DTZ007
		raise ValueError(f"year must be >= {_MIN_YEAR}")
	return value


@type_checker
def check_cvm_code(value: str) -> str:
	"""Validate a representative CVM code: up to 5 digits, no zero filler.

	Parameters
	----------
	value : str
		Digits only.

	Returns
	-------
	str
		The same text.

	Raises
	------
	ValueError
		If it is not 1 to 5 digits starting with 1-9.
	"""
	if not _CVM_CODE_RE.fullmatch(value):
		raise ValueError("CVM code must be 1 to 5 digits with no leading zero")
	return value


@type_checker
def check_participant_code(value: str) -> str:
	"""Validate a participant code in the exact ``AAAAA.BBBBBB.CCCCCC.T-DV`` layout.

	The page warns that any other formatting makes CVM reject the file. The check digit is only
	checked as one digit: the page does not publish its algorithm.

	Parameters
	----------
	value : str
		The participant code.

	Returns
	-------
	str
		The same text.

	Raises
	------
	ValueError
		If the layout differs (field width, zero filler, account type other than 0/1).
	"""
	if not _PARTICIPANT_RE.fullmatch(value):
		raise ValueError("code must follow AAAAA.BBBBBB.CCCCCC.T-DV (no leading zeros, T is 0|1)")
	return value


@type_checker
def whole_amount(value: object) -> int:
	"""Coerce an amount to ``int``; the page says every amount is "numérico e inteiro".

	Accepts ``int``, ``str`` of digits and a ``Decimal`` with no fractional part. A ``float``
	is refused (its binary error is already baked in), as are ``bool``, NaN, infinity and any
	fractional value: truncating money silently would hide a caller bug.

	Parameters
	----------
	value : object
		Raw input.

	Returns
	-------
	int
		The whole amount.

	Raises
	------
	ValueError
		If the value is not a whole number of an accepted type.
	"""
	if isinstance(value, bool) or not isinstance(value, Decimal | int | str):
		raise ValueError(f"expected int, Decimal or str, got {type(value).__name__}")
	if isinstance(value, str):
		if not _WHOLE_RE.fullmatch(value):
			raise ValueError("amount must be a whole number written in digits")
		return int(value)
	if isinstance(value, Decimal):
		if not value.is_finite() or value != value.to_integral_value():
			raise ValueError("amount must be a finite whole number")
		return int(value)
	return value
