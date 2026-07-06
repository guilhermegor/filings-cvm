"""Metaclass combining ABCMeta with TypeChecker for typed abstract base classes."""

from __future__ import annotations

from abc import ABCMeta

from filings-cvm._internal.utils.typing.type_checker import TypeChecker


class ABCTypeCheckerMeta(ABCMeta, TypeChecker):
	"""Metaclass for abstract base classes with runtime type checking.

	Combines :class:`abc.ABCMeta` (abstract-method enforcement) with
	:class:`~chassis.typing.type_checker.TypeChecker` (argument validation). Use as
	``metaclass=ABCTypeCheckerMeta`` instead of inheriting :class:`abc.ABC`.
	"""
