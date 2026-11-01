"""Frame construction seam: the one place the readers build a DataFrame from raw parts.

The layer policy (``.layer-policy.yaml``) lets ``ingestion/`` name ``pandas`` only as a
*type*; building or combining a frame is a call, and every call is a coupling to the vendor.
Readers therefore go through these helpers instead of ``pd.DataFrame`` / ``pd.concat``.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from filings_cvm._internal.utils.typing import type_checker


@type_checker
def frame_from_records(
	list_records: Sequence[Sequence[object]], tuple_columns: Sequence[str]
) -> pd.DataFrame:
	"""Build a frame from row records under an explicit column order.

	Parameters
	----------
	list_records : Sequence[Sequence[object]]
		One sequence of cell values per row.
	tuple_columns : Sequence[str]
		The column names, in the order the cells appear in each record.

	Returns
	-------
	pd.DataFrame
		The frame, with the given columns even when there are no records.
	"""
	return pd.DataFrame(list_records, columns=list(tuple_columns))


@type_checker
def concat_frames(list_frames: Sequence[pd.DataFrame]) -> pd.DataFrame:
	"""Stack frames vertically, renumbering the index and keeping first-seen column order.

	Parameters
	----------
	list_frames : Sequence[pd.DataFrame]
		The frames to stack; must not be empty.

	Returns
	-------
	pd.DataFrame
		A single frame with a fresh ``RangeIndex``.

	Raises
	------
	ValueError
		If ``list_frames`` is empty (pandas' own error for that is opaque).
	"""
	if not list_frames:
		raise ValueError("concat_frames needs at least one frame")
	return pd.concat(list(list_frames), ignore_index=True, sort=False)
