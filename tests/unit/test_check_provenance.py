"""Unit tests for ``bin/check_provenance.py`` — read_table must be paired with stamp_provenance.

Loaded by path (``bin/`` is not an importable package). Each case writes a tiny module to
``tmp_path`` and asserts the verdict of ``check_file``.
"""

import importlib.util
from pathlib import Path

import pytest


_PATH = Path(__file__).resolve().parents[2] / "bin" / "check_provenance.py"
_SPEC = importlib.util.spec_from_file_location("check_provenance", _PATH)
assert _SPEC is not None and _SPEC.loader is not None
cp = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cp)


def _write(tmp_path: Path, src: str) -> str:
	"""Write ``src`` to a scratch module and return its path."""
	path = tmp_path / "mod.py"
	path.write_text(src, encoding="utf-8")
	return str(path)


def test_check_file_read_and_stamp_passes(tmp_path: Path) -> None:
	"""A module calling both seams is clean."""
	src = "def f(x):\n\tdf = read_table(x)\n\treturn stamp_provenance(df)\n"
	assert cp.check_file(_write(tmp_path, src)) == 0


def test_check_file_read_without_stamp_fails(
	tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
	"""A module calling read_table but never stamp_provenance is one error."""
	assert cp.check_file(_write(tmp_path, "def f(x):\n\treturn read_table(x)\n")) == 1
	assert "stamp_provenance" in capsys.readouterr().out


def test_check_file_attribute_call_counts_as_read(tmp_path: Path) -> None:
	"""``mod.read_table(...)`` is detected the same as a bare call."""
	assert cp.check_file(_write(tmp_path, "def f(x):\n\treturn u.read_table(x)\n")) == 1


def test_check_file_neither_call_passes(tmp_path: Path) -> None:
	"""A module calling neither seam (thin subclass) is unaffected."""
	assert cp.check_file(_write(tmp_path, "def f(x):\n\treturn x\n")) == 0


def test_check_file_stamp_only_passes(tmp_path: Path) -> None:
	"""Stamping without reading is not a violation."""
	assert cp.check_file(_write(tmp_path, "def f(x):\n\treturn stamp_provenance(x)\n")) == 0
