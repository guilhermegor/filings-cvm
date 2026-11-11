"""Core type-validation engine: ``validate_type`` and its method wrapper.

The type hints are resolved once and cached on the wrapper (instead of on every
call) and both ``self`` and ``cls`` are skipped, so the wrapper is safe on
instance, static and class methods alike.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
import inspect
import types
from typing import Any, Literal, Union, get_args, get_origin, get_type_hints
from unittest.mock import Mock


# Both the legacy ``typing.Union[...]`` and the PEP 604 ``X | Y`` syntax must be
# treated as unions; the latter has a distinct origin (``types.UnionType``).
_UNION_ORIGINS = (Union, types.UnionType)


try:
	from typing import _TypedDictMeta  # private CPython API; may be absent elsewhere

	_TYPED_DICT_META: type | None = _TypedDictMeta
except AttributeError:
	_TYPED_DICT_META = None


def validate_type(value: Any, expected_type: Any, param_name: str) -> None:
	"""Raise ``TypeError`` when ``value`` does not satisfy ``expected_type``.

	Parameters
	----------
	value : Any
		Value to validate.
	expected_type : Any
		Annotation to check against.
	param_name : str
		Parameter name shown in the error message.

	Raises
	------
	TypeError
		When the value does not match the expected type.
	"""
	if expected_type is Any:
		return
	if isinstance(value, Mock):
		return
	if _is_typed_dict(expected_type):
		if not isinstance(value, dict):
			raise TypeError(
				f"{param_name} must be a dict for TypedDict, got {type(value).__name__}"
			)
		return
	if isinstance(value, bool) and expected_type in (int, float):
		raise TypeError(
			f"{param_name} must be of type {expected_type.__name__}, got {type(value).__name__}"
		)
	if expected_type is int and hasattr(value, "dtype") and value.dtype.kind in ("i", "u"):
		return
	if expected_type is float and not isinstance(value, float):
		raise TypeError(
			f"{param_name} must be of type {expected_type.__name__}, got {type(value).__name__}"
		)
	_validate_by_origin(value, expected_type, param_name)


def _is_typed_dict(expected_type: Any) -> bool:
	"""Return whether ``expected_type`` is a ``TypedDict`` subclass.

	Parameters
	----------
	expected_type : Any
		Annotation to inspect.

	Returns
	-------
	bool
		``True`` when the annotation is a TypedDict.
	"""
	if (
		isinstance(expected_type, type)
		and hasattr(expected_type, "__annotations__")
		and hasattr(expected_type, "__total__")
	):
		return True
	if _TYPED_DICT_META is not None:
		try:
			return isinstance(expected_type, type) and issubclass(
				type(expected_type), _TYPED_DICT_META
			)
		except (TypeError, AttributeError):
			return False
	return False


def _validate_by_origin(value: Any, expected_type: Any, param_name: str) -> None:
	"""Validate ``value`` against a generic / union / plain ``expected_type``.

	Parameters
	----------
	value : Any
		Value to validate.
	expected_type : Any
		Annotation to check against.
	param_name : str
		Parameter name shown in the error message.

	Raises
	------
	TypeError
		When the value does not match the expected type.
	"""
	origin = get_origin(expected_type)
	if origin is Literal:
		_validate_literal(value, expected_type, param_name)
		return
	if origin in _UNION_ORIGINS:
		_validate_union(value, expected_type, param_name)
		return
	if origin is list:
		_validate_list(value, expected_type, param_name)
		return
	if origin is not None:
		if not isinstance(value, origin):
			raise TypeError(
				f"{param_name} must be of type {expected_type}, got {type(value).__name__}"
			)
		return
	if isinstance(expected_type, type):
		if not isinstance(value, expected_type):
			str_got = type(value).__name__
			raise TypeError(
				f"{param_name} must be of type {expected_type.__name__}, got {str_got}"
			)
		return
	try:
		isinstance(value, expected_type)
	except TypeError:
		return


def _validate_literal(value: Any, expected_type: Any, param_name: str) -> None:
	"""Validate ``value`` against a ``Literal`` annotation.

	Parameters
	----------
	value : Any
		Value to validate.
	expected_type : Any
		The ``Literal[...]`` annotation.
	param_name : str
		Parameter name shown in the error message.

	Raises
	------
	TypeError
		When the value is not one of the literal options.
	"""
	args = get_args(expected_type)
	if value not in args:
		str_allowed = ", ".join(repr(a) for a in args)
		raise TypeError(f"{param_name} must be one of: {str_allowed}, got {value!r}")


def _validate_union(value: Any, expected_type: Any, param_name: str) -> None:
	"""Validate ``value`` against a ``Union`` / ``Optional`` annotation.

	Parameters
	----------
	value : Any
		Value to validate.
	expected_type : Any
		The union annotation.
	param_name : str
		Parameter name shown in the error message.

	Raises
	------
	TypeError
		When the value matches none of the union members.
	"""
	args = get_args(expected_type)
	for arg in args:
		if arg is type(None) and value is None:
			return
		try:
			validate_type(value, arg, param_name)
			return
		except TypeError:
			continue
	list_type_names = [getattr(a, "__name__", str(a)) for a in args]
	raise TypeError(
		f"{param_name} must be one of types: {', '.join(list_type_names)}, "
		f"got {type(value).__name__}"
	)


def _validate_list(value: Any, expected_type: Any, param_name: str) -> None:
	"""Validate ``value`` against a ``list[...]`` annotation, element by element.

	Parameters
	----------
	value : Any
		Value to validate.
	expected_type : Any
		The ``list[...]`` annotation.
	param_name : str
		Parameter name shown in the error message.

	Raises
	------
	TypeError
		When the value is not a list or an element has the wrong type.
	"""
	if not isinstance(value, list):
		raise TypeError(f"{param_name} must be of type list, got {type(value).__name__}")
	element_type = get_args(expected_type)[0] if get_args(expected_type) else Any
	for int_i, elem in enumerate(value):
		if get_origin(element_type) is Callable:
			if not callable(elem):
				raise TypeError(
					f"{param_name}[{int_i}] must be callable, got {type(elem).__name__}"
				)
		else:
			validate_type(elem, element_type, f"{param_name}[{int_i}]")


def create_type_checked_method(original_method: Callable[..., Any]) -> Callable[..., Any]:
	"""Wrap ``original_method`` so each call validates its argument types.

	The annotations are resolved once on the first call and cached, so the
	per-call cost is only the ``isinstance`` checks. Unresolvable annotations
	(forward references that never resolve) disable checking for that method.

	Parameters
	----------
	original_method : Callable[..., Any]
		Function or method to wrap.

	Returns
	-------
	Callable[..., Any]
		Wrapper that validates argument types before delegating.
	"""
	dict_cache: dict[str, Any] = {}

	@wraps(original_method)
	def wrapper(*args: Any, **kwargs: Any) -> Any:
		"""Validate argument types against the cached hints, then delegate."""
		if "hints" not in dict_cache:
			try:
				dict_cache["hints"] = get_type_hints(original_method)
				dict_cache["sig"] = inspect.signature(original_method)
			except (NameError, AttributeError, TypeError):
				dict_cache["hints"] = None
		dict_hints = dict_cache["hints"]
		if dict_hints is None:
			return original_method(*args, **kwargs)
		_check_arguments(dict_cache["sig"], dict_hints, args, kwargs)
		return original_method(*args, **kwargs)

	return wrapper


def _check_arguments(
	sig: inspect.Signature, dict_hints: dict[str, Any], args: tuple, kwargs: dict
) -> None:
	"""Validate positional and keyword arguments against the cached hints.

	Parameters
	----------
	sig : inspect.Signature
		The wrapped callable's signature.
	dict_hints : dict[str, Any]
		Resolved type hints keyed by parameter name.
	args : tuple
		Positional arguments passed to the call.
	kwargs : dict
		Keyword arguments passed to the call.
	"""
	int_pos = 0
	for str_param, param in sig.parameters.items():
		if str_param in ("self", "cls"):
			int_pos += 1
			continue
		if param.kind == inspect.Parameter.VAR_POSITIONAL:
			varargs_type = dict_hints.get(str_param, Any)
			if get_origin(varargs_type) is list:
				varargs_type = get_args(varargs_type)[0]
			while int_pos < len(args):
				validate_type(args[int_pos], varargs_type, f"{str_param}[{int_pos}]")
				int_pos += 1
		elif param.kind in (
			inspect.Parameter.POSITIONAL_ONLY,
			inspect.Parameter.POSITIONAL_OR_KEYWORD,
		):
			if int_pos < len(args) and str_param in dict_hints:
				validate_type(args[int_pos], dict_hints[str_param], str_param)
			int_pos += 1
	for str_param, value in kwargs.items():
		if str_param in dict_hints:
			validate_type(value, dict_hints[str_param], str_param)
