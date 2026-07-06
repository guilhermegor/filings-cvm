"""Metaclass combining Protocol's metaclass with TypeChecker for typed protocols."""

from __future__ import annotations

from typing import Protocol

from filings_cvm._internal.utils.typing.type_checker import TypeChecker


_ProtocolMeta = type(Protocol)


class ProtocolTypeCheckerMeta(_ProtocolMeta, TypeChecker):
	"""Metaclass for ``Protocol`` classes with runtime type checking.

	Combines Python's internal ``Protocol`` metaclass (structural subtyping) with
	:class:`~chassis.typing.type_checker.TypeChecker`. Use as
	``metaclass=ProtocolTypeCheckerMeta`` on a Protocol port to enforce annotated
	argument types on direct calls to the stub.
	"""
