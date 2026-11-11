"""Unit tests for #401: gate scripts are judged from the base ref, not the PR checkout."""

import importlib.util
import os
from pathlib import Path
import subprocess

import pytest
import yaml


_ROOT = Path(__file__).resolve().parents[2]
_STR_GATE_RUN = "check_review_threads.py"


def _load_integrity() -> object:
	"""Import ``bin/check_gate_integrity.py`` as a module."""
	cls_spec = importlib.util.spec_from_file_location(
		"_check_gate_integrity_401", _ROOT / "bin" / "check_gate_integrity.py"
	)
	assert cls_spec is not None
	assert cls_spec.loader is not None
	cls_module = importlib.util.module_from_spec(cls_spec)
	cls_spec.loader.exec_module(cls_module)
	return cls_module


def _steps() -> list:
	"""Return the review-threads workflow's steps."""
	path_wf = _ROOT / ".github" / "workflows" / "review_threads.yaml"
	return yaml.safe_load(path_wf.read_text(encoding="utf-8"))["jobs"]["review-threads"]["steps"]


def _gate_step_command() -> str:
	"""Return the ``run`` line that executes the review-threads gate."""
	return next(d["run"] for d in _steps() if _STR_GATE_RUN in d.get("run", ""))


_STR_BASE_GATE = ".gate-base/bin/check_review_threads.py"
_STR_GATE_SCRIPT = "bin/check_review_threads.py"
_DICT_GIT_IDENTITY = {
	"GIT_AUTHOR_NAME": "test",
	"GIT_AUTHOR_EMAIL": "test@example.com",
	"GIT_COMMITTER_NAME": "test",
	"GIT_COMMITTER_EMAIL": "test@example.com",
}


@pytest.mark.parametrize(
	("str_command", "bool_from_base"),
	[
		(_gate_step_command(), True),
		("python bin/check_review_threads.py", False),
		(f"python bin/check_review_threads.py && echo {_STR_BASE_GATE}", False),
	],
)
def test_gate_command_runs_from_the_base_checkout(str_command: str, bool_from_base: bool) -> None:
	"""The whole gate command runs the base-ref script, not the PR's ``bin/`` copy."""
	assert (str_command.split() == ["python", _STR_BASE_GATE]) is bool_from_base


def _base_checkout_step() -> dict:
	"""Return the workflow step that checks the base ref out into ``.gate-base``."""
	return next(d for d in _steps() if d.get("with", {}).get("path") == ".gate-base")


def test_base_checkout_step_uses_the_checkout_action() -> None:
	"""The ``.gate-base`` step is an ``actions/checkout`` step, not an arbitrary action."""
	assert _base_checkout_step()["uses"].startswith("actions/checkout@")


def test_base_checkout_step_targets_the_resolved_base_ref() -> None:
	"""The ``.gate-base`` checkout pins the resolved base ref."""
	assert _base_checkout_step()["with"]["ref"] == "${{ env.REVIEW_POLICY_BASE_REF }}"


def test_stale_run_cleanup_runs_from_the_base_checkout() -> None:
	"""The stale-run cleanup script also comes from ``.gate-base``, not the PR checkout."""
	str_run = next(d["run"] for d in _steps() if "rerun_stale_gate_runs.sh" in d.get("run", ""))
	str_call = next(s for s in str_run.splitlines() if "rerun_stale_gate_runs.sh" in s)
	assert str_call.split()[-2:] == ["bash", ".gate-base/bin/rerun_stale_gate_runs.sh"]


@pytest.mark.parametrize(("str_new", "bool_flagged"), [("x = 2\n", True), ("x = 1\n", False)])
def test_modified_gate_script_is_flagged(str_new: str, bool_flagged: bool) -> None:
	"""An edited ``bin/check_*`` script is a finding; an identical one is not."""
	cls_gate = _load_integrity()
	list_problems = cls_gate.gate_script_problems("x = 1\n", str_new, _STR_GATE_SCRIPT)
	assert bool(list_problems) is bool_flagged


def _git(path_repo: Path, *tuple_args: str) -> None:
	"""Run one git command in the fixture repository with a fixed identity."""
	subprocess.run(  # noqa: S603
		["git", *tuple_args],  # noqa: S607
		cwd=path_repo,
		env={**os.environ, **_DICT_GIT_IDENTITY},
		check=True,
		capture_output=True,
	)


_STR_BASE_SCRIPT = "x = 1\n" * 20
_STR_EDITED_SCRIPT = "x = 1\n" * 19 + "x = 2\n"
_STR_RENAMED_SCRIPT = "bin/check_review_threads_v2.py"


def _edit_in_place(path_repo: Path) -> None:
	"""Change one line of the gate script at its original path."""
	(path_repo / _STR_GATE_SCRIPT).write_text(_STR_EDITED_SCRIPT, encoding="utf-8")


def _rename_and_edit(path_repo: Path) -> None:
	"""Rename the gate script and change one line, so git pairs the two as a rename."""
	_git(path_repo, "mv", _STR_GATE_SCRIPT, _STR_RENAMED_SCRIPT)
	(path_repo / _STR_RENAMED_SCRIPT).write_text(_STR_EDITED_SCRIPT, encoding="utf-8")


def _leave_untouched(path_repo: Path) -> None:
	"""Leave the gate script as committed on ``main``."""


_DICT_CHANGES = {
	"edit": _edit_in_place,
	"rename_and_edit": _rename_and_edit,
	"none": _leave_untouched,
}


def _stage_branch_change(path_repo: Path, str_change: str) -> None:
	"""Commit a gate script on ``main``, branch off, and commit ``str_change`` to it."""
	_git(path_repo, "init", "-q", "-b", "main")
	path_script = path_repo / _STR_GATE_SCRIPT
	path_script.parent.mkdir(parents=True)
	path_script.write_text(_STR_BASE_SCRIPT, encoding="utf-8")
	_git(path_repo, "add", "-A")
	_git(path_repo, "commit", "-q", "-m", "base")
	_git(path_repo, "checkout", "-q", "-b", "feature")
	(path_repo / "README.md").write_text("unrelated\n", encoding="utf-8")
	_DICT_CHANGES[str_change](path_repo)
	_git(path_repo, "add", "-A")
	_git(path_repo, "commit", "-q", "-m", "change")


@pytest.mark.parametrize(
	("str_change", "int_exit"),
	[("edit", 1), ("rename_and_edit", 1), ("none", 0)],
)
def test_main_fails_an_unjustified_gate_script_change(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch, str_change: str, int_exit: int
) -> None:
	"""Through ``main``: an edited or renamed-and-edited gate script fails with no reason."""
	_stage_branch_change(tmp_path, str_change)
	monkeypatch.delenv("CI", raising=False)
	monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
	monkeypatch.delenv("GATE_CHANGE_OK", raising=False)
	monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)
	monkeypatch.chdir(tmp_path)
	assert _load_integrity().main([]) == int_exit
