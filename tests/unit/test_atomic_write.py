"""Unit tests for the atomic output helper and the writers' use of it."""

import inspect
from pathlib import Path
import re

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


def test_atomic_write_bytes_failure_keeps_old_target(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""A fault during the write leaves the previous file byte-identical."""
	path_out = tmp_path / "out.xml"
	path_out.write_bytes(b"old")

	def _boom(_fd: int) -> None:
		raise OSError("disk full")

	monkeypatch.setattr(atomic_write.os, "fsync", _boom)
	with pytest.raises(OSError, match="disk full"):
		atomic_write_bytes(path_out, b"new")
	assert path_out.read_bytes() == b"old"


def test_atomic_write_bytes_failure_leaves_no_temp_file(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""A fault during the write leaves no temp file in the directory."""
	path_out = tmp_path / "out.xml"

	def _boom(*_args: object) -> None:
		raise OSError("replace failed")

	monkeypatch.setattr(atomic_write.os, "replace", _boom)
	with pytest.raises(OSError, match="replace failed"):
		atomic_write_bytes(path_out, b"new")
	assert list(tmp_path.iterdir()) == []


def test_atomic_write_bytes_temp_file_is_in_destination_directory(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""The temp file sits beside the target so os.replace stays on one filesystem."""
	list_src: list[Path] = []
	fn_replace = atomic_write.os.replace

	def _spy(src: str, dst: Path) -> None:
		list_src.append(Path(src))
		fn_replace(src, dst)

	monkeypatch.setattr(atomic_write.os, "replace", _spy)
	atomic_write_bytes(tmp_path / "out.xml", b"x")
	assert list_src[0].parent == tmp_path


def test_writer_discovery_finds_every_writer_module() -> None:
	"""The guard below must not be a placebo that sweeps zero writers."""
	assert len(_writer_modules()) >= 9


@pytest.mark.parametrize("str_file", _writer_modules())
def test_writer_module_never_writes_its_output_directly(str_file: str) -> None:
	"""Writers must route output through atomic_write_bytes."""
	assert _DIRECT_WRITE.search(Path(str_file).read_text(encoding="utf-8")) is None
