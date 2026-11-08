"""Behaviour of ``bin/lib/pip_requirements.py`` for the mixed PEP 621 / Poetry layout."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


_PATH = Path(__file__).resolve().parents[2] / "bin" / "lib" / "pip_requirements.py"
_SPEC = importlib.util.spec_from_file_location("pip_requirements", _PATH)
mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(mod)

_MIXED = {
	"project": {"dependencies": ["requests>=2"]},
	"tool": {"poetry": {"group": {"dev": {"dependencies": {"pytest": "^8.0"}}}}},
}


def test_select_requirements_mixed_layout_reads_poetry_group() -> None:
	"""A Poetry-only group is resolved even when ``[project]`` is populated."""
	assert mod.select_requirements(_MIXED, ["main", "dev"]) == [
		"requests>=2",
		"pytest>=8.0,<9.0.0",
	]


def test_undeclared_groups_flags_a_group_no_table_declares() -> None:
	"""A requested group absent from both tables is reported."""
	assert mod.undeclared_groups(_MIXED, ["main", "dev", "docs"]) == ["docs"]


def test_build_requirement_rejects_or_constraint_naming_the_dependency() -> None:
	"""A ``||`` constraint exits with a message that names the dependency."""
	with pytest.raises(SystemExit, match="pkg"):
		mod.build_requirement("pkg", ">=1 || >=3")
