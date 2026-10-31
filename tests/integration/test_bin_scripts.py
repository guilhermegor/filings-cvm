"""Integration tests for the project's shared ``bin/`` shell seams.

Bash scripts have no conventional unit test, so this project maps the
tests-with-every-change rule onto shell like this:

- **Unit gate** = ``shellcheck --severity=warning --exclude=SC1091`` + ``bash -n``
  (run by ``bin/lint_shell.sh`` and the ``lint-shell`` pre-commit hook).
- **Integration** = invoke the script via ``subprocess`` and assert on observable
  behaviour (exit code, a created file/dir, a status line) — this module.

See ``tests/CLAUDE.md`` (Testing shell scripts) for the convention. Three seams are
covered: ``bin/poetry_exec.sh`` (the Poetry resolver wrapper every recipe routes
through), ``bin/precommit.sh`` (hook install that must skip gracefully off a git
work tree instead of aborting ``init``), and ``bin/lint_actions.sh`` (the workflow
schema gate, with the negative control that proves it rejects the defect it exists for).
"""

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest


# --------------------------
# Module Utilities
# --------------------------


def _bin_script(str_name: str) -> Path:
	"""Return the absolute path to a script under the repository's ``bin/``.

	Parameters
	----------
	str_name : str
		The script filename, e.g. ``poetry_exec.sh``.

	Returns
	-------
	pathlib.Path
		Absolute path to ``bin/<str_name>`` at the repository root.
	"""
	return Path(__file__).resolve().parents[2] / "bin" / str_name


def _env_without_git() -> dict[str, str]:
	"""Return the current environment minus every ``GIT_*`` variable.

	A hook run during ``git commit`` in a linked worktree exports the git-dir variable. Inherited
	by a child process, it makes ``rev-parse`` report "inside a work tree" from an unrelated tmp
	dir, and makes ``git init`` re-initialise the CALLER's repository, writing
	``core.bare=true`` into the shared config and leaving the main checkout unusable.

	Returns
	-------
	dict of {str: str}
		A copy of ``os.environ`` with the ``GIT_*`` keys removed.
	"""
	return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _run(
	str_script: str,
	*args: str,
	cwd: Path | None = None,
	dict_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
	"""Run a ``bin/`` script via bash and capture stdout/stderr separately.

	Parameters
	----------
	str_script : str
		The script filename under ``bin/``.
	args : str
		Arguments forwarded to the script.
	cwd : pathlib.Path or None, optional
		Working directory to run from; defaults to the current directory.
	dict_env : dict of {str: str} or None, optional
		Extra environment variables layered on top of the current environment; ``None``
		inherits the environment unchanged.

	Returns
	-------
	subprocess.CompletedProcess[str]
		The finished process with decoded ``stdout`` and ``stderr``.
	"""
	str_bash = shutil.which("bash") or "bash"
	dict_full_env = _env_without_git()
	dict_full_env.update(dict_env or {})
	# The argument vector is constant and trusted -- a resolved bash plus the repo's own
	# script -- with no untrusted input interpolated, so the bandit subprocess warning is
	# a false positive here.
	return subprocess.run(  # noqa: S603
		[str_bash, str(_bin_script(str_script)), *args],
		capture_output=True,
		text=True,
		check=False,
		cwd=str(cwd) if cwd is not None else None,
		env=dict_full_env,
	)


# --------------------------
# bin/poetry_exec.sh
# --------------------------


def test_poetry_exec_no_args_exits_with_usage_error() -> None:
	"""No arguments yields exit code 2 and a usage message routed to stderr."""
	cls_result = _run("poetry_exec.sh")

	assert cls_result.returncode == 2
	assert "Usage" in cls_result.stderr
	assert cls_result.stdout == ""


def test_poetry_exec_version_keeps_stdout_clean() -> None:
	"""``version -s`` returns only the version on stdout; chatter goes to stderr."""
	cls_result = _run("poetry_exec.sh", "version", "-s")
	if cls_result.returncode != 0:
		pytest.skip("Poetry could not be resolved -- offline/CI integration guard only")

	# stdout is exactly the project version -- no resolution chatter leaked in.
	str_version = cls_result.stdout.strip()
	assert str_version != ""
	assert "\n" not in str_version
	assert "Detected OS" not in cls_result.stdout

	# The resolution status the wrapper emits lands on stderr, not stdout.
	assert "Detected OS" in cls_result.stderr


# --------------------------
# bin/precommit.sh
# --------------------------


def test_precommit_skips_gracefully_off_git_tree(tmp_path: Path) -> None:
	"""Run outside a git work tree, the script skips without aborting or creating a repo.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest-provided throwaway directory used as a non-git work tree.
	"""
	cls_result = _run("precommit.sh", cwd=tmp_path)

	# Skip-gracefully default -- init must still complete, so exit 0.
	assert cls_result.returncode == 0
	# No repository is fabricated; the template default never runs git init.
	assert not (tmp_path / ".git").exists()
	# The skip is announced, so a missing repo is visible, not silent.
	str_output = cls_result.stdout + cls_result.stderr
	assert "skipping pre-commit hooks" in str_output


def test_precommit_registers_safe_directory_for_shared_worktree(tmp_path: Path) -> None:
	"""A dubious-ownership work tree self-heals: the script registers a git safe.directory.

	Simulates a shared / network checkout owned by another user via
	``GIT_TEST_ASSUME_DIFFERENT_OWNER=1`` plus a throwaway global git config, then asserts the
	script registered the tree (git's own suggested path) instead of mis-detecting it as "no
	repo". The final hook-install step may fail offline (no Poetry), but the safe.directory
	write happens first in ``ensure_git_repo``, so the assertion holds regardless of exit code.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest throwaway dir; a real git work tree is initialised inside it.
	"""
	str_git = shutil.which("git")
	if str_git is None:
		pytest.skip("git not available -- integration guard only")

	path_repo = tmp_path / "repo"
	path_repo.mkdir()
	path_home = tmp_path / "home"
	path_home.mkdir()
	path_global_cfg = path_home / ".gitconfig"
	# A real work tree; the throwaway HOME/config isolates the global safe.directory write.
	subprocess.run(  # noqa: S603
		[str_git, "init", "-q", str(path_repo)], check=True, env=_env_without_git()
	)

	dict_env = {
		"GIT_TEST_ASSUME_DIFFERENT_OWNER": "1",
		"GIT_CONFIG_GLOBAL": str(path_global_cfg),
		"HOME": str(path_home),
	}
	cls_result = _run("precommit.sh", cwd=path_repo, dict_env=dict_env)
	str_output = cls_result.stdout + cls_result.stderr
	if "dubious ownership" not in str_output and not path_global_cfg.exists():
		pytest.skip("git build does not honour GIT_TEST_ASSUME_DIFFERENT_OWNER -- guard only")

	# The throwaway global config now holds git's own suggested path, which proves the tree
	# resolved and init could keep going instead of the probe misreading it as absent.
	str_cfg = path_global_cfg.read_text(encoding="utf-8") if path_global_cfg.exists() else ""
	assert "safe" in str_cfg
	assert str(path_repo) in str_cfg or "%(prefix)" in str_cfg
	# The self-heal never fabricates a repo and never emits the "no git repo" skip.
	assert "No git repository here" not in str_output


# --------------------------
# bin/lint_actions.sh
# --------------------------


def _skip_without_actionlint() -> None:
	"""Skip the calling test when neither a venv nor a system ``actionlint`` resolves.

	The wrapper skips gracefully (exit 0) on a box without the linter — right locally,
	but it means "passed" cannot be read as "linted". These tests therefore assert on a
	real run or not at all.
	"""
	if shutil.which("actionlint") is not None:
		return
	cls_probe = subprocess.run(  # noqa: S603 — constant argv, no untrusted input
		[shutil.which("poetry") or "poetry", "run", "actionlint", "--version"],
		capture_output=True,
		text=True,
		check=False,
	)
	if cls_probe.returncode != 0:
		pytest.skip("actionlint unavailable -- integration guard only")


def test_lint_actions_passes_on_the_repository_workflows() -> None:
	"""Every workflow in the repo passes the schema gate, and the run is not vacuous.

	The second assertion is the one that matters: ``actionlint`` exits 0 when handed no
	files, so a wrapper whose discovery silently matched nothing would report success
	forever. The status line carries the count precisely so that cannot hide.
	"""
	_skip_without_actionlint()
	cls_result = _run("lint_actions.sh")
	str_output = cls_result.stdout + cls_result.stderr

	assert cls_result.returncode == 0, str_output
	assert "workflow(s)" in str_output
	assert not re.search(r"(?<!\d)0 workflow\(s\)", str_output)


def test_lint_actions_rejects_a_trigger_that_is_not_a_workflow_event(tmp_path: Path) -> None:
	"""The gate fails on ``pull_request_review_thread`` — the defect that motivated it.

	Negative control, and the whole point of the gate: this file is **valid YAML** and
	passes ``yamllint``, so the only tool that can tell it apart from a working workflow
	is the schema linter. In #217 the real thing reached CI and GitHub rejected the file
	outright — the workflow did not run at all, which reads as a merely slow gate rather
	than a dead one.

	Runs ``actionlint`` directly on a synthetic file rather than through the wrapper: the
	wrapper lints the repo's own (green) workflows, so the defect has to be introduced
	somewhere it cannot corrupt the working tree.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest-provided scratch directory holding the synthetic workflow.
	"""
	_skip_without_actionlint()
	path_workflow = tmp_path / "broken.yaml"
	path_workflow.write_text(
		"name: Broken\n"
		"on:\n"
		"  pull_request_review_thread:\n"
		"    types: [resolved, unresolved]\n"
		"jobs:\n"
		"  noop:\n"
		"    runs-on: ubuntu-latest\n"
		"    steps:\n"
		"      - run: echo hi\n",
		encoding="utf-8",
	)

	str_actionlint = shutil.which("actionlint")
	list_argv = (
		[str_actionlint, str(path_workflow)]
		if str_actionlint is not None
		else [shutil.which("poetry") or "poetry", "run", "actionlint", str(path_workflow)]
	)
	cls_result = subprocess.run(  # noqa: S603 — constant argv plus a pytest tmp path
		list_argv, capture_output=True, text=True, check=False
	)

	assert cls_result.returncode != 0
	assert "unknown Webhook event" in cls_result.stdout + cls_result.stderr


# --------------------------
# bin/quality_ratchet.py, bin/check_required_checks_sync.py, bin/check_coverage_floor.py
# --------------------------


def _run_python(
	path_script: Path, *args: str, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
	"""Run a Python ``bin/`` script with this interpreter, capturing its output.

	Parameters
	----------
	path_script : pathlib.Path
		The script to run.
	args : str
		Arguments forwarded to the script.
	cwd : pathlib.Path or None, optional
		Working directory; defaults to the current directory.

	Returns
	-------
	subprocess.CompletedProcess[str]
		The finished process.
	"""
	return subprocess.run(  # noqa: S603 — this interpreter plus a repo script or tmp path
		[sys.executable, str(path_script), *args],
		capture_output=True,
		text=True,
		encoding="utf-8",  # the scripts print UTF-8 glyphs; Windows defaults to cp1252
		errors="replace",
		check=False,
		cwd=str(cwd) if cwd is not None else None,
		env=_env_without_git(),
	)


def _ratchet_in(tmp_path: Path, str_baseline: str) -> Path:
	"""Copy the ratchet into ``tmp_path/bin`` beside a synthetic baseline.

	Parameters
	----------
	tmp_path : pathlib.Path
		Scratch root standing in for the repository.
	str_baseline : str
		Content of the synthetic ``bin/quality_baseline.txt``.

	Returns
	-------
	pathlib.Path
		The copied ``quality_ratchet.py``.
	"""
	path_bin = tmp_path / "bin"
	path_bin.mkdir()
	(path_bin / "quality_baseline.txt").write_text(str_baseline, encoding="utf-8")
	return Path(shutil.copy(_bin_script("quality_ratchet.py"), path_bin))


_STR_FAKE_GUARD = (
	"import sys; print('a.py:1: too long'); print('    b.py:2: informational'); sys.exit(1)"
)


@pytest.mark.parametrize(
	("str_baseline", "int_expected_rc"),
	[
		("g 1 a.py\n", 0),
		("", 1),
		("g 2 a.py\n", 1),
		("other 1 a.py\n", 1),
	],
	ids=["held-at-baseline", "new-file-is-zero", "below-baseline-must-lower", "other-guard-rows"],
)
def test_quality_ratchet_holds_counts_in_both_directions(
	tmp_path: Path, str_baseline: str, int_expected_rc: int
) -> None:
	"""A file passes only at exactly its baseline; above fails, below fails ("lower it").

	The indented ``b.py`` line is informational and must not be counted — were it counted, the
	``held-at-baseline`` case (which baselines only ``a.py``) would fail.

	Parameters
	----------
	tmp_path : pathlib.Path
		Scratch root holding the copied ratchet and its baseline.
	str_baseline : str
		Synthetic baseline content.
	int_expected_rc : int
		Expected exit code.
	"""
	path_ratchet = _ratchet_in(tmp_path, str_baseline)
	cls_result = _run_python(path_ratchet, "g", sys.executable, "-c", _STR_FAKE_GUARD)

	assert cls_result.returncode == int_expected_rc, cls_result.stdout


def test_quality_ratchet_passes_through_a_guard_failure_with_no_finding(tmp_path: Path) -> None:
	"""A guard that fails without a recognisable finding (a crash) is never baselined away.

	Parameters
	----------
	tmp_path : pathlib.Path
		Scratch root holding the copied ratchet.
	"""
	path_ratchet = _ratchet_in(tmp_path, "")
	cls_result = _run_python(
		path_ratchet, "g", sys.executable, "-c", "import sys; print('boom'); sys.exit(3)"
	)

	assert (cls_result.returncode, cls_result.stdout.strip()) == (3, "boom")


def test_quality_ratchet_write_baseline_records_counts(tmp_path: Path) -> None:
	"""``--write-baseline`` replaces the guard's rows and keeps every other guard's rows.

	Parameters
	----------
	tmp_path : pathlib.Path
		Scratch root holding the copied ratchet and its baseline.
	"""
	path_ratchet = _ratchet_in(tmp_path, "# header\nother 4 z.py\ng 9 a.py\n")
	_run_python(path_ratchet, "g", "--write-baseline", sys.executable, "-c", _STR_FAKE_GUARD)

	str_written = (tmp_path / "bin" / "quality_baseline.txt").read_text(encoding="utf-8")
	assert str_written == "# header\nother 4 z.py\ng 1 a.py\n"


_STR_WORKFLOW = (
	"name: Tests\n"
	"on:\n"
	"  pull_request:\n"
	"    branches: [main]\n"
	"jobs:\n"
	"  test:\n"
	"    name: Run (${{{{ matrix.os }}}})\n"
	"{str_if}"
	"    runs-on: ubuntu-latest\n"
	"    strategy:\n"
	"      matrix:\n"
	"        os: [ubuntu-latest, macos-latest]\n"
	"    steps:\n"
	"      - run: echo hi\n"
)


@pytest.mark.parametrize(
	("str_if", "int_expected_rc"),
	[("", 0), ("    if: github.event_name == 'push'\n", 1)],
	ids=["unconditional-job-on-main-filter", "conditional-job"],
)
def test_required_checks_sync_needs_an_unconditional_emitter(
	tmp_path: Path, str_if: str, int_expected_rc: int
) -> None:
	"""A required context passes only when a job running on every PR into main emits it.

	The ``branches: [main]`` filter is deliberately present in both cases: it must not, by
	itself, make the job conditional (the ruleset only judges PRs into ``main``).

	Parameters
	----------
	tmp_path : pathlib.Path
		Scratch root holding the synthetic workflow and required list.
	str_if : str
		The job's ``if:`` line, or empty for none.
	int_expected_rc : int
		Expected exit code.
	"""
	path_workflows = tmp_path / "workflows"
	path_workflows.mkdir()
	(path_workflows / "tests.yaml").write_text(
		_STR_WORKFLOW.format(str_if=str_if), encoding="utf-8"
	)
	path_list = tmp_path / "required.txt"
	path_list.write_text("# comment\nRun (macos-latest)\n", encoding="utf-8")

	cls_result = _run_python(
		_bin_script("check_required_checks_sync.py"),
		"--workflows",
		str(path_workflows),
		"--required-list",
		str(path_list),
	)

	assert cls_result.returncode == int_expected_rc, cls_result.stderr


@pytest.mark.parametrize(
	("str_omit", "int_expected_rc"),
	[("src/*/_internal/*", 0), ("src/*", 1)],
	ids=["internal-only", "section-swallowed"],
)
def test_coverage_floor_rejects_an_omit_that_swallows_a_section(
	tmp_path: Path, str_omit: str, int_expected_rc: int
) -> None:
	"""An omit glob matching a function-bearing ``ingestion/`` module fails the floor.

	Parameters
	----------
	tmp_path : pathlib.Path
		Scratch root standing in for the repository.
	str_omit : str
		The ``[run] omit`` pattern under test.
	int_expected_rc : int
		Expected exit code.
	"""
	path_section = tmp_path / "src" / "pkg" / "ingestion"
	path_section.mkdir(parents=True)
	(path_section / "reader.py").write_text("def read():\n    return 1\n", encoding="utf-8")
	(tmp_path / ".coveragerc").write_text(f"[run]\nomit =\n    {str_omit}\n", encoding="utf-8")

	cls_result = _run_python(_bin_script("check_coverage_floor.py"), cwd=tmp_path)

	assert cls_result.returncode == int_expected_rc, cls_result.stderr
