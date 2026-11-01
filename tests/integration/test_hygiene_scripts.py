"""Integration tests for the hygiene shell guards imported from BlueprintX (#295).

``bin/check_clean_index.sh`` and ``bin/check_secrets.sh`` are driven through ``subprocess`` and
asserted on observable behaviour (exit code), with a negative control for each. POSIX only: the
guards run on a developer box and the Linux CI job.
"""

import os
from pathlib import Path
import shutil
import subprocess

import pytest


pytestmark = pytest.mark.skipif(os.name != "posix", reason="bash guards run on POSIX hosts")

_BIN = Path(__file__).resolve().parents[2] / "bin"
_BASH = shutil.which("bash") or "bash"
_GIT = shutil.which("git") or "git"
_SYSTEM_PATH = "/usr/bin:/bin"


def _git_env() -> dict[str, str]:
	"""Return an environment with no inherited ``GIT_*`` variables."""
	return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _run_in(path_cwd: Path, str_script: str, *list_args: str, env: dict[str, str]) -> int:
	"""Run a ``bin/`` script from ``path_cwd`` and return its exit code."""
	list_cmd = [_BASH, str(_BIN / str_script), *list_args]
	return subprocess.run(  # noqa: S603 - constant, trusted argv
		list_cmd, cwd=path_cwd, env=env, capture_output=True, text=True, check=False
	).returncode


def _repo(path_dir: Path) -> Path:
	"""Create an empty git repository and return its path."""
	subprocess.run([_GIT, "init", "-q"], cwd=path_dir, env=_git_env(), check=True)  # noqa: S603
	return path_dir


def test_clean_index_passes_when_nothing_is_staged(tmp_path: Path) -> None:
	"""An empty index lets the push through."""
	assert _run_in(_repo(tmp_path), "check_clean_index.sh", env=_git_env()) == 0


def test_clean_index_blocks_a_staged_but_uncommitted_file(tmp_path: Path) -> None:
	"""A populated index means a commit was rejected, so the push is blocked."""
	path_repo = _repo(tmp_path)
	(path_repo / "a.txt").write_text("x\n", encoding="utf-8")
	subprocess.run([_GIT, "add", "a.txt"], cwd=path_repo, env=_git_env(), check=True)  # noqa: S603
	assert _run_in(path_repo, "check_clean_index.sh", env=_git_env()) == 1


def test_clean_index_is_a_no_op_outside_a_work_tree(tmp_path: Path) -> None:
	"""Outside a repository there is no index to inspect."""
	assert _run_in(tmp_path, "check_clean_index.sh", env=_git_env()) == 0


_GITLEAKS_IN_SYSTEM_DIR = shutil.which("gitleaks", path=_SYSTEM_PATH) is not None
_ENV_WITHOUT_GITLEAKS = {
	**{k: v for k, v in os.environ.items() if k != "GITLEAKS_REQUIRED"},
	"PATH": _SYSTEM_PATH,
}
_needs_no_system_gitleaks = pytest.mark.skipif(
	_GITLEAKS_IN_SYSTEM_DIR, reason="gitleaks lives in a system directory here"
)


@_needs_no_system_gitleaks
def test_secrets_skips_when_gitleaks_is_absent(tmp_path: Path) -> None:
	"""Locally, a missing scanner is a warning and exit 0."""
	assert _run_in(tmp_path, "check_secrets.sh", env=_ENV_WITHOUT_GITLEAKS) == 0


@_needs_no_system_gitleaks
def test_secrets_fails_when_gitleaks_is_required_but_absent(tmp_path: Path) -> None:
	"""In CI a skipped scanner reads as clean, so GITLEAKS_REQUIRED makes it a failure."""
	env = {**_ENV_WITHOUT_GITLEAKS, "GITLEAKS_REQUIRED": "1"}
	assert _run_in(tmp_path, "check_secrets.sh", env=env) == 1


def test_secrets_rejects_an_unknown_argument(tmp_path: Path) -> None:
	"""A typo in a flag must not silently scan nothing."""
	assert _run_in(tmp_path, "check_secrets.sh", "--bogus", env=dict(os.environ)) == 2
