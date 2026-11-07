"""Witness for the `RET` (flake8-return) rule family adopted in ``ruff.toml`` (blueprintx#426).

**Why this exists.** `RET505` (unnecessary `else` after `return`) was measured at 0 findings
across `src/ bin/ tests/ optional/` at adoption time — the codebase already writes early
returns everywhere. A gate that has never fired is indistinguishable from a gate that never
ran, so a should-fail witness is the only thing that tells the two apart. This test invokes
``ruff`` directly (not the shipped config, which also enables `ANN`/`D`/… and would drown the
signal in unrelated findings on a two-line fixture) with `--isolated --select RET505` against
two synthetic fixtures: one that MUST fail, one that MUST pass.
"""

from pathlib import Path
import shutil
import subprocess

import pytest


tomllib = pytest.importorskip("tomllib", reason="tomllib is stdlib only from Python 3.11")


_BAD_SOURCE = "def choose(flag: bool) -> int:\n\tif flag:\n\t\treturn 1\n\telse:\n\t\treturn 2\n"
_GOOD_SOURCE = "def choose(flag: bool) -> int:\n\tif flag:\n\t\treturn 1\n\treturn 2\n"

_STR_RUFF = shutil.which("ruff")

_PATH_RUFF_TOML = Path(__file__).parents[2] / "ruff.toml"


def _run_ruff_ret505(path_file: Path) -> subprocess.CompletedProcess[str]:
	"""Run ``ruff check --isolated --select RET505`` against a single file.

	Parameters
	----------
	path_file : pathlib.Path
		The Python source file to check.

	Returns
	-------
	subprocess.CompletedProcess[str]
		The completed ruff invocation (exit code + captured output).
	"""
	list_argv = [
		str(_STR_RUFF),
		"check",
		"--isolated",
		"--select",
		"RET505",
		"--output-format",
		"concise",
		str(path_file),
	]
	return subprocess.run(list_argv, capture_output=True, text=True, check=False)  # noqa: S603


@pytest.mark.skipif(_STR_RUFF is None, reason="ruff is not on PATH")
def test_ret505_flags_else_after_return(tmp_path: Path) -> None:
	"""An `if: return … else: return …` shape must be rejected by RET505."""
	path_file = tmp_path / "bad.py"
	path_file.write_text(_BAD_SOURCE, encoding="utf-8")
	cls_result = _run_ruff_ret505(path_file)
	assert cls_result.returncode == 1


@pytest.mark.skipif(_STR_RUFF is None, reason="ruff is not on PATH")
def test_ret505_names_the_rule_it_flags(tmp_path: Path) -> None:
	"""The rejection names RET505, so a crash (also non-zero) is told apart."""
	path_file = tmp_path / "bad.py"
	path_file.write_text(_BAD_SOURCE, encoding="utf-8")
	assert "RET505" in _run_ruff_ret505(path_file).stdout


@pytest.mark.skipif(_STR_RUFF is None, reason="ruff is not on PATH")
def test_ret505_allows_early_return(tmp_path: Path) -> None:
	"""An early-return shape (no `else` after `return`) must pass RET505 clean."""
	path_file = tmp_path / "good.py"
	path_file.write_text(_GOOD_SOURCE, encoding="utf-8")
	cls_result = _run_ruff_ret505(path_file)
	assert cls_result.returncode == 0


@pytest.mark.skipif(_STR_RUFF is None, reason="ruff is not on PATH")
def test_ret505_stays_silent_on_an_early_return(tmp_path: Path) -> None:
	"""The early-return shape produces no RET505 output."""
	path_file = tmp_path / "good.py"
	path_file.write_text(_GOOD_SOURCE, encoding="utf-8")
	assert "RET505" not in _run_ruff_ret505(path_file).stdout


@pytest.mark.xfail(
	reason="ruff.toml does not select RET yet; adoption is owned by #373",
	raises=AssertionError,
	strict=True,
)
def test_shipped_config_selects_ret() -> None:
	"""``ruff.toml`` must select `RET`, which the `--isolated` runs above cannot witness.

	⚠️ The two tests above pass `--select RET505` on the command line, so they answer "does
	this ruff build implement RET505", never "is RET enabled for this project". Dropping
	`"RET"` from ``[lint].select`` would disable the rule everywhere and leave both of them
	green — the silent hole this assertion closes.
	"""
	dict_config = tomllib.loads(_PATH_RUFF_TOML.read_text(encoding="utf-8"))
	assert "RET" in dict_config["lint"]["select"]
