"""Unit tests for the binary-float dtype gate.

The gate's whole value is the failing direction: a gate that only ever passes is
indistinguishable from no gate at all. So the happy path is the *least* interesting
assertion here — each test below introduces a deliberate violation and pins that the gate
catches it, plus the escape hatch that lets a genuinely dimensionless value through.

The script is not an importable package, so it is loaded by path (see ``tests/CLAUDE.md``).
"""

import importlib.util
from pathlib import Path

import pytest


_PATH = Path(__file__).resolve().parents[2] / "bin" / "check_dtypes.py"
_SPEC = importlib.util.spec_from_file_location("check_dtypes", _PATH)
assert _SPEC is not None and _SPEC.loader is not None
check_dtypes = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(check_dtypes)


@pytest.mark.parametrize(
	"str_dtype",
	["float", "float16", "float32", "float64", "float128", "Float32", "Float64"],
)
def test_check_file_flags_every_banned_float_spelling(tmp_path: Path, str_dtype: str) -> None:
	"""Each pandas/numpy float spelling is caught, not just ``float64``."""
	path_file = tmp_path / "reader.py"
	path_file.write_text(f'_DTYPES = {{"VL_PATRIM_LIQ": "{str_dtype}"}}\n', encoding="utf-8")

	assert check_dtypes.check_file(str(path_file)) == 1


def test_check_file_flags_a_float_named_only_in_a_docstring(tmp_path: Path) -> None:
	"""A docstring example is the worst place to teach the wrong dtype, so it counts too.

	This is not hypothetical: this repo's own ``apply_dtypes`` docstring cited ``"float64"``
	as an example dtype, and every reader is written by copying an existing one.
	"""
	path_file = tmp_path / "seam.py"
	path_file.write_text(
		'"""Maps a column, e.g. ``"int64"``, ``"float64"``."""\n', encoding="utf-8"
	)

	assert check_dtypes.check_file(str(path_file)) == 1


def test_check_file_accepts_a_float_annotated_with_a_reason(tmp_path: Path) -> None:
	"""The escape hatch clears the line — a ban with no way out gets routed around worse."""
	path_file = tmp_path / "stats.py"
	path_file.write_text(
		'_DTYPES = {"RATIO": "float64"}  # dtype-ok: dimensionless statistic, no exact scale\n',
		encoding="utf-8",
	)

	assert check_dtypes.check_file(str(path_file)) == 0


def test_check_file_accepts_the_lossless_declarations(tmp_path: Path) -> None:
	"""Text and decimal columns — the sanctioned replacements — pass cleanly."""
	path_file = tmp_path / "clean.py"
	path_file.write_text(
		'_DTYPES = {"CNPJ": "str", "NR": "int64"}\n_DECIMALS = ("VL_PATRIM_LIQ",)\n',
		encoding="utf-8",
	)

	assert check_dtypes.check_file(str(path_file)) == 0


def test_check_file_counts_every_violation_not_just_the_first(tmp_path: Path) -> None:
	"""A file with several offences reports all of them, so one run fixes the whole file."""
	path_file = tmp_path / "many.py"
	path_file.write_text(
		'_A = {"X": "float64"}\n_B = {"Y": "float32"}\n_C = {"Z": "str"}\n',
		encoding="utf-8",
	)

	assert check_dtypes.check_file(str(path_file)) == 2


def test_the_shipped_source_tree_is_free_of_banned_float_dtypes() -> None:
	"""The gate passes on ``src/`` as shipped — the regression guard for the whole rule."""
	assert sum(check_dtypes.check_file(str(p)) for p in check_dtypes._source_files()) == 0
