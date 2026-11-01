"""Unit tests for the dynamic-version stub gate (offline; no git, no network).

Each case pins one decision: the stub passes, a hand-bump fails, and a project that does not
enable dynamic versioning is ignored whatever its version.
"""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType

import pytest


_BIN = Path(__file__).resolve().parents[2] / "bin"


def _load(str_name: str) -> ModuleType:
	"""Load a ``bin/`` script by path (``bin/`` is not a package).

	Parameters
	----------
	str_name : str
		Module stem under ``bin/``.

	Returns
	-------
	ModuleType
		The imported module.
	"""
	cls_spec = importlib.util.spec_from_file_location(str_name, _BIN / f"{str_name}.py")
	cls_module = importlib.util.module_from_spec(cls_spec)
	sys.modules[str_name] = cls_module
	cls_spec.loader.exec_module(cls_module)
	return cls_module


gate = _load("check_dynamic_version_stub")

STR_DYNAMIC = '[tool.poetry-dynamic-versioning]\nenable = true\nvcs = "git"\n\n'


def _pyproject(str_version: str, str_dynamic: str) -> str:
	"""Build a minimal ``pyproject.toml`` body.

	Parameters
	----------
	str_version : str
		Value of ``[tool.poetry] version``.
	str_dynamic : str
		Optional dynamic-versioning section, placed after ``[tool.poetry]``.

	Returns
	-------
	str
		The document text.
	"""
	return f'[tool.poetry]\nname = "demo"\nversion = "{str_version}"\n\n{str_dynamic}'


def _run(path_dir: Path, str_text: str) -> int:
	"""Write ``pyproject.toml`` under ``path_dir`` and run the gate on it.

	Parameters
	----------
	path_dir : pathlib.Path
		Project root.
	str_text : str
		``pyproject.toml`` contents.

	Returns
	-------
	int
		The gate's exit code.
	"""
	(path_dir / "pyproject.toml").write_text(str_text, encoding="utf-8")
	return gate.main(["--root", str(path_dir)])


@pytest.mark.parametrize(
	("str_version", "str_dynamic", "int_expected"),
	[
		("0.0.0", STR_DYNAMIC, 0),
		("1.0.0", STR_DYNAMIC, 1),
		("1.0.0", "", 0),
		("1.0.0", STR_DYNAMIC.replace("true", "false"), 0),
	],
	ids=["stub-passes", "hand-bump-fails", "static-ignored", "disabled-ignored"],
)
def test_exit_code(tmp_path: Path, str_version: str, str_dynamic: str, int_expected: int) -> None:
	"""Pin the exit code for the stub, hand-bump and ignored-project cases.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest-provided project root.
	str_version : str
		Value of ``[tool.poetry] version``.
	str_dynamic : str
		Optional dynamic-versioning section.
	int_expected : int
		Expected exit code.
	"""
	assert _run(tmp_path, _pyproject(str_version, str_dynamic)) == int_expected


def test_finding_names_the_found_version() -> None:
	"""A hand-bump finding names the offending version."""
	assert "'1.0.0'" in gate.find_problem(_pyproject("1.0.0", STR_DYNAMIC))


def test_missing_version_is_a_finding() -> None:
	"""A tag-versioned project with no version at all is still a finding."""
	assert "<missing>" in gate.find_problem("[tool.poetry]\nname = 'x'\n\n" + STR_DYNAMIC)


def test_missing_pyproject_is_a_noop(tmp_path: Path) -> None:
	"""A root with no ``pyproject.toml`` exits 0.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest-provided empty directory.
	"""
	assert gate.main(["--root", str(tmp_path)]) == 0
