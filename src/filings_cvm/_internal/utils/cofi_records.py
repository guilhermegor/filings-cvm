"""COFI fixed-width record layer — shared by the COFI 4016 and COFI 4010 writers.

Implements the record layouts of the CVM page ``PadraoCOFI.aspx`` ("Padrão COFI 4010 e
COFI 4016", https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoCOFI.aspx): a
71-column text file (extension ``.cvm``) made of a control header, one record per account
and a control footer. Only what both documents share lives here — field padding, the
account check digit, the signed 18-digit amount columns, the three record builders and the
byte-level encode/write. Document-specific rules (which document code, which consistency
checks) belong to the writer of each document.

Assumptions the page does not state, made once here so every writer shares them:

* **Amount scale** — the 18-digit columns carry an implied decimal point with
  :data:`AMOUNT_SCALE` (2) places, truncated, never rounded.
* **Account field** — the 10-position ``Conta`` holds the 8-character account code
  (7-digit body + check digit) right-aligned and zero-filled.
* **Line terminator** — :data:`LINE_TERMINATOR` (CRLF) after every record.
* **Encoding** — ASCII by default; the page also names EBCDIC (``cp037``) for the
  control-record identifiers (``#``/``@`` are ``0x7B``/``0x7C`` there).
"""

from decimal import ROUND_DOWN, Decimal, InvalidOperation
from pathlib import Path
import re

from filings_cvm._internal.utils.typing import type_checker


RECORD_WIDTH = 71
LINE_TERMINATOR = "\r\n"
AMOUNT_SCALE = 2
AMOUNT_DIGITS = 18
ACCOUNT_FIELD_WIDTH = 10
ACCOUNT_CODE_LENGTH = 8
MAX_RECORD_COUNT = 999_999
# Mod-10 check-digit weights, measured against all 479 accounts of the COFI plan.
_CHECK_DIGIT_WEIGHTS = (3, 1, 7, 3, 1, 7, 3)
_CNPJ_LENGTH = 14
_ENCODINGS = {"ascii": "ascii", "ebcdic": "cp037"}
_RE_DIGITS = re.compile(r"[0-9]+")


@type_checker
def _require(condition: bool, message: str) -> None:
	"""Raise ``ValueError(message)`` unless ``condition`` holds.

	Parameters
	----------
	condition : bool
		The invariant being checked.
	message : str
		Error text used when it does not hold.

	Raises
	------
	ValueError
		If ``condition`` is false.
	"""
	if not condition:
		raise ValueError(message)


@type_checker
def numeric_field(value: int | str, width: int) -> str:
	"""Render a numeric (``9``) field: digits only, right-aligned, zero-filled.

	Parameters
	----------
	value : int or str
		A non-negative integer or a string of ASCII digits.
	width : int
		Field width in columns.

	Returns
	-------
	str
		Exactly ``width`` digits.

	Raises
	------
	ValueError
		If the value is negative, not all ASCII digits, or wider than the field.
	"""
	text = str(value)
	_require(
		not isinstance(value, bool) and _RE_DIGITS.fullmatch(text) is not None,
		f"numeric field needs non-negative digits, got {value!r}",
	)
	_require(len(text) <= width, f"value {text!r} does not fit a {width}-column field")
	return text.zfill(width)


@type_checker
def filler(width: int) -> str:
	"""Return ``width`` blanks (an ``X`` filler field).

	Parameters
	----------
	width : int
		Field width in columns.

	Returns
	-------
	str
		``width`` spaces.
	"""
	return " " * width


@type_checker
def account_check_digit(body: str) -> int:
	"""Compute the check digit of a 7-digit account body.

	Parameters
	----------
	body : str
		The seven leading digits of the account code.

	Returns
	-------
	int
		The check digit: ``(-sum(weight * digit)) mod 10`` with weights ``3,1,7`` cycling.

	Raises
	------
	ValueError
		If ``body`` is not exactly seven ASCII digits.
	"""
	if len(body) != len(_CHECK_DIGIT_WEIGHTS) or _RE_DIGITS.fullmatch(body) is None:
		raise ValueError(f"account body must be 7 digits, got {body!r}")
	total = sum(
		int(digit) * weight for digit, weight in zip(body, _CHECK_DIGIT_WEIGHTS, strict=True)
	)
	return (-total) % 10


@type_checker
def is_valid_account_code(code: str) -> bool:
	"""Tell whether an 8-character account code has a correct check digit.

	Parameters
	----------
	code : str
		Candidate code (7-digit body + check digit).

	Returns
	-------
	bool
		``True`` for exactly 8 ASCII digits whose last is the correct check digit.
	"""
	if len(code) != ACCOUNT_CODE_LENGTH or _RE_DIGITS.fullmatch(code) is None:
		return False
	return account_check_digit(code[:-1]) == int(code[-1])


@type_checker
def account_code_with_check_digit(body: str) -> str:
	"""Append the check digit to a 7-digit account body.

	Parameters
	----------
	body : str
		The seven leading digits of the account code.

	Returns
	-------
	str
		The 8-character account code.
	"""
	return f"{body}{account_check_digit(body)}"


@type_checker
def amount_to_digits(value: Decimal) -> tuple[str, str]:
	"""Split a decimal amount into its 18-digit absolute value and sign character.

	Parameters
	----------
	value : Decimal
		Amount with at most :data:`AMOUNT_SCALE` decimal places; floats are not accepted.

	Returns
	-------
	tuple[str, str]
		``(digits, sign)``: 18 zero-filled digits of ``abs(value)`` scaled by 10**2, and
		``"+"`` or ``"-"``.

	Raises
	------
	ValueError
		If the value is not finite, has more places than the scale, or overflows 18 digits.
	"""
	_require(value.is_finite(), f"amount must be finite, got {value!r}")
	scaled = value.scaleb(AMOUNT_SCALE)
	_require(
		scaled == scaled.to_integral_value(),
		f"amount {value} has more than {AMOUNT_SCALE} decimal places",
	)
	digits = numeric_field(int(abs(scaled)), AMOUNT_DIGITS)
	return digits, "-" if value < 0 else "+"


@type_checker
def decimal_amount_input(value: Decimal | str | int | float | None) -> Decimal:
	"""Coerce an incoming amount to a ``Decimal`` truncated to the amount scale.

	A before-validator for amount fields: ``float`` and ``bool`` are refused outright
	(a binary float has already lost the fraction), strings and ints are read exactly.

	Parameters
	----------
	value : Decimal, str, int, float or None
		Raw amount.

	Returns
	-------
	Decimal
		The amount truncated (``ROUND_DOWN``) to :data:`AMOUNT_SCALE` places.

	Raises
	------
	ValueError
		If ``value`` is a ``float``, a ``bool`` or ``None``, or is not a finite decimal.
	"""
	_require(
		not (value is None or isinstance(value, bool | float)),
		f"amount must be Decimal, str or int, never {type(value).__name__}",
	)
	try:
		amount = value if isinstance(value, Decimal) else Decimal(str(value))
	except InvalidOperation as exc:
		raise ValueError(f"invalid amount: {value!r}") from exc
	_require(amount.is_finite(), f"amount must be finite, got {value!r}")
	return amount.quantize(Decimal(1).scaleb(-AMOUNT_SCALE), rounding=ROUND_DOWN)


@type_checker
def header_record(document_code: str, cnpj: str, competence: str) -> str:
	"""Build the control header record (positions 1-71).

	Parameters
	----------
	document_code : str
		4-digit document code (``"4016"`` for the COFI Balanço).
	cnpj : str
		Fund CNPJ, 14 bare digits.
	competence : str
		Competence as ``MMAAAA`` (6 digits).

	Returns
	-------
	str
		The 71-column record (no terminator).

	Raises
	------
	ValueError
		If a field has the wrong shape.
	"""
	_require(len(cnpj) == _CNPJ_LENGTH, f"CNPJ must have {_CNPJ_LENGTH} digits, got {cnpj!r}")
	_require(len(competence) == len("MMAAAA"), f"competence must be MMAAAA, got {competence!r}")
	record = (
		"#C1"
		+ numeric_field(document_code, 4)
		+ numeric_field(cnpj, _CNPJ_LENGTH)
		+ filler(8)
		+ numeric_field(competence, 6)
		+ filler(36)
	)
	return _checked_width(record)


@type_checker
def account_record(code: str, total: Decimal, up_to_90: Decimal, after_90: Decimal) -> str:
	"""Build one account record (positions 1-71).

	Parameters
	----------
	code : str
		8-character account code with a valid check digit.
	total : Decimal
		Total column.
	up_to_90 : Decimal
		Realizável/Exigível até 90 dias column.
	after_90 : Decimal
		Realizável/Exigível após 90 dias column.

	Returns
	-------
	str
		The 71-column record (no terminator).

	Raises
	------
	ValueError
		If the code has a wrong check digit or an amount does not fit its column.
	"""
	_require(is_valid_account_code(code), f"invalid account code: {code!r}")
	record = numeric_field(code, ACCOUNT_FIELD_WIDTH) + filler(4)
	for amount in (total, up_to_90, after_90):
		digits, sign = amount_to_digits(amount)
		record += digits + sign
	return _checked_width(record)


@type_checker
def footer_record(record_count: int) -> str:
	"""Build the control footer record (positions 1-71).

	Parameters
	----------
	record_count : int
		Total records in the file, control records included.

	Returns
	-------
	str
		The 71-column record (no terminator).

	Raises
	------
	ValueError
		If the count is negative or exceeds six digits.
	"""
	return _checked_width("@1" + numeric_field(record_count, 6) + filler(63))


@type_checker
def _checked_width(record: str) -> str:
	"""Return ``record`` after asserting it is exactly :data:`RECORD_WIDTH` columns.

	Parameters
	----------
	record : str
		A built record.

	Returns
	-------
	str
		The same record.

	Raises
	------
	ValueError
		If the record is not 71 columns wide (a layout bug).
	"""
	if len(record) != RECORD_WIDTH:
		raise ValueError(f"record is {len(record)} columns wide, layout needs {RECORD_WIDTH}")
	return record


@type_checker
def render_file(records: list[str]) -> str:
	"""Join records into the file text, each followed by the line terminator.

	Parameters
	----------
	records : list[str]
		Header/account/footer records in file order.

	Returns
	-------
	str
		The file content.
	"""
	return "".join(record + LINE_TERMINATOR for record in records)


@type_checker
def write_file(content: str, output_path: str, encoding: str = "ascii") -> None:
	"""Encode ``content`` fully, then write the bytes in one go.

	Encoding happens before the file is opened, so a character the encoding cannot
	represent raises without truncating an existing file.

	Parameters
	----------
	content : str
		The rendered file text.
	output_path : str
		Destination path.
	encoding : str, optional
		``"ascii"`` or ``"ebcdic"`` (code page 037), by default ``"ascii"``.

	Raises
	------
	ValueError
		If ``encoding`` is unknown or ``content`` is not representable in it.
	"""
	_require(
		encoding in _ENCODINGS, f"encoding must be one of {sorted(_ENCODINGS)}, got {encoding!r}"
	)
	try:
		payload = content.encode(_ENCODINGS[encoding])
	except UnicodeEncodeError as exc:
		raise ValueError(f"content not representable in {encoding}: {exc}") from exc
	Path(output_path).write_bytes(payload)
