"""Provenance stamping — the columns every ingested frame carries beside its source columns.

Every DataFrame produced by ingestion (a downloaded file or a webscrape) carries a fixed set of
**provenance** columns, appended after its source columns, so a datalake's bronze layer is
self-describing and drift-detectable. The column names are owned by
:attr:`~filings_cvm._internal.utils.tabular_reader.FileContract.PROVENANCE_COLUMNS` (so the
contract describes the full output shape) but are **not** in ``tuple_required`` — that validates
the *source* artifact, which does not contain them. This seam appends them **after** contract
validation, uniformly, so no reader can forget:

- ``url`` — the exact source URL the data was fetched from.
- ``updated_at`` — the **collection** timestamp (when *this* read fetched the data), **tz-aware
  UTC**. Not the source's publication date. It is kept tz-aware (lossless, unambiguous); a sink
  that cannot store a tz-aware timestamp (e.g. a naive-``TIMESTAMP`` SQL column) normalises it at
  the **warehouse load boundary** — never here, and never via a per-reader flag.
- ``source_key`` — the dataset identifier from the contract (``FileContract.str_source_key``).
  Disambiguates rows when several readers share one ``url`` (e.g. the 19 ``cad_fi_hist`` members
  of one ZIP) or when many datasets land in one bronze table.
- ``package_version`` — the version of this package that produced the row. When a parsing bug is
  fixed, the rows a buggy version produced are identifiable and can be re-ingested selectively.
- ``ingestion_run_id`` — a UUID generated once per :func:`stamp_provenance` call, shared by every
  row of that read, grouping one ingestion for lineage/debugging.
- ``content_hash`` — ``sha256`` of the **downloaded artifact bytes** (via :func:`hash_artifact`),
  shared by every row. Lets the datalake detect whether the source artifact changed since the
  last run (idempotency / change-detection) without re-parsing.

This is the parsed-frame half of provenance; the raw-bytes half is ``raw_workspace``
(``path_raw``). :func:`stamp_provenance` itself is a **pure frame transform** — it does no I/O;
the artifact hash is computed by the reader (which holds the file) and passed in.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import TYPE_CHECKING
import uuid

import pandas as pd

from filings_cvm._internal.utils.tabular_reader import FileContract


# Runtime type-checking engine — layout-agnostic (see the sibling utils modules).
if TYPE_CHECKING:
	from filings_cvm._internal.utils.typing import type_checker
else:
	try:
		from filings_cvm._internal.utils.typing import type_checker
	except ModuleNotFoundError:  # DDD ships the engine as chassis.typing
		from filings_cvm._internal.utils.typing import type_checker


# The distribution name whose version stamps ``package_version``. Project-specific: a package
# scaffolded from this template substitutes its own dist name here.
_DIST_NAME = "filings-cvm"


@type_checker
def _package_version() -> str:
	"""Return this package's installed version, or ``"0.0.0"`` in a bare source tree."""
	try:
		return version(_DIST_NAME)
	except PackageNotFoundError:  # pragma: no cover - source tree without an installed dist
		return "0.0.0"


@type_checker
def hash_artifact(path_artifact: Path) -> str:
	"""Return ``"sha256:<hexdigest>"`` of a downloaded artifact's bytes.

	Read in chunks so a large dump (tens of MB) is hashed without loading it whole into memory.

	Parameters
	----------
	path_artifact : pathlib.Path
		The downloaded file (the ZIP for archives, the CSV for single-file dumps).

	Returns
	-------
	str
		The digest, prefixed with the algorithm (``"sha256:"``).
	"""
	cls_hash = hashlib.sha256()
	with path_artifact.open("rb") as file_bytes:
		for bytes_chunk in iter(lambda: file_bytes.read(1 << 20), b""):
			cls_hash.update(bytes_chunk)
	return f"sha256:{cls_hash.hexdigest()}"


@type_checker
def stamp_provenance(
	df_input: pd.DataFrame,
	str_url: str,
	cls_contract: FileContract,
	str_content_hash: str,
) -> pd.DataFrame:
	"""Append the provenance columns, returning a new frame (no I/O).

	The columns are added **last**, in the order declared by
	:attr:`FileContract.PROVENANCE_COLUMNS`. Text columns use the nullable ``string`` dtype
	(consistent with the rest of the library); ``updated_at`` is a single tz-aware UTC timestamp
	broadcast to every row. ``ingestion_run_id`` is generated once here, so all rows of one read
	share it.

	Parameters
	----------
	df_input : pd.DataFrame
		The parsed, contract-validated frame (left unmodified — work happens on a copy).
	str_url : str
		The source URL the data was fetched from.
	cls_contract : FileContract
		The contract of the read; supplies ``source_key`` and owns the provenance column names.
	str_content_hash : str
		``sha256`` of the downloaded artifact, from :func:`hash_artifact`.

	Returns
	-------
	pd.DataFrame
		A new frame with the provenance columns appended.
	"""
	(
		str_col_url,
		str_col_updated,
		str_col_source,
		str_col_version,
		str_col_run,
		str_col_hash,
	) = FileContract.PROVENANCE_COLUMNS
	int_rows = len(df_input)
	df_ = df_input.copy()
	df_[str_col_url] = pd.array([str_url] * int_rows, dtype="string")
	df_[str_col_updated] = pd.Timestamp(datetime.now(timezone.utc))
	df_[str_col_source] = pd.array([cls_contract.str_source_key] * int_rows, dtype="string")
	df_[str_col_version] = pd.array([_package_version()] * int_rows, dtype="string")
	df_[str_col_run] = pd.array([str(uuid.uuid4())] * int_rows, dtype="string")
	df_[str_col_hash] = pd.array([str_content_hash] * int_rows, dtype="string")
	return df_
