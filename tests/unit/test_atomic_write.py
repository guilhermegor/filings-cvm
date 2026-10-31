"""Unit tests for the atomic output helper and the writers' use of it."""

import contextlib
import inspect
import os
from pathlib import Path
import re
import stat

import pytest

from filings_cvm import submission
from filings_cvm._internal.utils import atomic_write
from filings_cvm._internal.utils.atomic_write import atomic_write_bytes


_DIRECT_WRITE = re.compile(r"\bopen\(|\.write_bytes\(|\.write_text\(")


def _writer_modules() -> list[str]:
	"""Return the source file of each public submission writer class."""
	set_files = {
		inspect.getsourcefile(obj)
		for name in submission.__all__
		if inspect.isclass(obj := getattr(submission, name)) and hasattr(obj, "export")
	}
	return sorted(str(path) for path in set_files if path)


def test_atomic_write_bytes_creates_file_with_exact_bytes(tmp_path: Path) -> None:
	"""A successful write lands the exact payload."""
	path_out = tmp_path / "out.xml"
	atomic_write_bytes(path_out, b"\xe7\xe3<x/>")
	assert path_out.read_bytes() == b"\xe7\xe3<x/>"


def test_atomic_write_bytes_replaces_existing_target(tmp_path: Path) -> None:
	"""A successful write replaces a previous file completely."""
	path_out = tmp_path / "out.xml"
	path_out.write_bytes(b"old content that is longer")
	atomic_write_bytes(str(path_out), b"new")
	assert path_out.read_bytes() == b"new"


def _boom_fsync(_fd: int) -> None:
	"""Fail like a full disk."""
	raise OSError("disk full")


def _boom_replace(*_args: object) -> None:
	"""Fail like a broken rename."""
	raise OSError("replace failed")


@pytest.fixture
def path_after_failed_overwrite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
	"""Overwrite an existing file with fsync failing; return the target path."""
	path_out = tmp_path / "out.xml"
	path_out.write_bytes(b"old")
	monkeypatch.setattr(atomic_write.os, "fsync", _boom_fsync)
	with contextlib.suppress(OSError):
		atomic_write_bytes(path_out, b"new")
	return path_out


@pytest.fixture
def dir_after_failed_replace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
	"""Write a new file with os.replace failing; return the directory."""
	monkeypatch.setattr(atomic_write.os, "replace", _boom_replace)
	with contextlib.suppress(OSError):
		atomic_write_bytes(tmp_path / "out.xml", b"new")
	return tmp_path


def test_atomic_write_bytes_failure_raises(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""A fault during the write propagates to the caller."""
	monkeypatch.setattr(atomic_write.os, "fsync", _boom_fsync)
	with pytest.raises(OSError, match="disk full"):
		atomic_write_bytes(tmp_path / "out.xml", b"new")


def test_atomic_write_bytes_failure_keeps_old_target(path_after_failed_overwrite: Path) -> None:
	"""A fault during the write leaves the previous file byte-identical."""
	assert path_after_failed_overwrite.read_bytes() == b"old"


def test_atomic_write_bytes_failure_leaves_no_temp_file(
	dir_after_failed_replace: Path,
) -> None:
	"""A fault during the write leaves no temp file in the directory."""
	assert list(dir_after_failed_replace.iterdir()) == []


class _Spy:
	"""Record the first positional argument of every call, then delegate."""

	def __init__(self, fn: object) -> None:
		self.fn = fn
		self.list_first: list[object] = []

	def __call__(self, first: object, *rest: object) -> None:
		self.list_first.append(first)
		self.fn(first, *rest)


@pytest.fixture
def replace_spy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> _Spy:
	"""Spy on os.replace around one successful write."""
	spy = _Spy(atomic_write.os.replace)
	monkeypatch.setattr(atomic_write.os, "replace", spy)
	atomic_write_bytes(tmp_path / "out.xml", b"x")
	return spy


def test_atomic_write_bytes_temp_file_is_in_destination_directory(
	replace_spy: _Spy, tmp_path: Path
) -> None:
	"""The temp file sits beside the target so os.replace stays on one filesystem."""
	assert Path(str(replace_spy.list_first[0])).parent == tmp_path


@pytest.fixture
def fsync_spy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> _Spy:
	"""Spy on os.fsync around one successful write."""
	spy = _Spy(atomic_write.os.fsync)
	monkeypatch.setattr(atomic_write.os, "fsync", spy)
	atomic_write_bytes(tmp_path / "out.xml", b"x")
	return spy


def test_atomic_write_bytes_fsyncs_the_directory(fsync_spy: _Spy) -> None:
	"""The rename is made durable by an fsync on the parent directory."""
	assert len(fsync_spy.list_first) == 2


@pytest.fixture
def mode_written_under_umask_022(tmp_path: Path) -> int:
	"""Write one file under umask 022 and return its permission bits."""
	path_out = tmp_path / "out.xml"
	umask = os.umask(0o022)
	atomic_write_bytes(path_out, b"x")
	os.umask(umask)
	return stat.S_IMODE(path_out.stat().st_mode)


def test_atomic_write_bytes_uses_umask_default_mode(mode_written_under_umask_022: int) -> None:
	"""The file gets open()'s default permissions, not mkstemp's 0600."""
	assert mode_written_under_umask_022 == 0o644


def test_writer_discovery_finds_every_writer_module() -> None:
	"""The guard below must not be a placebo that sweeps zero writers."""
	assert len(_writer_modules()) >= 9


@pytest.mark.parametrize("str_file", _writer_modules())
def test_writer_module_never_writes_its_output_directly(str_file: str) -> None:
	"""Writers must route output through atomic_write_bytes."""
	assert _DIRECT_WRITE.search(Path(str_file).read_text(encoding="utf-8")) is None
