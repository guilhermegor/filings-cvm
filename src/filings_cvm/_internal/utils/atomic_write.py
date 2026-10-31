"""Atomic file output for the submission writers.

A writer's destination must always be either the previous file or the complete new one,
never a partial write left behind by an I/O fault.
"""

from __future__ import annotations

import contextlib
import os
from pathlib import Path
import tempfile

from filings_cvm._internal.utils.typing import type_checker


@type_checker
def atomic_write_bytes(path: str | Path, payload: bytes) -> None:
	"""Write ``payload`` to ``path`` atomically.

	The bytes go to a temp file in the destination's own directory (so ``os.replace`` stays
	on one filesystem), are flushed and fsynced, then replace the target. On any failure the
	temp file is removed and a pre-existing target is left untouched.

	Parameters
	----------
	path : str | Path
		Destination file path.
	payload : bytes
		Exact bytes to write.

	Raises
	------
	OSError
		If the write, fsync or replace fails.
	"""
	path_dest = Path(path)
	fd, str_tmp = tempfile.mkstemp(
		dir=path_dest.parent, prefix=f".{path_dest.name}.", suffix=".tmp"
	)
	try:
		with os.fdopen(fd, "wb") as file_tmp:
			file_tmp.write(payload)
			file_tmp.flush()
			os.fsync(file_tmp.fileno())
		os.replace(str_tmp, path_dest)
	except BaseException:
		with contextlib.suppress(FileNotFoundError):
			os.unlink(str_tmp)
		raise
