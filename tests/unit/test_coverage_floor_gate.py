"""Unit tests for the coverage-floor omit gate (``bin/check_coverage_floor.py``).

Ported from the BlueprintX template and adapted: this repo's floor is derived from
``src/<pkg>/{ingestion,submission}`` (not ``src/capabilities/*/{domain,application}``), with
``_internal/`` as the one deliberate exclusion.

The should-PASS cases matter as much as the should-fail ones: a gate exercised only on what
it rejects has been shown to reject, not to discriminate.
"""

from collections.abc import Callable
import functools
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


GateRunner = Callable[[Path], tuple[int, str]]


def _load_gate() -> ModuleType:
	"""Import ``bin/check_coverage_floor.py`` as a module.

	Returns
	-------
	ModuleType
		The loaded gate module.
	"""
	path_gate = Path(__file__).resolve().parents[2] / "bin" / "check_coverage_floor.py"
	cls_spec = importlib.util.spec_from_file_location("_check_coverage_floor", path_gate)
	assert cls_spec is not None
	assert cls_spec.loader is not None
	cls_module = importlib.util.module_from_spec(cls_spec)
	cls_spec.loader.exec_module(cls_module)
	return cls_module


def _project(tmp_path: Path, str_omit: str) -> Path:
	"""Write a minimal project root with a ``.coveragerc`` and empty ``src/``.

	Parameters
	----------
	tmp_path : pathlib.Path
		Directory to build in.
	str_omit : str
		The ``omit =`` body (indented lines), or ``""`` for an empty list.

	Returns
	-------
	pathlib.Path
		The project root.
	"""
	(tmp_path / "src").mkdir()
	str_body = f"omit =\n{str_omit}" if str_omit else "omit ="
	(tmp_path / ".coveragerc").write_text(f"[run]\nsource = src/\n{str_body}\n", encoding="utf-8")
	return tmp_path


def _module(path_root: Path, str_section: str, str_source: str) -> Path:
	"""Write ``src/pkg/<section>/service.py`` and return its relative path.

	Parameters
	----------
	path_root : pathlib.Path
		The project root built by ``_project``.
	str_section : str
		``"ingestion"``, ``"submission"`` or ``"_internal"``.
	str_source : str
		The module's Python source.

	Returns
	-------
	pathlib.Path
		The module path relative to the project root.
	"""
	path_dir = path_root / "src" / "pkg" / str_section
	path_dir.mkdir(parents=True, exist_ok=True)
	(path_dir / "service.py").write_text(str_source, encoding="utf-8")
	return Path("src/pkg") / str_section / "service.py"


_SRC_FUNC = "def compute():\n\treturn 1\n"


def test_missing_coveragerc_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
	"""No ``.coveragerc`` at all must exit non-zero, never green."""
	(tmp_path / "src").mkdir()
	monkeypatch.chdir(tmp_path)
	assert _load_gate().main() == 1


def _run(
	monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture, path_root: Path
) -> tuple[int, str]:
	"""Chdir into a project, run the gate, and return ``(exit_code, stderr)``."""
	monkeypatch.chdir(path_root)
	int_code = _load_gate().main()
	return int_code, capsys.readouterr().err


@pytest.fixture
def run_gate(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> GateRunner:
	"""Return a runner that yields ``(exit_code, stderr)`` for a project root."""
	return functools.partial(_run, monkeypatch, capsys)


def test_no_section_modules_fails(tmp_path: Path, run_gate: GateRunner) -> None:
	"""Scanning zero logic-bearing modules must exit non-zero, never report success."""
	assert run_gate(_project(tmp_path, "    src/*/_internal/*\n"))[0] == 1


def test_no_section_modules_says_why(tmp_path: Path, run_gate: GateRunner) -> None:
	"""The zero-module failure names its cause on stderr."""
	assert (
		"ZERO logic-bearing modules" in run_gate(_project(tmp_path, "    src/*/_internal/*\n"))[1]
	)


def test_internal_only_omit_passes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
	"""Omitting only ``_internal/`` leaves every section module in the denominator."""
	path_root = _project(tmp_path, "    src/*/_internal/*\n")
	_module(path_root, "ingestion", _SRC_FUNC)
	_module(path_root, "submission", _SRC_FUNC)
	monkeypatch.chdir(path_root)
	assert _load_gate().main() == 0


@pytest.fixture
def widened_omit(tmp_path: Path, run_gate: GateRunner) -> tuple[int, str]:
	"""Run the gate on a project whose omit list swallows the ingestion section."""
	path_root = _project(tmp_path, "    src/*/_internal/*\n    src/*/ingestion/*\n")
	_module(path_root, "ingestion", _SRC_FUNC)
	return run_gate(path_root)


def test_widened_omit_swallowing_a_section_fails(widened_omit: tuple[int, str]) -> None:
	"""The synthetic probe: widening omit past ``_internal/`` must fail."""
	assert widened_omit[0] == 1


def test_widened_omit_names_the_swallowed_file(widened_omit: tuple[int, str]) -> None:
	"""The failure names the module the omit list swallowed."""
	assert "pkg/ingestion/service.py" in widened_omit[1]


@pytest.fixture
def misomitted_file(tmp_path: Path, run_gate: GateRunner) -> tuple[int, str]:
	"""Run the gate on a project that omits a single submission module."""
	path_root = _project(tmp_path, "    src/*/_internal/*\n    src/pkg/submission/service.py\n")
	_module(path_root, "submission", _SRC_FUNC)
	return run_gate(path_root)


def test_single_misomitted_submission_file_fails(misomitted_file: tuple[int, str]) -> None:
	"""One omitted submission file must fail the gate."""
	assert misomitted_file[0] == 1


def test_single_misomitted_submission_file_is_named(misomitted_file: tuple[int, str]) -> None:
	"""Detection is per module: the omitted file is named on its own."""
	assert "pkg/submission/service.py" in misomitted_file[1]


def test_function_free_module_is_never_in_the_must_cover_set(tmp_path: Path) -> None:
	"""A module with only class attributes defines no function, so it is not in the floor."""
	cls_gate = _load_gate()
	path_root = _project(tmp_path, "")
	_module(path_root, "ingestion", "class Status:\n\tOPEN = 1\n")
	path_module = path_root / "src" / "pkg" / "ingestion" / "service.py"
	assert cls_gate.defines_a_function(path_module) is False


def test_discovery_keeps_function_bearing_and_drops_function_free_modules(
	tmp_path: Path,
) -> None:
	"""``must_stay_covered`` filters on behaviour: only the function-bearing module stays."""
	path_root = _project(tmp_path, "")
	_module(path_root, "ingestion", "class Status:\n\tOPEN = 1\n")
	path_keep = path_root / "src" / "pkg" / "submission" / "service.py"
	_module(path_root, "submission", _SRC_FUNC)
	assert _load_gate().must_stay_covered(path_root / "src") == [path_keep]


def test_internal_modules_are_not_in_the_must_cover_set(tmp_path: Path) -> None:
	"""``_internal/`` is the one deliberate exclusion: never part of the derived floor."""
	cls_gate = _load_gate()
	path_root = _project(tmp_path, "")
	_module(path_root, "_internal", _SRC_FUNC)
	assert cls_gate.must_stay_covered(path_root / "src") == []


def test_omit_patterns_expands_environment_variables(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Coverage.py expands ``${VAR}`` before applying omit; the raw text would never match."""
	cls_gate = _load_gate()
	monkeypatch.setenv("COV_ROOT", "/srv/app")
	path_cfg = tmp_path / ".coveragerc"
	path_cfg.write_text("[run]\nomit =\n    ${COV_ROOT}/src/*/ingestion/*\n", encoding="utf-8")

	assert cls_gate.omit_patterns(path_cfg) == ["/srv/app/src/*/ingestion/*"]


def test_absolute_omit_pattern_still_swallows_a_relative_module(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""An expanded, absolute pattern must match the RELATIVE module path it really omits."""
	cls_gate = _load_gate()
	path_root = _project(tmp_path, "")
	path_module = _module(path_root, "ingestion", _SRC_FUNC)
	monkeypatch.chdir(path_root)
	str_absolute_pattern = f"{path_root.resolve().as_posix()}/src/*/ingestion/*"

	list_problems = cls_gate.swallowed_by_omit([path_module], [str_absolute_pattern])

	assert len(list_problems) == 1


def test_relative_omit_pattern_keeps_working(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Widening to absolute must not break the plain relative form."""
	cls_gate = _load_gate()
	path_root = _project(tmp_path, "")
	path_module = _module(path_root, "ingestion", _SRC_FUNC)
	monkeypatch.chdir(path_root)

	list_problems = cls_gate.swallowed_by_omit([path_module], ["src/*/ingestion/*"])

	assert len(list_problems) == 1
