"""Function decorator for opt-in per-function runtime type checking."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from filings-cvm._internal.utils.typing.validate import create_type_checked_method


def type_checker(func: Callable[..., Any]) -> Callable[..., Any]:
	"""Wrap ``func`` with runtime argument type checking from its annotations.

	Use on standalone module-level functions, or on a method whose class cannot
	use the :class:`~chassis.typing.type_checker.TypeChecker` metaclass.

	Parameters
	----------
	func : Callable[..., Any]
		Function to wrap.

	Returns
	-------
	Callable[..., Any]
		Wrapped callable that validates argument types on every call.

	Examples
	--------
	>>> @type_checker
	... def add(x: int, y: int) -> int:
	...     return x + y
	>>> add(1, "two")  # raises TypeError
	"""
	return create_type_checked_method(func)
