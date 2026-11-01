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
import xml.etree.ElementTree as ET

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
_XML_DECLARATION = '<?xml version="1.0" encoding="windows-1252"?>\n'
# Cc controls except tab (09) and newline (0A).
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")
# Length caps the spec does not state for a code field: a conservative, documented assumption.
CODE_MAX_LEN = 50


@type_checker
def ensure(ok: bool, message: str) -> None:
	"""Raise ``ValueError(message)`` unless ``ok``.

	Parameters
	----------
	ok : bool
		The condition that must hold.
	message : str
		Error text.

	Raises
	------
	ValueError
		If ``ok`` is false.
	"""
	if not ok:
		raise ValueError(message)


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
	ensure(bool(_DATE_BR_RE.fullmatch(value)), "date must follow DD/MM/AAAA")
	parsed = datetime.strptime(value, "%d/%m/%Y").date()  # noqa: DTZ007
	ensure(parsed.year >= _MIN_YEAR, f"year must be >= {_MIN_YEAR}")
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
	ensure(bool(_MONTH_YEAR_RE.fullmatch(value)), "competence must follow MM/AAAA")
	parsed = datetime.strptime(value, "%m/%Y").date()  # noqa: DTZ007
	ensure(parsed.year >= _MIN_YEAR, f"year must be >= {_MIN_YEAR}")
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
	ensure(
		bool(_COD_PARTIC_RE.fullmatch(value)),
		"participant code must follow AAAAA.BBBBBB.CCCCCC.T-DV, no zero filler",
	)
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
	ensure(
		bool(_CVM_CODE_RE.fullmatch(value)), "CVM code must be 1 to 5 digits with no leading zero"
	)
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
	ensure(
		bool(_CNPJ_SHAPE_RE.fullmatch(value)),
		"CNPJ must be 14 characters, bare or masked as NN.NNN.NNN/NNNN-NN",
	)
	ensure(is_valid_cnpj(value), f"invalid CNPJ: {value!r}")
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
	ensure(
		bool(_CPF_SHAPE_RE.fullmatch(value)) and is_valid_cpf(value),
		f"invalid CPF for PF: {value!r}",
	)
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
	ensure(
		len(value) <= CODE_MAX_LEN and bool(_CODE_RE.fullmatch(value)),
		f"code must be 1 to {CODE_MAX_LEN} characters of [0-9A-Za-z._/-]",
	)
	return value


@type_checker
def _ensure_encodable(value: str) -> None:
	"""Require ``value`` to be encodable in windows-1252.

	Parameters
	----------
	value : str
		The text.

	Raises
	------
	ValueError
		Naming the first character windows-1252 cannot encode.
	"""
	try:
		value.encode(_XML_TEXT_ENCODING)
	except UnicodeEncodeError as exc:
		raise ValueError(
			f"character {value[exc.start]!r} is not encodable in windows-1252"
		) from exc


@type_checker
def _to_decimal(value: object, label: str, expected: str) -> Decimal:
	"""Coerce an ``int``/``str``/``Decimal`` to ``Decimal``; refuse everything else.

	Parameters
	----------
	value : object
		Raw input.
	label : str
		Field kind for the error message (``"decimal"`` or ``"integer"``).
	expected : str
		Accepted types, for the error message.

	Returns
	-------
	Decimal
		The parsed value (possibly NaN or infinite; the caller checks).

	Raises
	------
	ValueError
		If the type is a float, bool or unsupported, or the text is not a number.
	"""
	ensure(
		not isinstance(value, bool) and isinstance(value, Decimal | int | str),
		f"expected {expected}, got {type(value).__name__}",
	)
	try:
		return value if isinstance(value, Decimal) else Decimal(str(value))
	except InvalidOperation as exc:
		raise ValueError(f"invalid {label} value: {value!r}") from exc


@type_checker
def _truncate(value: Decimal, quantum: Decimal) -> Decimal:
	"""Truncate toward zero at ``quantum``; ``-0`` becomes ``0``.

	Parameters
	----------
	value : Decimal
		A finite value.
	quantum : Decimal
		The scale, e.g. ``Decimal("0.01")``.

	Returns
	-------
	Decimal
		The truncated value.

	Raises
	------
	ValueError
		If the value has too many digits to quantize.
	"""
	try:
		truncated = value.quantize(quantum, rounding=ROUND_DOWN)
	except InvalidOperation as exc:
		raise ValueError(f"invalid decimal value: {value!r}") from exc
	return truncated if truncated else truncated.copy_abs()


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
		ensure(bool(value.strip()), "text must not be blank")
		ensure(len(value) <= max_len, f"text must have at most {max_len} characters")
		ensure(_CONTROL_RE.search(value) is None, "control character is not allowed")
		_ensure_encodable(value)
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
		as_decimal = _to_decimal(value, "decimal", "Decimal, int or str")
		ensure(as_decimal.is_finite(), "value must be finite")
		return _truncate(as_decimal, quantum)

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
	as_decimal = _to_decimal(value, "integer", "int, Decimal or str")
	ensure(
		as_decimal.is_finite() and as_decimal == as_decimal.to_integral_value(),
		"value must be a whole number",
	)
	return int(as_decimal)


@type_checker
def finish_xml(root: ET.Element, output_path: str | None) -> str | None:
	"""Indent ``root``, prepend the declaration, then return or write the document.

	Parameters
	----------
	root : ET.Element
		The ``DOC_ARQ`` element.
	output_path : str or None
		Destination file; ``None`` returns the text instead.

	Returns
	-------
	str or None
		The XML when ``output_path`` is ``None``, else ``None``.
	"""
	ET.indent(root, space="    ")
	xml_str = _XML_DECLARATION + ET.tostring(root, encoding="unicode", short_empty_elements=False)
	if output_path is None:
		return xml_str
	write_xml_file(output_path, xml_str)
	return None
