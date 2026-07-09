"""Workspace seam deciding whether a fetched raw artifact survives the read.

Every ingestion reader downloads a **raw artifact** from the source (a `.zip`, `.csv`,
`.html`, `.xlsx`, `.txt`, …) and parses it. Two callers want two different things from
that artifact once parsing is done:

- An interactive consumer wants a DataFrame and nothing else — the bytes are scratch.
- A **datalake** ingestion routine wants the artifact *kept*, byte-for-byte, as the bronze
  layer's authoritative record.

This seam collapses both into one branch, so no reader reimplements it: pass ``None`` and
the artifact lands in a :class:`tempfile.TemporaryDirectory` that is destroyed on exit;
pass a path and the directory is created (parents included) and left in place, holding the
downloaded artifact and everything extracted from it.

**Why keeping the raw artifact matters.** Upstream sources change their data contract
without notice — a renamed column, a restructured page, a flipped encoding — and the
transform breaks. If the bytes only ever lived in memory, that failure is unreproducible:
the artifact that caused it is gone, and re-fetching may return an already-different
source. Persisted, every contract break becomes a replayable local file, and the failure
log points at a concrete artifact rather than a bare stack trace.

The seam is deliberately *not* a storage abstraction: it yields a plain
:class:`pathlib.Path`. A reader writes files there with the stdlib; whatever syncs that
directory to object storage is the caller's concern, not this library's.

ponytail: local filesystem only. Object storage (S3, or an S3-compatible server such as
rustfs) is reached today by pointing ``path_raw`` at a mounted or synced directory. If a
caller ever needs to hand this an ``s3://`` URL directly, that upgrade lands **here** —
swap the two branches below for an ``fsspec``/``s3fs`` open — and no reader changes, which
is the whole reason the branch lives behind one function instead of inside each reader.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import tempfile

from filings_cvm._internal.utils.typing import type_checker


@contextmanager
@type_checker
def raw_workspace(path_raw: Path | None = None) -> Iterator[Path]:
	"""Yield a directory for a reader's raw artifacts, kept only if ``path_raw`` is given.

	Parameters
	----------
	path_raw : pathlib.Path, optional
		Directory in which to **persist** the downloaded artifact and anything extracted
		from it. Created if absent (parents included). When ``None`` (the default) a
		temporary directory is used instead and removed on exit, so the read leaves no
		trace on disk.

	Yields
	------
	pathlib.Path
		The directory the reader should download and extract into.

	Examples
	--------
	Read in memory, leaving nothing behind::

		with raw_workspace() as path_dir:
			...

	Read and keep the raw artifact for the datalake's bronze layer::

		with raw_workspace(Path("/data/bronze/cvm/cda/202504")) as path_dir:
			...
	"""
	if path_raw is None:
		with tempfile.TemporaryDirectory() as str_tmp:
			yield Path(str_tmp)
		return

	path_raw.mkdir(parents=True, exist_ok=True)
	yield path_raw
