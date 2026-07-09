"""Explicit column typing for DataFrames loaded from a source.

A single place to enforce the project rule *every DataFrame or SQL-to-memory load
must declare its column types* — instead of trusting pandas' inference, which silently
turns a zero-padded code into an int or a mixed column into ``object``. Pass an
``astype`` dict for the plain types plus optional lists for ``date`` / ``datetime``
columns, which need ``to_datetime`` rather than ``astype``.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import pandas as pd


# ``astype("str")`` is **not** missing-value safe on pandas < 3: it stringifies every NA into
# the literal three-character text ``"nan"``, so a blank field silently becomes data. pandas 3
# introduced a real ``str`` dtype that preserves NA, which means the same declaration produces
# different values depending on the interpreter (the lock file carries pandas 2.3 and 3.0, keyed
# by Python marker — CI runs both). ``"string"`` is the nullable text dtype and behaves
# identically on 2 and 3, so a ``"str"`` declaration is normalised to it. Callers keep writing
# the obvious ``"str"``.
_DTYPE_TEXT = "string"

# Runtime type-checking engine — layout-agnostic (utils.typing in MVC, chassis.typing in
# DDD; always injected, just at different paths). mypy reads the single TYPE_CHECKING
# import (no redefinition); at runtime the try/except picks whichever layout shipped.
if TYPE_CHECKING:
	from filings_cvm._internal.utils.typing import type_checker
else:
	try:
		from filings_cvm._internal.utils.typing import type_checker
	except ModuleNotFoundError:  # DDD ships the engine as chassis.typing
		from filings_cvm._internal.utils.typing import type_checker


@type_checker
def apply_dtypes(
	df_input: pd.DataFrame,
	dict_dtypes: dict[str, str] | None = None,
	list_date_cols: Sequence[str] | None = None,
	list_datetime_cols: Sequence[str] | None = None,
) -> pd.DataFrame:
	"""Coerce a DataFrame's columns to declared types, returning a new frame.

	Validation runs first (fail fast): every referenced column must exist, and the
	three column sets must be disjoint. Then, on a copy: the ``astype`` dict is applied,
	``list_datetime_cols`` are parsed to full timestamps, and ``list_date_cols`` to pure
	``date`` objects.

	Parameters
	----------
	df_input : pd.DataFrame
		The source frame (left unmodified — work happens on a copy).
	dict_dtypes : dict of {str: str}, optional
		Column→dtype mapping passed to :meth:`pandas.DataFrame.astype` (e.g. ``"str"``,
		``"int64"``, ``"float64"``). A ``"str"`` declaration is applied as pandas'
		nullable ``"string"`` dtype, so a missing value stays missing instead of becoming
		the literal text ``"nan"`` (which is what a bare ``astype(str)`` yields on
		pandas < 3). Elements of such a column are still ordinary :class:`str`.
	list_date_cols : sequence of str, optional
		Columns coerced to ``datetime.date`` (date only, no time component).
	list_datetime_cols : sequence of str, optional
		Columns coerced to ``datetime64`` timestamps.

	Returns
	-------
	pd.DataFrame
		A new frame with the requested types applied.

	Raises
	------
	KeyError
		If any referenced column is absent from ``df_input``.
	ValueError
		If a column appears in more than one of the three sets, or a date/datetime
		column cannot be parsed (``to_datetime`` uses ``errors="raise"``).
	"""
	dict_dtypes = dict_dtypes or {}
	list_date_cols = list(list_date_cols or [])
	list_datetime_cols = list(list_datetime_cols or [])

	list_referenced = list(dict_dtypes.keys()) + list_date_cols + list_datetime_cols
	set_missing = {str_col for str_col in list_referenced if str_col not in df_input.columns}
	if set_missing:
		raise KeyError(f"Columns not found in DataFrame: {sorted(set_missing)}")

	set_seen: set[str] = set()
	set_overlap: set[str] = set()
	for str_col in list_referenced:
		if str_col in set_seen:
			set_overlap.add(str_col)
		set_seen.add(str_col)
	if set_overlap:
		raise ValueError(f"Columns assigned more than one target type: {sorted(set_overlap)}")

	df_typed = df_input.copy()

	if dict_dtypes:
		dict_resolved = {
			str_col: (_DTYPE_TEXT if str_dtype == "str" else str_dtype)
			for str_col, str_dtype in dict_dtypes.items()
		}
		df_typed = df_typed.astype(dict_resolved)

	for str_col in list_datetime_cols:
		df_typed[str_col] = pd.to_datetime(df_typed[str_col], errors="raise")

	for str_col in list_date_cols:
		df_typed[str_col] = pd.to_datetime(df_typed[str_col], errors="raise").dt.date

	return df_typed
