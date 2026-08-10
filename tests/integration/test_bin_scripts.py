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
import shutil
import subprocess

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
	dict_full_env = {**os.environ, **dict_env} if dict_env else None
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
		[str_git, "init", "-q", str(path_repo)], check=True
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
	assert "0 workflow(s)" not in str_output


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
