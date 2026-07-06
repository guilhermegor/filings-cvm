"""Metaclass that applies runtime type checking to every method in a class.

``staticmethod``, ``classmethod`` and ``property`` descriptors are preserved (the
underlying function is wrapped and re-wrapped in the same descriptor) so a checked
static method called via an instance no longer receives ``self`` as its first
argument.
"""

from __future__ import annotations

from typing import Any

from filings-cvm._internal.utils.typing.validate import create_type_checked_method


class TypeChecker(type):
	"""Metaclass for automatic runtime type checking of all public methods.

	Apply as ``metaclass=TypeChecker`` to enforce annotated argument types on
	every call, including ``__init__``. Dunder methods (except ``__init__``) are
	left untouched to avoid interfering with Python internals.

	Examples
	--------
	>>> class Calculator(metaclass=TypeChecker):
	...     def add(self, x: int, y: int) -> int:
	...         return x + y
	>>> Calculator().add(1, "two")  # raises TypeError
	"""

	def __new__(
		cls: type[TypeChecker],
		str_name: str,
		tuple_bases: tuple,
		dict_attrs: dict[str, Any],
	) -> TypeChecker:
		"""Wrap public methods with type checking before the class is created.

		Parameters
		----------
		cls : type[TypeChecker]
			The metaclass.
		str_name : str
			Name of the class being created.
		tuple_bases : tuple
			Base classes.
		dict_attrs : dict[str, Any]
			Class namespace dictionary.

		Returns
		-------
		TypeChecker
			New class with type-checked methods.
		"""
		for str_attr, attr_value in dict_attrs.items():
			if str_attr.startswith("__"):
				continue
			dict_attrs[str_attr] = _wrap_attribute(attr_value)
		if "__init__" in dict_attrs:
			dict_attrs["__init__"] = create_type_checked_method(dict_attrs["__init__"])
		return super().__new__(cls, str_name, tuple_bases, dict_attrs)


def _wrap_attribute(attr_value: Any) -> Any:
	"""Wrap a class attribute with type checking, preserving its descriptor.

	Parameters
	----------
	attr_value : Any
		The class-body attribute (function, staticmethod, classmethod, property,
		or a non-callable).

	Returns
	-------
	Any
		The wrapped attribute (descriptor preserved), or the attribute unchanged
		when it is not a checkable callable.
	"""
	if isinstance(attr_value, staticmethod):
		return staticmethod(create_type_checked_method(attr_value.__func__))
	if isinstance(attr_value, classmethod):
		return classmethod(create_type_checked_method(attr_value.__func__))
	if isinstance(attr_value, property):
		return attr_value
	if callable(attr_value):
		return create_type_checked_method(attr_value)
	return attr_value
