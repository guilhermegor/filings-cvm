"""Unit tests for ``bin/check_typing.py`` — runtime type-checker application gate.

Loaded by path (``bin/`` is not an importable package). Each case writes a tiny module to
``tmp_path`` and asserts the error count returned by ``check_file``.
"""

import importlib.util
from pathlib import Path

import pytest


_PATH = Path(__file__).resolve().parents[2] / "bin" / "check_typing.py"
_SPEC = importlib.util.spec_from_file_location("check_typing", _PATH)
assert _SPEC is not None and _SPEC.loader is not None
ct = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(ct)


def _errors(tmp_path: Path, src: str) -> int:
	"""Write ``src`` to a scratch module and return ``check_file``'s error count."""
	path = tmp_path / "mod.py"
	path.write_text(src, encoding="utf-8")
	return ct.check_file(str(path))


def test_check_file_decorated_function_passes(tmp_path: Path) -> None:
	"""A function with @type_checker is clean."""
	assert _errors(tmp_path, "@type_checker\ndef f() -> None:\n\tpass\n") == 0


def test_check_file_undecorated_function_fails(
	tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
	"""A standalone function without @type_checker is one error."""
	assert _errors(tmp_path, "def f() -> None:\n\tpass\n") == 1
	assert "@type_checker" in capsys.readouterr().out


def test_check_file_private_function_is_checked(tmp_path: Path) -> None:
	"""A ``_``-prefixed helper is not exempt."""
	assert _errors(tmp_path, "def _f() -> None:\n\tpass\n") == 1


def test_check_file_dunder_function_is_skipped(tmp_path: Path) -> None:
	"""Dunder names are the one skip."""
	assert _errors(tmp_path, "def __getattr__(name):\n\tpass\n") == 0


def test_check_file_root_class_without_metaclass_fails(tmp_path: Path) -> None:
	"""A base-less class must declare a checker metaclass."""
	assert _errors(tmp_path, "class A:\n\tpass\n") == 1


def test_check_file_root_class_with_metaclass_passes(tmp_path: Path) -> None:
	"""A base-less class with TypeChecker passes."""
	assert _errors(tmp_path, "class A(metaclass=TypeChecker):\n\tpass\n") == 0


def test_check_file_subclass_inherits_metaclass_passes(tmp_path: Path) -> None:
	"""A class with a base is left alone."""
	assert _errors(tmp_path, "class B(A):\n\tpass\n") == 0


def test_check_file_pydantic_model_with_metaclass_fails(tmp_path: Path) -> None:
	"""A Pydantic model must not set a checker metaclass."""
	assert _errors(tmp_path, "class M(BaseModel, metaclass=TypeChecker):\n\tpass\n") == 1


def test_check_file_pydantic_model_plain_passes(tmp_path: Path) -> None:
	"""A plain Pydantic model passes."""
	assert _errors(tmp_path, "class M(BaseModel):\n\tx: int\n") == 0
