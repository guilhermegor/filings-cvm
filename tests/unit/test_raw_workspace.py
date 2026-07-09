"""Unit tests for the raw-artifact workspace seam.

The seam decides whether a reader's downloaded artifact survives the read: discarded when
``path_raw`` is ``None``, persisted when it is a path. Both branches are exercised here so
no reader has to re-test them.
"""

from pathlib import Path

import pytest

from filings_cvm._internal.utils.raw_workspace import raw_workspace


def test_workspace_without_path_yields_a_directory_that_is_removed_on_exit() -> None:
	"""A ``None`` path yields a real temp directory, destroyed once the block exits."""
	with raw_workspace() as path_dir:
		assert path_dir.is_dir()
		(path_dir / "artifact.zip").write_bytes(b"raw")
		path_seen = path_dir

	assert not path_seen.exists()


def test_workspace_with_path_creates_it_and_keeps_its_contents(tmp_path: Path) -> None:
	"""A given path is created (parents included) and its contents outlive the block.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest-provided scratch directory.
	"""
	path_raw = tmp_path / "bronze" / "cvm" / "202504"

	with raw_workspace(path_raw) as path_dir:
		assert path_dir == path_raw
		(path_dir / "artifact.zip").write_bytes(b"raw")

	assert (path_raw / "artifact.zip").read_bytes() == b"raw"


def test_workspace_accepts_an_existing_directory(tmp_path: Path) -> None:
	"""Reusing an existing directory is not an error (``exist_ok``).

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest-provided scratch directory, already present.
	"""
	with raw_workspace(tmp_path) as path_dir:
		assert path_dir == tmp_path


def test_workspace_rejects_a_wrong_argument_type() -> None:
	"""The ``@type_checker`` decorator rejects a string where a Path is declared."""
	with pytest.raises(TypeError), raw_workspace("not-a-path"):  # type: ignore[arg-type]
		pass
