"""Explicit column typing for DataFrames loaded from a source.

A single place to enforce the project rule *every DataFrame or SQL-to-memory load
must declare its column types* — instead of trusting pandas' inference, which silently
turns a zero-padded code into an int or a mixed column into ``object``. Pass an
``astype`` dict for the plain types plus optional lists for ``date`` / ``datetime``
columns, which need ``to_datetime`` rather than ``astype``, and ``decimal`` columns, which
need exact :class:`~decimal.Decimal` conversion.

A number whose fractional part carries meaning is **never** a binary float here: use
``list_decimal_cols``. ``bin/check_dtypes.py`` enforces that structurally across ``src/``.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
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
def _to_decimal(value: object) -> object:
	"""Convert one source value to an exact :class:`~decimal.Decimal`.

	Accepts the two forms a lossless pipeline can deliver — text (``"1984223115.42"``, the
	usual shape from a text-first CSV read or from JSON parsed with ``parse_float=Decimal``)
	and ``int`` — plus ``Decimal`` itself, which passes through untouched. Missing values
	stay missing.

	A binary ``float`` is **rejected rather than converted**. By the time a float exists the
	source's exact value is already gone, so converting it would launder a lossy value into a
	type that advertises exactness — the silent failure this seam exists to prevent. The fix
	belongs upstream at the parse boundary (``json.loads(..., parse_float=Decimal)``, or
	reading the column as text), never here.

	Parameters
	----------
	value : object
		One cell from a decimal-typed column.

	Returns
	-------
	object
		A :class:`decimal.Decimal`, or :data:`pandas.NA` for a missing value.

	Raises
	------
	ValueError
		If ``value`` is a binary ``float`` — precision was already lost upstream.
	"""
	if value is None or value is pd.NA:
		return pd.NA
	if isinstance(value, Decimal):
		return value
	# NaN is a float, but it means "missing", not "a value we lost precision on" — pandas uses
	# it as the missing marker in any numeric column. Test it before the float rejection below,
	# or every blank cell in such a column would raise instead of staying NA.
	if isinstance(value, float) and value != value:
		return pd.NA
	if isinstance(value, float):
		raise ValueError(
			f"Refusing to convert float {value!r} to Decimal: the source's exact value is "
			"already lost. Parse the source losslessly instead — "
			"json.loads(..., parse_float=Decimal), or read the column as text."
		)
	if isinstance(value, int):
		return Decimal(value)
	str_value = str(value).strip()
	if not str_value or str_value.lower() in {"nan", "none", "<na>"}:
		return pd.NA
	return Decimal(str_value)


@type_checker
def apply_dtypes(
	df_input: pd.DataFrame,
	dict_dtypes: dict[str, str] | None = None,
	list_date_cols: Sequence[str] | None = None,
	list_datetime_cols: Sequence[str] | None = None,
	list_decimal_cols: Sequence[str] | None = None,
) -> pd.DataFrame:
	"""Coerce a DataFrame's columns to declared types, returning a new frame.

	Validation runs first (fail fast): every referenced column must exist, and the
	four column sets must be disjoint. Then, on a copy: the ``astype`` dict is applied,
	``list_datetime_cols`` are parsed to full timestamps, ``list_date_cols`` to pure
	``date`` objects, and ``list_decimal_cols`` to exact :class:`decimal.Decimal` values.

	Parameters
	----------
	df_input : pd.DataFrame
		The source frame (left unmodified — work happens on a copy).
	dict_dtypes : dict of {str: str}, optional
		Column→dtype mapping passed to :meth:`pandas.DataFrame.astype` (e.g. ``"str"``,
		``"int64"``). A ``"str"`` declaration is applied as pandas'
		nullable ``"string"`` dtype, so a missing value stays missing instead of becoming
		the literal text ``"nan"`` (which is what a bare ``astype(str)`` yields on
		pandas < 3). Elements of such a column are still ordinary :class:`str`.
		**Never declare a binary float dtype for an ingested source column** — use
		``list_decimal_cols`` (see below); ``bin/check_dtypes.py`` enforces this.
	list_date_cols : sequence of str, optional
		Columns coerced to ``datetime.date`` (date only, no time component).
	list_datetime_cols : sequence of str, optional
		Columns coerced to ``datetime64`` timestamps.
	list_decimal_cols : sequence of str, optional
		Columns coerced to exact :class:`decimal.Decimal` values (``object`` dtype), for any
		number whose fractional part carries meaning — money, volumes, rates, quantities.
		A binary float cannot represent most decimal fractions: ``1984223115.42`` is stored
		as ``1984223115.4200000762939453125``, and that loss is **irreversible and silent**,
		surfacing later as a reconciliation that misses by a hair. The source's own scale is
		preserved exactly (``"1.50"`` stays 2dp, ``"1.5000"`` stays 4dp); no precision is
		*chosen* here, because choosing one is a downstream (warehouse) decision this layer
		cannot make.

	Returns
	-------
	pd.DataFrame
		A new frame with the requested types applied.

	Raises
	------
	KeyError
		If any referenced column is absent from ``df_input``.
	ValueError
		If a column appears in more than one of the four sets, a date/datetime
		column cannot be parsed (``to_datetime`` uses ``errors="raise"``), or a decimal
		column already holds a binary ``float`` (see :func:`_to_decimal`).
	"""
	dict_dtypes = dict_dtypes or {}
	list_date_cols = list(list_date_cols or [])
	list_datetime_cols = list(list_datetime_cols or [])
	list_decimal_cols = list(list_decimal_cols or [])

	list_referenced = (
		list(dict_dtypes.keys()) + list_date_cols + list_datetime_cols + list_decimal_cols
	)
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

	for str_col in list_decimal_cols:
		df_typed[str_col] = df_typed[str_col].map(_to_decimal)

	return df_typed
