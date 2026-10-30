"""Unit tests for ``bin/check_schemas.py`` — schema modules hold only pydantic models.

Loaded by path (``bin/`` is not an importable package). Each case writes a tiny module to
``tmp_path`` and asserts the verdict of ``check_file``; one case runs the gate over the real tree.
"""

import importlib.util
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


def test_direct_basemodel_passes(tmp_path: Path) -> None:
	"""A class deriving from the imported ``BaseModel`` is clean."""
	src = "from pydantic import BaseModel\nclass A(BaseModel): ...\n"
	assert cs.check_file(_write(tmp_path, src)) == 0


def test_attribute_qualified_basemodel_passes(tmp_path: Path) -> None:
	"""``pydantic.BaseModel`` is resolved through the module import, aliased or not."""
	src = "import pydantic as p\nclass A(p.BaseModel): ...\n"
	assert cs.check_file(_write(tmp_path, src)) == 0


def test_import_aliased_basemodel_passes(tmp_path: Path) -> None:
	"""A renamed import is still ``BaseModel``."""
	src = "from pydantic import BaseModel as Model\nclass A(Model): ...\n"
	assert cs.check_file(_write(tmp_path, src)) == 0


def test_transitive_in_file_model_passes(tmp_path: Path) -> None:
	"""A subclass of an in-file model is clean, however deep the chain."""
	src = (
		"from pydantic import BaseModel\n"
		"class A(BaseModel): ...\n"
		"class B(A): ...\n"
		"class C(B): ...\n"
	)
	assert cs.check_file(_write(tmp_path, src)) == 0


def test_enum_passes(tmp_path: Path) -> None:
	"""A domain Enum is allowed."""
	src = "from enum import StrEnum\nclass K(StrEnum): ...\n"
	assert cs.check_file(_write(tmp_path, src)) == 0


def test_reexport_alias_is_not_inspected(tmp_path: Path) -> None:
	"""An assignment is not a class, so it is never an offender."""
	src = "from pydantic import BaseModel\nclass M(BaseModel): ...\nAlias = M\n"
	assert cs.check_file(_write(tmp_path, src)) == 0


def test_plain_class_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
	"""Negative case: a behavioural class is one error naming it (not a placebo)."""
	src = (
		"from pydantic import BaseModel\n"
		"class M(BaseModel): ...\n"
		"class Service:\n"
		"\tdef run(self): ...\n"
	)
	assert cs.check_file(_write(tmp_path, src)) == 1
	assert "Service" in capsys.readouterr().out


def test_subclass_of_foreign_base_fails(tmp_path: Path) -> None:
	"""A class deriving from a non-model base (e.g. a port) is rejected."""
	assert cs.check_file(_write(tmp_path, "class W(SubmissionWriter): ...\n")) == 1


def test_unrelated_class_named_basemodel_fails(tmp_path: Path) -> None:
	"""The name alone proves nothing: this ``BaseModel`` is not pydantic's."""
	src = "from filings_cvm.ports import BaseModel\nclass A(BaseModel): ...\n"
	assert cs.check_file(_write(tmp_path, src)) == 1


def test_later_nonmodel_cannot_hide_behind_same_named_model(tmp_path: Path) -> None:
	"""Acceptance is per definition: the second ``X`` is reported despite the first."""
	src = (
		"from pydantic import BaseModel\nclass X(BaseModel): ...\nclass X:\n\tdef run(self): ...\n"
	)
	assert cs.check_file(_write(tmp_path, src)) == 1


def test_nested_class_is_checked(tmp_path: Path) -> None:
	"""A class nested in a model is still a class, and this gate reports it on purpose."""
	src = "from pydantic import BaseModel\nclass A(BaseModel):\n\tclass Config: ...\n"
	assert cs.check_file(_write(tmp_path, src)) == 1


def test_real_schema_tree_is_clean_and_nonempty(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""The gate inspects real files, from any working directory."""
	monkeypatch.chdir(tmp_path)
	files = cs._schema_files()
	assert {p.name for p in files} >= {"informe_diario.py", "perfil_mensal.py"}
	assert sum(cs.check_file(str(p)) for p in files) == 0
	assert cs.main() == 0


def test_schema_files_finds_nested_modules(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""A module in a subfolder of ``schemas/`` is collected."""
	nested = tmp_path / "src" / "pkg" / "_internal" / "config" / "schemas" / "fidc"
	nested.mkdir(parents=True)
	(nested / "foo.py").write_text("", encoding="utf-8")
	(nested.parent / "__init__.py").write_text("", encoding="utf-8")
	monkeypatch.setattr(cs, "_ROOT", tmp_path)
	assert [p.name for p in cs._schema_files()] == ["foo.py"]


def test_main_with_no_schema_files_fails(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
	"""Finding nothing to check is a failure, or a renamed directory would pass forever."""
	monkeypatch.setattr(cs, "_ROOT", tmp_path)
	assert cs.main() == 1
	assert "nothing was checked" in capsys.readouterr().out


def test_main_with_a_violation_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
	"""The entry point exits non-zero on an offending class, the path CI actually takes."""
	folder = tmp_path / "src" / "pkg" / "_internal" / "config" / "schemas"
	folder.mkdir(parents=True)
	(folder / "bad.py").write_text("class Service: ...\n", encoding="utf-8")
	monkeypatch.setattr(cs, "_ROOT", tmp_path)
	assert cs.main() == 1
