r"""Strict field validators for the Informe Art. 12 Res. CVM 33 (escriturador) XML schema.

Pure functions (no I/O) the schema composes into ``Annotated`` field types. They live here, not in
a ``schemas/`` module, because that directory holds only Pydantic models
(``bin/check_schemas.py``).

Every check uses ``re.fullmatch`` with ``[0-9]``: a ``$`` anchor accepts a trailing newline and
``\d`` accepts non-ASCII digits, and either would let a malformed value reach the XML.
"""

from datetime import date, datetime
import re

from filings_cvm._internal.utils.typing import type_checker


_DATE_BR_RE = re.compile(r"[0-9]{2}/[0-9]{2}/[0-9]{4}")
_MONTH_YEAR_RE = re.compile(r"[0-9]{2}/[0-9]{4}")
# Bare or masked CNPJ (letters allowed for the 2026 alphanumeric form). The library's own
# unmasking drops every non-alphanumeric character, so shape is checked before it runs.
_CNPJ_SHAPE_RE = re.compile(
	r"[0-9A-Z]{12}[0-9]{2}|[0-9A-Z]{2}\.[0-9A-Z]{3}\.[0-9A-Z]{3}/[0-9A-Z]{4}-[0-9]{2}"
)
# Earliest year a CVM filing can plausibly carry; rejects 0001-style typos.
_MIN_YEAR = 1900


@type_checker
def parse_br_date(value: str) -> date:
	"""Parse a ``DD/MM/AAAA`` string into a real calendar date.

	Parameters
	----------
	value : str
		The date text, zero-padded exactly as the standard states it.

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
def parse_month_year(value: str) -> date:
	"""Parse a ``MM/AAAA`` competence into the first day of that month.

	Parameters
	----------
	value : str
		The competence text.

	Returns
	-------
	date
		The first day of the month.

	Raises
	------
	ValueError
		If the shape is wrong, the month is out of range or the year is before 1900.
	"""
	if not _MONTH_YEAR_RE.fullmatch(value):
		raise ValueError("competence must follow MM/AAAA")
	parsed = datetime.strptime(value, "%m/%Y").date()  # noqa: DTZ007
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
		The same text, once it names a real month.
	"""
	parse_month_year(value)
	return value


@type_checker
def check_cnpj_shape(value: str) -> str:
	"""Require the bare 14-character or the ``NN.NNN.NNN/NNNN-NN`` shape of a CNPJ.

	Parameters
	----------
	value : str
		The CNPJ text.

	Returns
	-------
	str
		The same text.

	Raises
	------
	ValueError
		If it has any other shape (stray whitespace, separators or case).
	"""
	if not _CNPJ_SHAPE_RE.fullmatch(value):
		raise ValueError("CNPJ must be 14 characters, bare or masked as NN.NNN.NNN/NNNN-NN")
	return value
