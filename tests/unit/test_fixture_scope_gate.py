"""Unit tests for the fixture-scope gate (offline; no git, no network).

The gate is a PROXY (blueprintx#442) — it cannot detect order dependence, only the cheapest
way it gets introduced (a fixture's `scope=` widened away from the pytest default). Every
test below either proves the gate FIRES on a widened, unjustified scope, or pins one measured
reason it must NOT fire (function scope, no scope at all, a written justification, a dynamic
value it cannot read).
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


gate = _load("check_fixture_scope")


def _test_file(path_dir: Path, str_source: str) -> Path:
	"""Write a test-module source file and return its path.

	Parameters
	----------
	path_dir : pathlib.Path
		Directory to write into.
	str_source : str
		File contents.

	Returns
	-------
	pathlib.Path
		The written file.
	"""
	path_file = path_dir / "test_sample.py"
	path_file.write_text(str_source, encoding="utf-8")
	return path_file


@pytest.fixture
def list_unjustified_module_scope(tmp_path: Path) -> list[str]:
	"""Return the findings for a module-scope fixture that carries no written reason.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.

	Returns
	-------
	list[str]
		The gate's findings.
	"""
	path_file = _test_file(
		tmp_path,
		'import pytest\n\n\n@pytest.fixture(scope="module")\ndef shared():\n\treturn {}\n',
	)
	return gate.file_problems(path_file)


def test_a_module_scope_fixture_with_no_reason_is_reported(
	list_unjustified_module_scope: list[str],
) -> None:
	"""A widened, unjustified scope produces exactly one finding.

	Parameters
	----------
	list_unjustified_module_scope : list[str]
		The gate's findings.
	"""
	assert len(list_unjustified_module_scope) == 1


def test_the_finding_names_the_fixture(list_unjustified_module_scope: list[str]) -> None:
	"""The finding names the offending fixture.

	Parameters
	----------
	list_unjustified_module_scope : list[str]
		The gate's findings.
	"""
	assert "shared()" in list_unjustified_module_scope[0]


def test_the_finding_names_the_widened_scope(list_unjustified_module_scope: list[str]) -> None:
	"""The finding names the scope that was widened.

	Parameters
	----------
	list_unjustified_module_scope : list[str]
		The gate's findings.
	"""
	assert "scope='module'" in list_unjustified_module_scope[0]


@pytest.mark.parametrize("str_scope", ["class", "session", "package"])
def test_every_wide_scope_is_reported(tmp_path: Path, str_scope: str) -> None:
	"""class/session/package are widened scopes too, not just module."""
	path_file = _test_file(
		tmp_path,
		f'import pytest\n\n\n@pytest.fixture(scope="{str_scope}")\ndef shared():\n\treturn {{}}\n',
	)

	assert len(gate.file_problems(path_file)) == 1


def test_a_bare_fixture_decorator_is_accepted() -> None:
	"""`@pytest.fixture` with no call carries no `scope=` to widen."""
	node_dec = __import__("ast").parse("@fixture\ndef f(): pass").body[0].decorator_list[0]

	assert gate._decorator_call_name(node_dec) is None


def test_a_file_with_an_imported_bare_fixture_has_no_findings(tmp_path: Path) -> None:
	"""`from pytest import fixture` + bare `@fixture` goes through `file_problems` clean."""
	path_file = _test_file(
		tmp_path, "from pytest import fixture\n\n\n@fixture\ndef f():\n\treturn {}\n"
	)

	assert gate.file_problems(path_file) == []


def test_the_default_function_scope_is_accepted(tmp_path: Path) -> None:
	"""No `scope=` kwarg at all — the pytest default — passes clean."""
	path_file = _test_file(tmp_path, "import pytest\n\n\n@pytest.fixture\ndef f():\n\treturn {}\n")

	assert gate.file_problems(path_file) == []


def test_an_explicit_function_scope_is_accepted(tmp_path: Path) -> None:
	"""`scope="function"` spelled out explicitly is the same as the default."""
	path_file = _test_file(
		tmp_path,
		'import pytest\n\n\n@pytest.fixture(scope="function")\ndef f():\n\treturn {}\n',
	)

	assert gate.file_problems(path_file) == []


def test_a_written_justification_on_the_decorator_line_is_accepted(tmp_path: Path) -> None:
	"""`# fixture-scope-ok: <reason>` on the decorator line is the escape hatch."""
	path_file = _test_file(
		tmp_path,
		'import pytest\n\n\n@pytest.fixture(scope="module")  '
		"# fixture-scope-ok: read-only, never mutated\ndef shared():\n\treturn {}\n",
	)

	assert gate.file_problems(path_file) == []


def test_a_written_justification_on_the_def_line_is_also_accepted(tmp_path: Path) -> None:
	"""The reason may sit anywhere from the decorator through the `def` line."""
	path_file = _test_file(
		tmp_path,
		'import pytest\n\n\n@pytest.fixture(scope="module")\n'
		"def shared():  # fixture-scope-ok: seeded once per module on purpose\n\treturn {}\n",
	)

	assert gate.file_problems(path_file) == []


def test_a_bare_marker_with_no_reason_is_rejected(tmp_path: Path) -> None:
	"""Mirrors `test-change-ok:` / `complexity-ok:` elsewhere: the reason is REQUIRED."""
	path_file = _test_file(
		tmp_path,
		'import pytest\n\n\n@pytest.fixture(scope="module")  # fixture-scope-ok:\n'
		"def shared():\n\treturn {}\n",
	)

	assert len(gate.file_problems(path_file)) == 1


def test_a_dynamic_scope_value_is_not_flagged(tmp_path: Path) -> None:
	"""A `scope=` computed from a variable is not a decidable literal — not flagged.

	Not a loophole: anything dynamic enough to dodge this proxy is unusual enough that a
	human reviewing the diff will notice it on its own merits.
	"""
	path_file = _test_file(
		tmp_path,
		'import pytest\n\nSTR_SCOPE = "module"\n\n\n'
		"@pytest.fixture(scope=STR_SCOPE)\ndef shared():\n\treturn {}\n",
	)

	assert gate.file_problems(path_file) == []


def test_an_unparsable_file_raises_rather_than_reporting_clean(tmp_path: Path) -> None:
	"""A file the gate cannot parse must be a finding, never silently clean."""
	path_file = _test_file(tmp_path, "def f(:\n")

	with pytest.raises(gate.UnparsableFileError):
		gate.file_problems(path_file)


def test_audit_mode_fails_when_discovery_matches_nothing(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Zero discovered test files is a FAILURE — a renamed `tests/` layout must not go green."""
	monkeypatch.setattr(gate, "PATH_ROOT", tmp_path)

	assert gate.main([]) == 1


def test_audit_mode_passes_and_reports_the_count(
	tmp_path: Path,
	monkeypatch: pytest.MonkeyPatch,
	capsys: pytest.CaptureFixture[str],
) -> None:
	"""On success the gate prints how many files it checked, rather than staying silent."""
	path_tests = tmp_path / "tests" / "unit"
	path_tests.mkdir(parents=True)
	_test_file(path_tests, "import pytest\n\n\n@pytest.fixture\ndef f():\n\treturn {}\n")
	monkeypatch.setattr(gate, "PATH_ROOT", tmp_path)

	gate.main([])
	assert "1 file(s) checked" in capsys.readouterr().out


def test_audit_mode_reports_a_violation_without_the_success_line(
	tmp_path: Path,
	monkeypatch: pytest.MonkeyPatch,
	capsys: pytest.CaptureFixture[str],
) -> None:
	"""A widened scope fails the gate and the output carries the finding, not the success count."""
	path_tests = tmp_path / "tests" / "unit"
	path_tests.mkdir(parents=True)
	_test_file(
		path_tests,
		'import pytest\n\n\n@pytest.fixture(scope="module")\ndef shared():\n\treturn {}\n',
	)
	monkeypatch.setattr(gate, "PATH_ROOT", tmp_path)

	int_code = gate.main([])
	str_out = capsys.readouterr().out
	assert (int_code, "shared()" in str_out, "file(s) checked" in str_out) == (1, True, False)


def test_audit_mode_exits_zero_on_a_clean_tree(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""A tree with only a bare fixture decorator exits 0."""
	path_tests = tmp_path / "tests" / "unit"
	path_tests.mkdir(parents=True)
	_test_file(path_tests, "import pytest\n\n\n@pytest.fixture\ndef f():\n\treturn {}\n")
	monkeypatch.setattr(gate, "PATH_ROOT", tmp_path)

	assert gate.main([]) == 0


def test_audit_mode_fails_on_a_real_violation_end_to_end(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""The finding must reach the exit code, not just `file_problems`' return value."""
	path_tests = tmp_path / "tests" / "unit"
	path_tests.mkdir(parents=True)
	_test_file(
		path_tests,
		'import pytest\n\n\n@pytest.fixture(scope="session")\ndef f():\n\treturn {}\n',
	)
	monkeypatch.setattr(gate, "PATH_ROOT", tmp_path)

	assert gate.main([]) == 1
