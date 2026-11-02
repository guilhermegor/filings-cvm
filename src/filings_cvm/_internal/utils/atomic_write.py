"""Atomic file output for the submission writers.

A writer's destination must always be either the previous file or the complete new one,
never a partial write left behind by an I/O fault.
"""

from __future__ import annotations

import contextlib
import os
from pathlib import Path
import secrets

from filings_cvm._internal.utils.typing import type_checker


@type_checker
def atomic_write_bytes(path: str | Path, payload: bytes) -> None:
	"""Write ``payload`` to ``path`` atomically.

	The bytes go to a temp file in the destination's own directory (so ``os.replace`` stays
	on one filesystem), are flushed and fsynced, then replace the target. If the write,
	fsync or replace fails, the temp file is removed and a pre-existing target is left
	untouched. The directory fsync runs after the replace: if it fails, the new file is
	already in place and ``OSError`` is still raised.

	The caller therefore needs write permission on the destination's parent directory, not
	only on an existing target file. A pre-existing target keeps its permission bits; a new
	file gets the mode a plain ``open()`` would give (``0o666`` minus the umask).

	Parameters
	----------
	path : str | Path
		Destination file path.
	payload : bytes
		Exact bytes to write.

	Raises
	------
	OSError
		If the write, fsync or replace fails, or if the directory fsync fails after the
		replace (the target then already holds the new payload).
	"""
	path_dest = Path(path)
	path_tmp = path_dest.with_name(f".{path_dest.name}.{secrets.token_hex(8)}.tmp")
	# the kernel applies the umask to this 0o666 itself, so the process umask is never touched
	flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
	fd = os.open(path_tmp, flags, 0o666)
	try:
		_apply_dest_mode(path_tmp, path_dest)
		with os.fdopen(fd, "wb") as file_tmp:
			file_tmp.write(payload)
			file_tmp.flush()
			os.fsync(file_tmp.fileno())
		os.replace(path_tmp, path_dest)
	except BaseException:
		with contextlib.suppress(FileNotFoundError):
			os.unlink(path_tmp)
		raise
	_fsync_dir(path_dest.parent)


@type_checker
def _apply_dest_mode(path_tmp: Path, path_dest: Path) -> None:
	"""Give the still-empty temp file the existing destination's permission bits.

	Runs before any payload byte is written, so the payload is never readable under a wider
	mode than the final file. A missing destination leaves the ``0o666``-minus-umask default.

	Parameters
	----------
	path_tmp : Path
		Temp file, opened but not yet written.
	path_dest : Path
		Final destination, which may not exist yet.
	"""
	with contextlib.suppress(FileNotFoundError):
		os.chmod(path_tmp, os.stat(path_dest).st_mode & 0o7777)


@type_checker
def _fsync_dir(path_dir: Path) -> None:
	"""Fsync the directory so the rename survives a crash (POSIX; no-op elsewhere).

	Parameters
	----------
	path_dir : Path
		Directory holding the renamed file.
	"""
	if os.name != "posix":
		return
	fd = os.open(path_dir, os.O_RDONLY)
	try:
		os.fsync(fd)
	finally:
		os.close(fd)
