"""Tests for the frame-construction seam."""

import pandas as pd
import pytest

from filings_cvm._internal.utils.frames import concat_frames, frame_from_records


def test_frame_from_records_keeps_column_order_and_values() -> None:
	"""Records land under the given columns in order."""
	df_ = frame_from_records([("a", "1"), ("b", "2")], ("K", "V"))
	assert df_.to_dict("list") == {"K": ["a", "b"], "V": ["1", "2"]}


def test_frame_from_records_without_records_keeps_the_columns() -> None:
	"""An empty record list still yields the declared columns."""
	df_ = frame_from_records([], ("K", "V"))
	assert list(df_.columns) == ["K", "V"]


def test_concat_frames_renumbers_the_index() -> None:
	"""Stacked frames get a fresh RangeIndex."""
	df_ = concat_frames([pd.DataFrame({"x": [1]}), pd.DataFrame({"x": [2]})])
	assert list(df_.index) == [0, 1]


def test_concat_frames_rejects_an_empty_list() -> None:
	"""An empty input fails loudly rather than with pandas' opaque error."""
	with pytest.raises(ValueError, match="at least one frame"):
		concat_frames([])
