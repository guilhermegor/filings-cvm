r"""Digit-string and e-mail validators for the CVM XML standards (Informe Anual de Auditor).

Companion of ``xml_fields``: pure functions a schema composes into ``Annotated`` field types.
Every check uses ``re.fullmatch`` with ``[0-9]`` — ``$`` accepts a trailing newline and ``\d``
accepts non-ASCII digits, and both would let a malformed value reach the XML.
"""

import re

from filings_cvm._internal.utils.typing import type_checker


_CPF_SHAPE_RE = re.compile(r"[0-9]{11}|[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}")
_CEP_RE = re.compile(r"[0-9]{8}")
_EMAIL_RE = re.compile(r"[^\s@,;<>()\[\]\\\"]+@[^\s@,;<>()\[\]\\\"]+")


@type_checker
def check_cpf_shape(value: str) -> str:
	"""Require the bare 11-digit or the ``NNN.NNN.NNN-NN`` shape of a CPF.

	Parameters
	----------
	value : str
		The CPF text.

	Returns
	-------
	str
		The same text.

	Raises
	------
	ValueError
		If it has any other shape (stray whitespace, separators or letters).
	"""
	if not _CPF_SHAPE_RE.fullmatch(value):
		raise ValueError("CPF must be 11 digits, bare or masked as NNN.NNN.NNN-NN")
	return value


@type_checker
def check_cep(value: str) -> str:
	"""Require a CEP of exactly eight digits (the one field where a leading zero is kept).

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
		If it is not exactly eight ASCII digits.
	"""
	if not _CEP_RE.fullmatch(value):
		raise ValueError("CEP must be exactly 8 digits")
	return value


@type_checker
def check_single_email(value: str) -> str:
	"""Require exactly one e-mail address (``local@domain``, no list separators or spaces).

	Parameters
	----------
	value : str
		The address text.

	Returns
	-------
	str
		The same text.

	Raises
	------
	ValueError
		If it is not a single plausible address.
	"""
	if not _EMAIL_RE.fullmatch(value) or "." not in value.rsplit("@", 1)[1]:
		raise ValueError("must be a single e-mail address (local@domain.tld)")
	return value
