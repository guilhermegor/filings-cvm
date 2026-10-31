r"""Strict field validators shared by the CVM XML-standard schemas.

Pure functions (no I/O) that a schema composes into ``Annotated`` field types: real calendar
dates, bounded decimals that refuse ``float``, XML-safe text, and the few digit-string shapes the
standards use. They live here, not in a ``schemas/`` module, because that directory holds only
Pydantic models (``bin/check_schemas.py``).

Every check uses ``re.fullmatch`` with ``[0-9]`` — a ``$`` anchor accepts a trailing newline and
``\d`` accepts non-ASCII digits, and both would let a malformed value reach the XML.
"""

from collections.abc import Callable, Sequence
from datetime import date, datetime
from decimal import ROUND_DOWN, Decimal, InvalidOperation
import re
import unicodedata

from filings_cvm._internal.utils.typing import type_checker


_DATE_BR_RE = re.compile(r"[0-9]{2}/[0-9]{2}/[0-9]{4}")
_MONTH_YEAR_RE = re.compile(r"[0-9]{2}/[0-9]{4}")
_HHMM_RE = re.compile(r"([01][0-9]|2[0-3]):[0-5][0-9]")
# No zero filler, so the first digit is 1-9; 19 digits is the width of a signed 64-bit "long".
# Bare or masked CNPJ (letters allowed for the 2026 alphanumeric form). The library's own
# unmasking drops every non-alphanumeric character, so shape is checked before it runs.
_CNPJ_SHAPE_RE = re.compile(
	r"[0-9A-Z]{12}[0-9]{2}|[0-9A-Z]{2}\.[0-9A-Z]{3}\.[0-9A-Z]{3}/[0-9A-Z]{4}-[0-9]{2}"
)
_LONG_DIGITS_RE = re.compile(r"[1-9][0-9]{0,18}")
_LONG_MAX = 9223372036854775807
# Earliest year a CVM filing can plausibly carry; rejects 0001-style typos.
_MIN_YEAR = 1900
_XML_TEXT_ENCODING = "windows-1252"
_ALLOWED_CONTROLS = frozenset({"\n", "\t"})


@type_checker
def parse_br_date(value: str) -> date:
	"""Parse a ``DD/MM/AAAA`` string into a real calendar date.

	Parameters
	----------
	value : str
		The date text, zero-padded exactly as the standards state it.

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
		The same text, once month is 01-12 and the year is 1900 or later.

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
	return value


@type_checker
def check_hhmm(value: str) -> str:
	"""Validate a ``HH:MM`` time of day and return it unchanged.

	Parameters
	----------
	value : str
		The time text.

	Returns
	-------
	str
		The same text.

	Raises
	------
	ValueError
		If it is not a 24-hour ``HH:MM`` time.
	"""
	if not _HHMM_RE.fullmatch(value):
		raise ValueError("time must follow HH:MM (00:00 to 23:59)")
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


@type_checker
def check_long_digits(value: str) -> str:
	"""Validate a digits-only ``long`` (a phone number) with no zero filler.

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
		If it has a non-digit, a leading zero, or does not fit a signed 64-bit integer.
	"""
	if not _LONG_DIGITS_RE.fullmatch(value) or int(value) > _LONG_MAX:
		raise ValueError("must be digits only, no leading zero, and fit a 64-bit long")
	return value


@type_checker
def check_xml_text(value: str) -> str:
	"""Validate free text for a windows-1252 XML document and return it unchanged.

	Rejects blank text, control characters other than newline and tab (illegal or silently
	rewritten in XML 1.0), and characters windows-1252 cannot encode.

	Parameters
	----------
	value : str
		The text.

	Returns
	-------
	str
		The same text.

	Raises
	------
	ValueError
		If the text is blank, holds a control character, or is not windows-1252 encodable.
	"""
	if not value.strip():
		raise ValueError("text must not be blank")
	for char in value:
		if unicodedata.category(char) == "Cc" and char not in _ALLOWED_CONTROLS:
			raise ValueError(f"control character U+{ord(char):04X} is not allowed")
	try:
		value.encode(_XML_TEXT_ENCODING)
	except UnicodeEncodeError as exc:
		raise ValueError(
			f"character {value[exc.start]!r} is not encodable in windows-1252"
		) from exc
	return value


@type_checker
def strict_decimal(places: int) -> Callable[[object], Decimal]:
	"""Build a before-validator that coerces to ``Decimal`` at a fixed scale (ROUND_DOWN).

	Accepts ``Decimal``, ``int`` and ``str`` only. A ``float`` is refused (its binary error is
	already baked in before the value arrives) and so is ``bool``, NaN and infinity. Excess
	decimal places are truncated toward zero, never rounded, and a result of ``-0.00`` becomes
	``0.00``.

	Parameters
	----------
	places : int
		Decimal places the field is serialised with.

	Returns
	-------
	Callable[[object], Decimal]
		The validator.
	"""
	quantum = Decimal(1).scaleb(-places)

	@type_checker
	def _coerce(value: object) -> Decimal:
		"""Coerce one incoming value.

		Parameters
		----------
		value : object
			Raw input.

		Returns
		-------
		Decimal
			The value truncated to the bound scale.

		Raises
		------
		ValueError
			If the value is a float, bool or unsupported type, or is not a finite decimal.
		"""
		if isinstance(value, bool) or not isinstance(value, Decimal | int | str):
			raise ValueError(f"expected Decimal, int or str, got {type(value).__name__}")
		try:
			as_decimal = value if isinstance(value, Decimal) else Decimal(value)
			if not as_decimal.is_finite():
				raise ValueError("value must be finite")
			truncated = as_decimal.quantize(quantum, rounding=ROUND_DOWN)
		except InvalidOperation as exc:
			raise ValueError(f"invalid decimal value: {value!r}") from exc
		return abs(truncated) if truncated == 0 else truncated

	return _coerce


@type_checker
def require_unique_funds(cnpjs: Sequence[str]) -> None:
	"""Reject a file that reports the same fund twice.

	Parameters
	----------
	cnpjs : Sequence[str]
		The ``CNPJ_FUNDO`` of each ``ROW_INFORME``.

	Raises
	------
	ValueError
		If a CNPJ repeats.
	"""
	seen: set[str] = set()
	for cnpj in cnpjs:
		if cnpj in seen:
			raise ValueError(f"fund {cnpj} appears in more than one ROW_INFORME")
		seen.add(cnpj)
