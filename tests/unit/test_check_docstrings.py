"""Unit tests for ``bin/check_docstrings.py`` — NumPy docstring vs signature gate.

Loaded by path (``bin/`` is not an importable package). Only a function with a return
annotation (or annotated params) is type-compared; type mismatches are hard errors, while
missing docstrings and Raises drift are soft warnings that never count.
"""

import importlib.util
from pathlib import Path

import pytest


_PATH = Path(__file__).resolve().parents[2] / "bin" / "check_docstrings.py"
_SPEC = importlib.util.spec_from_file_location("check_docstrings", _PATH)
assert _SPEC is not None and _SPEC.loader is not None
cd = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cd)


def _errors(tmp_path: Path, src: str) -> int:
	"""Write ``src`` to a scratch module and return ``check_file``'s hard-error count."""
	path = tmp_path / "mod.py"
	path.write_text(src, encoding="utf-8")
	return cd.check_file(str(path))


_RETURN_TMPL = (
	'def f() -> {hint}:\n\t"""Do it.\n\n\tReturns\n\t-------\n\t{doc}\n\t\tThe value.\n\t"""\n'
	"\treturn 1\n"
)

_PARAM_TMPL = (
	'def f(x: {hint}) -> None:\n\t"""Do it.\n\n\tParameters\n\t----------\n\tx : {doc}\n'
	'\t\tThe input.\n\t"""\n'
)


def test_check_file_matching_return_type_passes(tmp_path: Path) -> None:
	"""Documented return type equal to the annotation is clean."""
	assert _errors(tmp_path, _RETURN_TMPL.format(hint="int", doc="int")) == 0


def test_check_file_mismatched_return_type_fails(
	tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
	"""A documented return type differing from the annotation is a hard error."""
	assert _errors(tmp_path, _RETURN_TMPL.format(hint="int", doc="str")) == 1
	assert "Return type mismatch" in capsys.readouterr().out


def test_check_file_union_spelled_with_or_passes(tmp_path: Path) -> None:
	"""NumPy ``str or None`` matches ``str | None``."""
	assert _errors(tmp_path, _RETURN_TMPL.format(hint="str | None", doc="str or None")) == 0


def test_check_file_matching_param_type_passes(tmp_path: Path) -> None:
	"""Documented parameter type equal to the annotation is clean."""
	assert _errors(tmp_path, _PARAM_TMPL.format(hint="int", doc="int")) == 0


def test_check_file_mismatched_param_type_fails(
	tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
	"""A documented parameter type differing from the annotation is a hard error."""
	assert _errors(tmp_path, _PARAM_TMPL.format(hint="int", doc="str")) == 1
	assert "mismatch" in capsys.readouterr().out


def test_check_file_missing_docstring_is_warning_only(
	tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
	"""No docstring prints a warning but does not count as an error."""
	assert _errors(tmp_path, "def f() -> int:\n\treturn 1\n") == 0
	assert "Missing docstring" in capsys.readouterr().out


def test_check_file_raises_drift_is_warning_only(
	tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
	"""A direct raise absent from the docstring warns but is not an error."""
	src = 'def f() -> None:\n\t"""Do it."""\n\traise ValueError("x")\n'
	assert _errors(tmp_path, src) == 0
	assert "Raised but not documented" in capsys.readouterr().out
