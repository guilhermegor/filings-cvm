"""Shared field helpers for CVM XML-standard schemas.

Direction-neutral building blocks reused by every ``_internal/schemas/<standard>.py``
model: a decimal-scale truncation factory (ROUND_DOWN, never inflating a value past
the scale a standard permits) and the Brazilian CPF/CNPJ check-digit validators.

This is a private ``_``-prefixed module — it ships in the wheel but is not part of the
public API. Each standard imports these to declare its own ``Annotated`` field types
and validators, so the truncation/validation logic lives in exactly one place.
"""

from collections.abc import Callable
from decimal import ROUND_DOWN, Decimal, InvalidOperation

from filings_cvm._internal.utils.br_identifiers import (
	is_valid_cnpj,
	is_valid_cpf,
	unmask_cnpj,
	unmask_cpf,
)


# Raw values a decimal before-validator may receive, before coercion to Decimal.
DecimalInput = Decimal | str | int | float | None


def truncate_to_scale(decimal_places: int) -> Callable[[DecimalInput], Decimal | None]:
	"""Build a before-validator that truncates a value to ``decimal_places`` (ROUND_DOWN).

	Truncation (never rounding) is used so a value is never inflated past the scale
	the CVM standard permits; any excess precision is discarded toward zero.

	Parameters
	----------
	decimal_places : int
		Number of decimal places mandated by the CVM standard for the field.

	Returns
	-------
	Callable[[DecimalInput], Optional[Decimal]]
		A validator callable returning the truncated ``Decimal`` (or ``None``).

	Raises
	------
	ValueError
		Raised by the returned validator when a value cannot be interpreted as a
		decimal number.
	"""
	quantum = Decimal(1).scaleb(-decimal_places)

	def _truncate(value: DecimalInput) -> Decimal | None:
		"""Truncate a single incoming value to the bound scale.

		Parameters
		----------
		value : DecimalInput
			Raw value from XML parsing, CSV reload, or direct construction.

		Returns
		-------
		Optional[Decimal]
			Truncated value, or ``None`` when the input is ``None``.

		Raises
		------
		ValueError
			If the value cannot be interpreted as a decimal number.
		"""
		if value is None:
			return None
		try:
			as_decimal = value if isinstance(value, Decimal) else Decimal(str(value))
		except (InvalidOperation, ValueError) as exc:
			raise ValueError(f"invalid decimal value: {value!r}") from exc
		return as_decimal.quantize(quantum, rounding=ROUND_DOWN)

	return _truncate


def validated_cnpj(value: str) -> str:
	"""Normalise and check-digit-validate a CNPJ, returning its bare 14-char form.

	Parameters
	----------
	value : str
		A CNPJ in any shape (masked, padded, or bare).

	Returns
	-------
	str
		The unmasked (bare) CNPJ.

	Raises
	------
	ValueError
		If the value is not a valid CNPJ (failing check digits).
	"""
	if not is_valid_cnpj(value):
		raise ValueError(f"invalid CNPJ: {value!r}")
	return unmask_cnpj(value)


def validate_person_doc(tp_pessoa: str, value: str) -> str:
	"""Validate a document as CPF (PF) or CNPJ (PJ) and return its bare form.

	Parameters
	----------
	tp_pessoa : str
		``"PF"`` (natural person → CPF) or ``"PJ"`` (legal entity → CNPJ).
	value : str
		The document in any shape.

	Returns
	-------
	str
		The unmasked (bare) document.

	Raises
	------
	ValueError
		If the document is not valid for the given person type.
	"""
	if tp_pessoa == "PF":
		if not is_valid_cpf(value):
			raise ValueError(f"invalid CPF for PF: {value!r}")
		return unmask_cpf(value)
	if not is_valid_cnpj(value):
		raise ValueError(f"invalid CNPJ for PJ: {value!r}")
	return unmask_cnpj(value)
