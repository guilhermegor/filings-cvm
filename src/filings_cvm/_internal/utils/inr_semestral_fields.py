r"""Strict field validators for the Informe Semestral de INR schemas (Parte I and Parte II).

Pure functions (no I/O) that ``schemas/inr_semestral.py`` composes into ``Annotated`` field types.
They live here because ``schemas/`` holds only Pydantic models (``bin/check_schemas.py``).

Every check uses ``re.fullmatch`` with ``[0-9]``: a ``$`` anchor accepts a trailing newline and
``\d`` accepts non-ASCII digits, and either would let a malformed value reach the XML.
"""

from collections.abc import Callable
from datetime import date, datetime
from decimal import ROUND_DOWN, Decimal, InvalidOperation
import re
import unicodedata

from filings_cvm._internal.utils.br_identifiers import (
	is_valid_cnpj,
	is_valid_cpf,
	unmask_cnpj,
	unmask_cpf,
)
from filings_cvm._internal.utils.typing import type_checker


_DATE_BR_RE = re.compile(r"[0-9]{2}/[0-9]{2}/[0-9]{4}")
_MONTH_YEAR_RE = re.compile(r"[0-9]{2}/[0-9]{4}")
# AAAAA.BBBBBB.CCCCCC.T-DV with no zero filler (a lone 0 is allowed); T is 0 or 1.
_COD_PARTIC_RE = re.compile(
	r"(0|[1-9][0-9]{0,4})\.(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})\.[01]-[0-9]"
)
_CVM_CODE_RE = re.compile(r"[1-9][0-9]{0,4}")
_CNPJ_SHAPE_RE = re.compile(
	r"[0-9A-Z]{12}[0-9]{2}|[0-9A-Z]{2}\.[0-9A-Z]{3}\.[0-9A-Z]{3}/[0-9A-Z]{4}-[0-9]{2}"
)
_CPF_SHAPE_RE = re.compile(r"[0-9]{11}|[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}")
_CODE_RE = re.compile(r"[0-9A-Za-z._/-]+")
_MIN_YEAR = 1900
_XML_TEXT_ENCODING = "windows-1252"
_ALLOWED_CONTROLS = frozenset({"\n", "\t"})
# Length caps the spec does not state for a code field: a conservative, documented assumption.
CODE_MAX_LEN = 50


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
		The same text.

	Raises
	------
	ValueError
		If the shape is wrong, the month is not 01-12 or the year is before 1900.
	"""
	if not _MONTH_YEAR_RE.fullmatch(value):
		raise ValueError("competence must follow MM/AAAA")
	parsed = datetime.strptime(value, "%m/%Y").date()  # noqa: DTZ007
	if parsed.year < _MIN_YEAR:
		raise ValueError(f"year must be >= {_MIN_YEAR}")
	return value


@type_checker
def check_cod_partic(value: str) -> str:
	"""Validate a participant code ``AAAAA.BBBBBB.CCCCCC.T-DV`` and return it unchanged.

	Parameters
	----------
	value : str
		The code, formatted exactly as the standard states.

	Returns
	-------
	str
		The same text.

	Raises
	------
	ValueError
		If it does not have the shape (segments up to 5/6/6 digits without zero filler, account
		type 0 or 1, one check digit).
	"""
	if not _COD_PARTIC_RE.fullmatch(value):
		raise ValueError("participant code must follow AAAAA.BBBBBB.CCCCCC.T-DV, no zero filler")
	return value


@type_checker
def check_cvm_code(value: str) -> str:
	"""Validate a representative CVM code (up to 5 digits, no zero filler).

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
		If it is not 1-5 digits starting with 1-9.
	"""
	if not _CVM_CODE_RE.fullmatch(value):
		raise ValueError("CVM code must be 1 to 5 digits with no leading zero")
	return value


@type_checker
def to_cnpj_field(value: str) -> str:
	"""Check a CNPJ and return it as the XML carries it: unmasked, leading zeros omitted.

	The shape is checked before the library's unmasking (which drops every non-alphanumeric
	character) so stray separators or whitespace cannot be laundered into a valid number.

	Parameters
	----------
	value : str
		A bare or masked CNPJ.

	Returns
	-------
	str
		The CNPJ without punctuation and without leading zeros.

	Raises
	------
	ValueError
		If the shape is wrong or the check digits fail.
	"""
	if not _CNPJ_SHAPE_RE.fullmatch(value):
		raise ValueError("CNPJ must be 14 characters, bare or masked as NN.NNN.NNN/NNNN-NN")
	if not is_valid_cnpj(value):
		raise ValueError(f"invalid CNPJ: {value!r}")
	return unmask_cnpj(value).lstrip("0")


@type_checker
def to_person_doc(tp_pessoa: str, value: str) -> str:
	"""Check a CPF (``PF``) or CNPJ (``PJ``) and return it unmasked, leading zeros omitted.

	Parameters
	----------
	tp_pessoa : str
		``"PF"`` or ``"PJ"``.
	value : str
		The document, bare or masked.

	Returns
	-------
	str
		The document without punctuation and without leading zeros.

	Raises
	------
	ValueError
		If the shape or the check digits do not fit the person type.
	"""
	if tp_pessoa == "PJ":
		return to_cnpj_field(value)
	if not _CPF_SHAPE_RE.fullmatch(value) or not is_valid_cpf(value):
		raise ValueError(f"invalid CPF for PF: {value!r}")
	return unmask_cpf(value).lstrip("0")


@type_checker
def check_code(value: str) -> str:
	"""Validate a non-empty code field (asset, SELIC or exchange-ticker code).

	Parameters
	----------
	value : str
		The code.

	Returns
	-------
	str
		The same text.

	Raises
	------
	ValueError
		If it is empty, longer than ``CODE_MAX_LEN`` or holds characters outside
		``[0-9A-Za-z._/-]``.
	"""
	if len(value) > CODE_MAX_LEN or not _CODE_RE.fullmatch(value):
		raise ValueError(f"code must be 1 to {CODE_MAX_LEN} characters of [0-9A-Za-z._/-]")
	return value


@type_checker
def text_field(max_len: int) -> Callable[[str], str]:
	"""Build a validator for free text of at most ``max_len`` windows-1252 characters.

	Rejects blank text, control characters other than newline and tab, and characters
	windows-1252 cannot encode (they would otherwise fail, or wipe the file, at write time).

	Parameters
	----------
	max_len : int
		Maximum length stated by the standard.

	Returns
	-------
	Callable[[str], str]
		The validator.
	"""

	@type_checker
	def _check(value: str) -> str:
		"""Validate one text value.

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
			If it is blank, too long, holds a control character or is not encodable.
		"""
		if not value.strip():
			raise ValueError("text must not be blank")
		if len(value) > max_len:
			raise ValueError(f"text must have at most {max_len} characters")
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

	return _check


@type_checker
def strict_decimal(places: int) -> Callable[[object], Decimal]:
	"""Build a before-validator coercing to ``Decimal`` at a fixed scale (``ROUND_DOWN``).

	Accepts ``Decimal``, ``int`` and ``str`` only: a ``float`` is refused (its binary error is
	already baked in) and so are ``bool``, NaN and infinity. Excess places are truncated toward
	zero, and ``-0`` becomes ``0``.

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
def format_decimal(value: Decimal, places: int) -> str:
	"""Render a ``Decimal`` the way the XML carries it: fixed scale, comma separator.

	Parameters
	----------
	value : Decimal
		A value already truncated to ``places``.
	places : int
		Decimal places to render.

	Returns
	-------
	str
		For example ``"12,340000"``.
	"""
	return f"{value:.{places}f}".replace(".", ",")


@type_checker
def write_xml_file(path: str, text: str) -> None:
	"""Encode ``text`` to windows-1252 *before* opening ``path``, then write the bytes.

	Encoding first means an unencodable character raises with the destination untouched,
	instead of truncating an existing file.

	Parameters
	----------
	path : str
		Destination file.
	text : str
		The XML document.
	"""
	payload = text.encode(_XML_TEXT_ENCODING)
	with open(path, "wb") as handle:  # noqa: PTH123
		handle.write(payload)


@type_checker
def strict_int(value: object) -> int:
	"""Accept an integer or an integer-valued ``str``/``Decimal``; refuse ``float`` and ``bool``.

	Parameters
	----------
	value : object
		Raw input.

	Returns
	-------
	int
		The integer value.

	Raises
	------
	ValueError
		If the value is a float, bool, unsupported type, or has a fractional part.
	"""
	if isinstance(value, bool) or not isinstance(value, Decimal | int | str):
		raise ValueError(f"expected int, Decimal or str, got {type(value).__name__}")
	try:
		as_decimal = value if isinstance(value, Decimal) else Decimal(value)
	except InvalidOperation as exc:
		raise ValueError(f"invalid integer value: {value!r}") from exc
	if not as_decimal.is_finite() or as_decimal != as_decimal.to_integral_value():
		raise ValueError("value must be a whole number")
	return int(as_decimal)
