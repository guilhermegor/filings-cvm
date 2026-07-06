"""Robust tabular reading (Excel, CSV, JSON, or SQL) with dtype treatment and data contracts.

One reusable seam for turning a worksheet, a CSV, a JSON document, OR a SQL query into a
typed, validated DataFrame. File format is chosen by extension (``.csv`` → CSV with a
configurable delimiter; ``.json`` → a JSON array of records; otherwise Excel). Capabilities:

- :func:`read_table` — reads a **file**, **always** enforces its contract (raising
  :class:`ContractError` on violation), and applies explicit column types via
  :func:`utils.dtypes.apply_dtypes` (never trusting pandas' inference).
- :func:`read_query` — the **SQL** sibling: runs a parameterized query against an
  already-open DB-API connection and shares the same mandatory contract + dtype tail. The
  seam never opens connections (that stays a controller/boundary concern).
- :func:`find_file_problems` — validates a file against a contract and returns problems
  **without raising** (the boundary uses it to abort, skip, or notify).
- :class:`FileContract` — declares the columns a file must have and the columns that must
  hold valid CNPJs (a coercible-type check).

Bare ``pd.read_*`` is banned project-wide (ruff ``TID251``); this seam (and tests) is the one
exempt place, so every read funnels through a contract + dtype check. Projects keep their
concrete contract instances next to their models (or in ``config/contracts/``); the machinery
here stays domain-agnostic.
"""

from __future__ import annotations

from collections.abc import Sequence
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd

from filings-cvm._internal.utils.br_identifiers import is_valid_cnpj, unmask_cnpj
from filings-cvm._internal.utils.dtypes import apply_dtypes


# Runtime type-checking engine — layout-agnostic (utils.typing in MVC, chassis.typing in
# DDD; always injected, just at different paths). mypy reads the single TYPE_CHECKING
# import (no redefinition); at runtime the try/except picks whichever layout shipped.
if TYPE_CHECKING:
	from filings-cvm._internal.utils.typing import TypeChecker, type_checker
else:
	try:
		from filings-cvm._internal.utils.typing import TypeChecker, type_checker
	except ModuleNotFoundError:  # DDD ships the engine as chassis.typing
		from filings-cvm._internal.utils.typing import TypeChecker, type_checker


@dataclass(frozen=True)
class FileContract(metaclass=TypeChecker):
	"""The required shape of one input file.

	Parameters
	----------
	str_name : str
		Human-readable file label (used in logs and notifications).
	str_source_key : str
		Source key used to route notifications (e.g. ``"cadastro"``).
	tuple_required : tuple of str
		Columns that must be present.
	tuple_cnpj_cols : tuple of str
		Columns that must hold at least one valid CNPJ (coercible-type check).
	"""

	str_name: str
	str_source_key: str
	tuple_required: tuple[str, ...]
	tuple_cnpj_cols: tuple[str, ...]


class ContractError(Exception, metaclass=TypeChecker):
	"""Raised when a strictly-read file/query violates its data contract.

	Parameters
	----------
	list_problems : list of str
		The problem messages describing the violations.
	"""

	def __init__(self, list_problems: list[str]) -> None:
		self.list_problems = list_problems
		super().__init__("; ".join(list_problems))


@type_checker
def read_table(
	path_file: Path,
	str_sheet: str,
	dict_dtypes: dict[str, str],
	cls_contract: FileContract,
	list_date_cols: Sequence[str] | None = None,
	str_csv_sep: str = ";",
	list_columns: Sequence[str] | None = None,
	str_encoding: str = "utf-8-sig",
	int_header_row: int = 0,
	int_csv_quoting: int = csv.QUOTE_MINIMAL,
) -> pd.DataFrame:
	"""Read a file (Excel/CSV/JSON) into a typed, contract-validated DataFrame.

	The data contract is **mandatory**: the file is always validated first and
	:class:`ContractError` is raised on any violation, before types are applied. A read that
	legitimately constrains nothing still declares intent by passing an empty contract
	(``FileContract(name, key, (), ())``).

	Parameters
	----------
	path_file : pathlib.Path
		Path to the workbook, CSV, or JSON. The extension selects the reader.
	str_sheet : str
		Worksheet name (used for Excel; ignored for CSV/JSON). ``""`` reads the first sheet.
	dict_dtypes : dict of {str: str}
		Column→dtype mapping enforced via :func:`utils.dtypes.apply_dtypes`.
	cls_contract : FileContract
		The contract the file must satisfy (required).
	list_date_cols : sequence of str, optional
		Columns coerced to ``datetime.date``.
	str_csv_sep : str, optional
		CSV delimiter (default ``";"``); ignored otherwise.
	list_columns : sequence of str, optional
		CSV only: read **headerless** and assign these names in order. Ignored otherwise.
	str_encoding : str, optional
		CSV only: text encoding (default ``"utf-8-sig"`` so a leading BOM never corrupts the
		first cell). Pass ``"ISO-8859-1"`` for Latin-1 exports. Ignored otherwise.
	int_header_row : int, optional
		Excel only: zero-based header-row index (default ``0``). Ignored otherwise.
	int_csv_quoting : int, optional
		CSV only: the :mod:`csv` quoting constant passed to the reader (default
		``csv.QUOTE_MINIMAL``, pandas' own default). Pass ``csv.QUOTE_NONE`` for external
		``;``-delimited regulatory dumps (e.g. CVM open data), where an upstream submitter's
		stray ``"`` is literal text, not a field wrapper — the default engine would swallow the
		delimiter and shift subsequent columns, corrupting the parse. Ignored otherwise.

	Returns
	-------
	pd.DataFrame
		The rows with the declared types applied.

	Raises
	------
	ContractError
		When the file violates ``cls_contract``.
	"""
	df_raw = _read_raw(
		path_file,
		str_sheet,
		None,
		str_csv_sep,
		list_columns,
		str_encoding,
		int_header_row,
		int_csv_quoting,
	)
	return _finalize(df_raw, dict_dtypes, list_date_cols, cls_contract)


@type_checker
def read_query(
	cls_connection: Any,  # noqa: ANN401 — opaque DB-API connection; any driver's object is valid
	str_sql: str,
	dict_dtypes: dict[str, str],
	cls_contract: FileContract,
	list_params: Sequence[Any] | None = None,
	list_date_cols: Sequence[str] | None = None,
) -> pd.DataFrame:
	"""Run a parameterized SQL query into a typed, contract-validated DataFrame.

	The SQL sibling of :func:`read_table`: it shares the same mandatory contract check +
	:func:`utils.dtypes.apply_dtypes` tail so file and DB reads cannot diverge. The connection
	is **passed in already open** (the seam never opens connections — that is a
	controller/boundary concern); queries are parameterized, never string-interpolated.

	Parameters
	----------
	cls_connection : Any
		An open DB-API 2.0 connection (e.g. from ``config.connection_db.build_connection``).
		Opaque by design — any driver's connection object is accepted.
	str_sql : str
		The SQL query, with ``?``/``%s`` placeholders for any parameters.
	dict_dtypes : dict of {str: str}
		Column→dtype mapping enforced via :func:`utils.dtypes.apply_dtypes`.
	cls_contract : FileContract
		The contract the result must satisfy (required).
	list_params : sequence, optional
		Bound query parameters passed to :func:`pandas.read_sql_query`.
	list_date_cols : sequence of str, optional
		Columns coerced to ``datetime.date``.

	Returns
	-------
	pd.DataFrame
		The query rows with the declared types applied.

	Raises
	------
	ContractError
		When the result violates ``cls_contract``.
	"""
	df_raw = pd.read_sql_query(str_sql, cls_connection, params=list_params)
	return _finalize(df_raw, dict_dtypes, list_date_cols, cls_contract)


@type_checker
def find_file_problems(
	cls_contract: FileContract, path_file: Path, str_sheet: str, str_csv_sep: str = ";"
) -> list[str]:
	"""Validate a file against its contract; return problems (never raises).

	Parameters
	----------
	cls_contract : FileContract
		The contract to validate against.
	path_file : pathlib.Path
		The file to read (Excel or CSV).
	str_sheet : str
		Worksheet name (used for Excel; ignored for CSV).
	str_csv_sep : str, optional
		CSV delimiter (default ``";"``); ignored for Excel.

	Returns
	-------
	list of str
		One message per problem found; empty when the file is sound.

	Raises
	------
	FileNotFoundError
		If the file does not exist (raised by the reader).
	"""
	df_raw = _read_raw(path_file, str_sheet, "str", str_csv_sep)
	return find_contract_problems(df_raw, cls_contract)


@type_checker
def find_contract_problems(df_input: pd.DataFrame, cls_contract: FileContract) -> list[str]:
	"""Return the contract problems of an already-read frame (never raises).

	Parameters
	----------
	df_input : pd.DataFrame
		The frame to validate (raw, as read).
	cls_contract : FileContract
		The contract to validate against.

	Returns
	-------
	list of str
		Missing required columns and CNPJ columns holding no valid CNPJ.
	"""
	list_problems: list[str] = []
	for str_col in cls_contract.tuple_required:
		if str_col not in df_input.columns:
			list_problems.append(
				f"Required column missing in '{cls_contract.str_name}': '{str_col}'"
			)
	for str_col in cls_contract.tuple_cnpj_cols:
		if str_col not in df_input.columns:
			continue
		series_valid = df_input[str_col].astype(str).map(lambda v: is_valid_cnpj(unmask_cnpj(v)))
		if not bool(series_valid.any()):
			list_problems.append(
				f"Column '{str_col}' in '{cls_contract.str_name}' holds no valid CNPJ "
				f"(unexpected data type)"
			)
	return list_problems


@type_checker
def resolve_sheet_name(path_file: Path, tuple_known_names: tuple[str, ...]) -> str:
	"""Resolve which worksheet to read from a workbook whose sheet name varies by source.

	A **single-sheet** workbook uses that one sheet (whatever its name); a **multi-sheet**
	workbook uses the first sheet whose name matches one of ``tuple_known_names``
	(case-insensitive). A multi-sheet workbook with **no** known name raises
	:class:`ContractError`, so the caller treats the file as invalid rather than silently
	reading the wrong sheet. Non-Excel files have no sheet concept and return ``""``.

	Parameters
	----------
	path_file : pathlib.Path
		The workbook to inspect.
	tuple_known_names : tuple of str
		Accepted sheet names, in priority order (matched case-insensitively).

	Returns
	-------
	str
		The sheet name to read (``""`` for non-Excel files).

	Raises
	------
	ContractError
		When the workbook has multiple sheets and none matches ``tuple_known_names``.
	"""
	if path_file.suffix.lower() not in {".xlsx", ".xls", ".xlsm"}:
		return ""
	with pd.ExcelFile(path_file) as cls_excel:
		list_sheets = [str(s) for s in cls_excel.sheet_names]
	if len(list_sheets) == 1:
		return list_sheets[0]
	dict_by_lower = {s.casefold(): s for s in list_sheets}
	for str_known in tuple_known_names:
		str_match = dict_by_lower.get(str_known.casefold())
		if str_match is not None:
			return str_match
	raise ContractError(
		[
			f"{path_file.name}: multiple sheets {list_sheets} and none with a known name "
			f"{list(tuple_known_names)}"
		]
	)


@type_checker
def _finalize(
	df_raw: pd.DataFrame,
	dict_dtypes: dict[str, str],
	list_date_cols: Sequence[str] | None,
	cls_contract: FileContract,
) -> pd.DataFrame:
	"""Enforce the contract then apply declared types (shared, mandatory read tail).

	Parameters
	----------
	df_raw : pd.DataFrame
		The frame as read (file or query), before validation or typing.
	dict_dtypes : dict of {str: str}
		Column→dtype mapping enforced via :func:`utils.dtypes.apply_dtypes`.
	list_date_cols : sequence of str | None
		Columns coerced to ``datetime.date``.
	cls_contract : FileContract
		The contract validated before typing.

	Returns
	-------
	pd.DataFrame
		The rows with the declared types applied.

	Raises
	------
	ContractError
		When the frame violates ``cls_contract``.
	"""
	list_problems = find_contract_problems(df_raw, cls_contract)
	if list_problems:
		raise ContractError(list_problems)
	return apply_dtypes(df_raw, dict_dtypes=dict_dtypes, list_date_cols=list_date_cols)


@type_checker
def _read_raw(
	path_file: Path,
	str_sheet: str,
	str_dtype: str | None,
	str_csv_sep: str,
	list_columns: Sequence[str] | None = None,
	str_encoding: str = "utf-8-sig",
	int_header_row: int = 0,
	int_csv_quoting: int = csv.QUOTE_MINIMAL,
) -> pd.DataFrame:
	"""Read a file into a raw DataFrame, dispatching by extension (CSV, JSON, or Excel).

	Parameters
	----------
	path_file : pathlib.Path
		The file to read.
	str_sheet : str
		Worksheet name (Excel only; ignored for CSV and JSON).
	str_dtype : str | None
		Optional dtype applied to every column on read (e.g. ``"str"`` for validation);
		``None`` lets the reader infer (types are applied afterwards).
	str_csv_sep : str
		CSV delimiter (ignored for Excel and JSON).
	list_columns : sequence of str, optional
		CSV only: when given, read headerless and assign these column names.
	str_encoding : str, optional
		CSV text encoding (default ``"utf-8-sig"`` so a leading BOM never corrupts the first
		cell); pass ``"ISO-8859-1"`` for Latin-1 exports.
	int_header_row : int, optional
		Excel header-row index (default ``0``). Ignored for CSV/JSON.
	int_csv_quoting : int, optional
		CSV :mod:`csv` quoting constant (default ``csv.QUOTE_MINIMAL``). ``csv.QUOTE_NONE``
		treats a stray ``"`` as literal text — correct for ``;``-delimited regulatory dumps.

	Returns
	-------
	pd.DataFrame
		The raw rows as read.

	Raises
	------
	FileNotFoundError
		If ``path_file`` does not exist (fail fast at the read boundary).
	"""
	if not path_file.exists():
		raise FileNotFoundError(f"File not found: {path_file}")
	str_suffix = path_file.suffix.lower()
	if str_suffix == ".csv":
		if list_columns is not None:
			return pd.read_csv(
				path_file,
				dtype=str_dtype,
				sep=str_csv_sep,
				header=None,
				names=list(list_columns),
				encoding=str_encoding,
				quoting=int_csv_quoting,
			)
		return pd.read_csv(
			path_file,
			dtype=str_dtype,
			sep=str_csv_sep,
			encoding=str_encoding,
			quoting=int_csv_quoting,
		)
	if str_suffix == ".json":
		df_json = pd.read_json(path_file)
		return df_json.astype(str_dtype) if str_dtype is not None else df_json
	# An empty sheet name means "the first worksheet, whatever it is named" — external files
	# arrive with locale-dependent default sheet names such as Planilha1 or Sheet1, so read the
	# first sheet by position rather than guessing its name.
	sheet_excel: str | int = 0 if str_sheet == "" else str_sheet
	return pd.read_excel(path_file, sheet_name=sheet_excel, dtype=str_dtype, header=int_header_row)
