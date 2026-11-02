"""The autouse fixture in ``tests/conftest.py`` must hide a git hook's ``GIT_*`` variables."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest


# Spelled out on purpose: deriving it from the fixture's own list would let a removed name
# silently drop its own test case.
_EXPECTED_HIDDEN = (
	"GIT_DIR",
	"GIT_WORK_TREE",
	"GIT_INDEX_FILE",
	"GIT_OBJECT_DIRECTORY",
	"GIT_ALTERNATE_OBJECT_DIRECTORIES",
	"GIT_COMMON_DIR",
	"GIT_PREFIX",
	"GIT_CONFIG_PARAMETERS",
)

_INNER = "import os\ndef test_inner():\n\tassert os.environ.get({name!r}) is None\n"


@pytest.mark.parametrize("name", _EXPECTED_HIDDEN)
def test_git_hook_variable_is_hidden_from_tests(name: str, tmp_path: Path) -> None:
	"""A test run with ``name`` set in the outer environment sees it unset."""
	(tmp_path / "test_inner.py").write_text(_INNER.format(name=name))
	conftest = Path(__file__).resolve().parents[1] / "conftest.py"
	(tmp_path / "conftest.py").write_text(conftest.read_text())
	# An inherited PYTEST_ADDOPTS filter would deselect the inner test and flip the exit code.
	env = {**os.environ, name: str(tmp_path / "sentinel")}
	env.pop("PYTEST_ADDOPTS", None)
	result = subprocess.run(  # noqa: S603  (fixed argv, no shell)
		[sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(tmp_path)],
		env=env,
		capture_output=True,
		text=True,
		check=False,
	)
	assert result.returncode == 0, result.stdout + result.stderr
