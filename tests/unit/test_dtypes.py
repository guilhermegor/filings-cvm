"""Unit tests for the explicit column-typing seam.

The behaviour worth pinning is the one that differs between pandas majors: a ``"str"``
declaration must keep missing values missing, on 2.x and 3.x alike. A bare
``astype(str)`` stringifies NA into the literal text ``"nan"`` on pandas < 3, quietly
fabricating data that then flows into a datalake as if CVM had sent it.
"""

from decimal import Decimal

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


def test_apply_dtypes_decimal_preserves_the_source_value_exactly() -> None:
	"""A decimal column keeps every digit the source published.

	Asserted with ``==`` against a ``Decimal`` built from the same text, never
	``pytest.approx``: approximate equality is precisely the blindness this seam exists to
	remove, so a tolerance-based assertion would pass even on the float path it forbids.
	"""
	df_input = pd.DataFrame({"VL_PATRIM_LIQ": ["1984223115.42"]})

	df_typed = apply_dtypes(df_input, list_decimal_cols=("VL_PATRIM_LIQ",))

	value = df_typed["VL_PATRIM_LIQ"].iloc[0]
	assert isinstance(value, Decimal)
	assert value == Decimal("1984223115.42")
	# The binary-float round trip this seam replaces, shown failing on the same value.
	assert value != Decimal(1984223115.42)
	assert str(value) == "1984223115.42"


def test_apply_dtypes_decimal_preserves_the_sources_own_scale() -> None:
	"""Trailing zeros are the source's declared precision, not noise to normalise away.

	Quantizing is a silver/gold decision; ingestion has no basis for choosing a scale.
	"""
	df_input = pd.DataFrame({"VL": ["1.50", "1.5000", "2"]})

	df_typed = apply_dtypes(df_input, list_decimal_cols=("VL",))

	assert [str(v) for v in df_typed["VL"].tolist()] == ["1.50", "1.5000", "2"]


def test_apply_dtypes_decimal_refuses_a_binary_float_instead_of_converting() -> None:
	"""A float reaching the seam is rejected — converting would launder a lost value.

	``Decimal(1984223115.42)`` succeeds and yields an exact-looking number carrying the
	float's error, which nothing downstream would ever question. Refusing points the fix at
	the parse boundary, where the precision was actually lost.
	"""
	df_input = pd.DataFrame({"VL": [1984223115.42]})

	with pytest.raises(ValueError, match="Refusing to convert float"):
		apply_dtypes(df_input, list_decimal_cols=("VL",))


def test_apply_dtypes_decimal_treats_nan_as_missing_not_as_a_lossy_float() -> None:
	"""NaN is pandas' missing marker; it must stay NA rather than trip the float refusal."""
	df_input = pd.DataFrame({"VL": ["1.50", np.nan, None, ""]})

	df_typed = apply_dtypes(df_input, list_decimal_cols=("VL",))

	assert df_typed["VL"].isna().tolist() == [False, True, True, True]


def test_apply_dtypes_decimal_accepts_int_and_passes_decimal_through() -> None:
	"""The two other lossless inputs a pipeline can deliver are accepted as-is."""
	df_input = pd.DataFrame({"VL": [7, Decimal("3.140")]})

	df_typed = apply_dtypes(df_input, list_decimal_cols=("VL",))

	assert df_typed["VL"].tolist() == [Decimal(7), Decimal("3.140")]
	assert str(df_typed["VL"].iloc[1]) == "3.140"


def test_apply_dtypes_raises_when_a_column_is_both_decimal_and_typed() -> None:
	"""The mutual-exclusion rule covers the fourth set too."""
	df_input = pd.DataFrame({"VL": ["1.50"]})

	with pytest.raises(ValueError, match="more than one target type"):
		apply_dtypes(df_input, {"VL": "str"}, list_decimal_cols=("VL",))
