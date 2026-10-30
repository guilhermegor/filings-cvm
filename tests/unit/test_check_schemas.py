"""Unit tests for ``bin/check_schemas.py`` — schema modules hold only pydantic models.

Loaded by path (``bin/`` is not an importable package). Each case writes a tiny module to
``tmp_path`` and asserts the verdict of ``check_file``; one case runs the gate over the real tree.
"""

import importlib.util
import os
from pathlib import Path

import pytest


_ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location("check_schemas", _ROOT / "bin" / "check_schemas.py")
assert _SPEC is not None and _SPEC.loader is not None
cs = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cs)


def _write(tmp_path: Path, src: str) -> str:
	"""Write ``src`` to a scratch module and return its path."""
	path = tmp_path / "mod.py"
	path.write_text(src, encoding="utf-8")
	return str(path)


def test_basemodel_and_nested_models_pass(tmp_path: Path) -> None:
	"""Direct, attribute-qualified and in-file transitive models are clean."""
	src = (
		"import pydantic\n"
		"class A(BaseModel): ...\n"
		"class B(pydantic.BaseModel): ...\n"
		"class C(A): ...\n"
		"class D(C): ...\n"
	)
	assert cs.check_file(_write(tmp_path, src)) == 0


def test_enum_and_alias_pass(tmp_path: Path) -> None:
	"""A domain Enum and a re-export alias are allowed."""
	src = "class K(StrEnum): ...\nclass M(BaseModel): ...\nAlias = M\n"
	assert cs.check_file(_write(tmp_path, src)) == 0


def test_plain_class_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
	"""Negative case: a behavioural class is one error naming it (not a placebo)."""
	src = "class M(BaseModel): ...\nclass Service:\n\tdef run(self): ...\n"
	assert cs.check_file(_write(tmp_path, src)) == 1
	assert "Service" in capsys.readouterr().out


def test_subclass_of_foreign_base_fails(tmp_path: Path) -> None:
	"""A class deriving from a non-model base (e.g. a port) is rejected."""
	assert cs.check_file(_write(tmp_path, "class W(SubmissionWriter): ...\n")) == 1


def test_real_schema_tree_is_clean_and_nonempty() -> None:
	"""The gate inspects real files (guards against a path glob that matches nothing)."""
	cwd = Path.cwd()
	os.chdir(_ROOT)
	try:
		files = cs._schema_files()
	finally:
		os.chdir(cwd)
	assert {p.name for p in files} >= {"informe_diario.py", "perfil_mensal.py"}
	assert sum(cs.check_file(str(_ROOT / p)) for p in files) == 0
