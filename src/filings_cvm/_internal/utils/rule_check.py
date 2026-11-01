"""Table-driven cross-field rule check for model validators."""

from __future__ import annotations

from collections.abc import Sequence

from filings_cvm._internal.utils.typing import type_checker


@type_checker
def raise_first(rules: Sequence[tuple[bool, str]]) -> None:
	"""Raise ``ValueError`` with the message of the first rule whose flag is true.

	Parameters
	----------
	rules : Sequence[tuple[bool, str]]
		``(violated, message)`` pairs, in the order they should be reported.

	Raises
	------
	ValueError
		With the message of the first violated rule.
	"""
	message = next((text for violated, text in rules if violated), None)
	if message is not None:
		raise ValueError(message)
