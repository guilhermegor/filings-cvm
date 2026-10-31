"""Fixed-width record layer shared by the COFI ``.cvm`` submission writers.

CVM publishes the COFI 4010 (Balancete) and COFI 4016 (Balanço) standards on one page,
``PadraoCOFI.aspx``: a text file of **71-position records** — a control header, one
record per account, and a control footer. This module holds only what the two share:
the three record builders, the amount codec, and the fixed-width field helpers. The
document-specific models and writers live elsewhere.

Amounts are 18 digits holding the **absolute** value, followed by a one-character
sign. The page states no decimal scale; this layer assumes **2 implied decimals**
(``"12.34"`` is written ``000000000000001234``), truncated toward zero.
"""

from decimal import ROUND_DOWN, Decimal, InvalidOperation

from filings_cvm._internal.utils.typing import type_checker


RECORD_LEN = 71
AMOUNT_DIGITS = 18
AMOUNT_SCALE = 2
# Footer record count is 6 digits, so no file may hold more records than this.
MAX_RECORDS = 999_999
# 10**(18 - scale): the (exclusive) ceiling on an absolute amount.
_AMOUNT_CEILING = Decimal(10) ** (AMOUNT_DIGITS - AMOUNT_SCALE)
_QUANTUM = Decimal(1).scaleb(-AMOUNT_SCALE)


@type_checker
def parse_cofi_amount(value: object) -> Decimal:
	"""Coerce a raw amount to a ``Decimal`` truncated to 2 places, refusing ``float``.

	A binary float cannot carry a decimal fraction exactly, so converting one would
	launder an already-lossy value; it is rejected instead (pass ``str`` or ``Decimal``).

	Parameters
	----------
	value : object
		A ``Decimal``, ``str`` or ``int``.

	Returns
	-------
	Decimal
		The value truncated toward zero to 2 decimal places.

	Raises
	------
	ValueError
		If the value is a ``float``/``bool``, not a finite number, or its absolute
		value does not fit the 18-digit column (16 integer digits).
	"""
	if isinstance(value, float | bool) or not isinstance(value, Decimal | str | int):
		raise ValueError(f"amount must be Decimal, str or int, never {type(value).__name__}")
	try:
		as_decimal = value if isinstance(value, Decimal) else Decimal(value)
	except (InvalidOperation, ValueError) as exc:
		raise ValueError(f"invalid decimal amount: {value!r}") from exc
	if not as_decimal.is_finite() or abs(as_decimal) >= _AMOUNT_CEILING:
		raise ValueError(f"amount out of range for an 18-digit column: {value!r}")
	return as_decimal.quantize(_QUANTUM, rounding=ROUND_DOWN)


@type_checker
def format_amount(value: Decimal) -> str:
	"""Render an amount as its 18 absolute digits plus a sign character.

	Parameters
	----------
	value : Decimal
		An amount already truncated to 2 places (see :func:`parse_cofi_amount`).

	Returns
	-------
	str
		19 characters: 18 zero-padded digits then ``"+"`` (zero or positive) or ``"-"``.
	"""
	int_cents = int(abs(value).scaleb(AMOUNT_SCALE))
	sign = "-" if value < 0 else "+"
	return f"{int_cents:0{AMOUNT_DIGITS}d}{sign}"


@type_checker
def _fixed(text: str, width: int) -> str:
	"""Left-justify ``text`` into exactly ``width`` characters.

	Parameters
	----------
	text : str
		Content to place.
	width : int
		Field width.

	Returns
	-------
	str
		``text`` padded with spaces to ``width``.

	Raises
	------
	ValueError
		If ``text`` is longer than ``width``.
	"""
	if len(text) > width:
		raise ValueError(f"{text!r} does not fit a {width}-character field")
	return text.ljust(width)


@type_checker
def _checked(record: str) -> str:
	"""Assert a built record is exactly 71 positions.

	Parameters
	----------
	record : str
		The assembled record.

	Returns
	-------
	str
		``record`` unchanged.

	Raises
	------
	ValueError
		If the record is not 71 characters (a layout bug, not a user error).
	"""
	if len(record) != RECORD_LEN:
		raise ValueError(f"record has {len(record)} positions, expected {RECORD_LEN}")
	return record


@type_checker
def header_record(cod_doc: str, cnpj: str, competence: str) -> str:
	"""Build the control header record (``#C1``…).

	Parameters
	----------
	cod_doc : str
		4-digit document code (``"4010"`` for Balancete).
	cnpj : str
		Bare 14-digit fund CNPJ.
	competence : str
		Competence in ``MMAAAA`` form.

	Returns
	-------
	str
		The 71-position header record.
	"""
	return _checked(
		"#C1"
		+ _fixed(cod_doc, 4)
		+ _fixed(cnpj, 14)
		+ _fixed("", 8)
		+ _fixed(competence, 6)
		+ _fixed("", 36)
	)


@type_checker
def account_record(
	cod_conta: str, vl_total: Decimal, vl_ate_90: Decimal, vl_apos_90: Decimal
) -> str:
	"""Build one account record.

	Parameters
	----------
	cod_conta : str
		10-position account code with check digit.
	vl_total : Decimal
		Total column.
	vl_ate_90 : Decimal
		Realizável/Exigível up to 90 days column.
	vl_apos_90 : Decimal
		Realizável/Exigível after 90 days column.

	Returns
	-------
	str
		The 71-position account record.
	"""
	return _checked(
		_fixed(cod_conta, 10)
		+ _fixed("", 4)
		+ format_amount(vl_total)
		+ format_amount(vl_ate_90)
		+ format_amount(vl_apos_90)
	)


@type_checker
def footer_record(n_records: int) -> str:
	"""Build the control footer record (``@1``…).

	Parameters
	----------
	n_records : int
		Total records in the file, the header(s) and this footer included.

	Returns
	-------
	str
		The 71-position footer record.

	Raises
	------
	ValueError
		If the count does not fit 6 digits.
	"""
	if not 0 < n_records <= MAX_RECORDS:
		raise ValueError(f"record count {n_records} does not fit the 6-digit field")
	return _checked("@1" + f"{n_records:06d}" + _fixed("", 63))
