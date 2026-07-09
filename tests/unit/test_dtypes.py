"""Unit tests for the explicit column-typing seam.

The behaviour worth pinning is the one that differs between pandas majors: a ``"str"``
declaration must keep missing values missing, on 2.x and 3.x alike. A bare
``astype(str)`` stringifies NA into the literal text ``"nan"`` on pandas < 3, quietly
fabricating data that then flows into a datalake as if CVM had sent it.
"""

import numpy as np
import pandas as pd
import pytest

from filings_cvm._internal.utils.dtypes import apply_dtypes


def test_apply_dtypes_keeps_missing_text_values_missing() -> None:
	"""A blank field stays NA under a ``"str"`` declaration — never the string "nan"."""
	df_input = pd.DataFrame({"ID_SUBCLASSE": [np.nan, "ABC", None]})

	df_typed = apply_dtypes(df_input, {"ID_SUBCLASSE": "str"})

	assert df_typed["ID_SUBCLASSE"].isna().tolist() == [True, False, True]
	# Guards the regression where a blank became the literal three-character text.
	assert "nan" not in df_typed["ID_SUBCLASSE"].dropna().tolist()


def test_apply_dtypes_text_elements_are_plain_str() -> None:
	"""Present values of a ``"str"`` column remain ordinary ``str``, not a pandas scalar."""
	df_typed = apply_dtypes(pd.DataFrame({"CNPJ": ["00.000.000/0001-91"]}), {"CNPJ": "str"})

	assert isinstance(df_typed["CNPJ"].iloc[0], str)


def test_apply_dtypes_leaves_non_text_dtypes_untouched() -> None:
	"""A non-``str`` declaration is passed through to ``astype`` verbatim."""
	df_typed = apply_dtypes(pd.DataFrame({"NR": ["1", "2"]}), {"NR": "int64"})

	assert df_typed["NR"].tolist() == [1, 2]


def test_apply_dtypes_does_not_mutate_the_input_frame() -> None:
	"""Typing works on a copy; the caller's frame is left alone."""
	df_input = pd.DataFrame({"NR": ["1"]})

	apply_dtypes(df_input, {"NR": "int64"})

	assert df_input["NR"].iloc[0] == "1"


def test_apply_dtypes_raises_on_unknown_column() -> None:
	"""A declaration naming an absent column fails fast."""
	with pytest.raises(KeyError):
		apply_dtypes(pd.DataFrame({"A": [1]}), {"B": "int64"})


def test_apply_dtypes_raises_when_a_column_has_two_target_types() -> None:
	"""A column declared both as a dtype and a date column is a contradiction."""
	df_input = pd.DataFrame({"DT": ["2025-04-30"]})

	with pytest.raises(ValueError, match="more than one target type"):
		apply_dtypes(df_input, {"DT": "str"}, list_date_cols=("DT",))
