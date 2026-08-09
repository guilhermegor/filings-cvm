"""Shared bases for the CVM FI/DOC/EXTRATO (fund information extract) ingestion readers.

The dataset publishes **two different artifacts**: `extrato_fi_AAAA.csv`, one file per year holding
**every** filing delivered that year, and `extrato_fi.csv`, a fixed-URL **snapshot** holding the
**latest** filing per fund. They share the same 117 columns but answer different questions, so each
gets its own reader and its own `FileContract` (see the contract module for the measurements).

Two private bases, because the two artifact kinds differ in exactly one thing — whether a reference
period selects the file:

- `_BaseExtratoReader` — download → parse → provenance-stamp. Takes no `date_ref`; the snapshot
  reader uses it directly.
- `_BaseExtratoYearlyReader` — adds the yearly partition and the **regime window**, since the
  yearly series changed schema at 2020 (`CNPJ_FUNDO`, 116 columns, through 2019 →
  `TP_FUNDO_CLASSE` + `CNPJ_FUNDO_CLASSE`, 117, from 2020). ⚠️ That cutover is **measured from the
  published headers**, not inferred from a regulation — Resolução CVM 175 postdates it by years, so
  despite producing the same columns as the Perfil Mensal split it is **not** the same cause. Each
  reader refuses a year outside its own regime and **names its sibling**, rather than downloading
  megabytes to end in a `ContractError` about a missing column.

Only `DT_COMPTC` is coerced to a pure `date` — the META declares exactly one `date` field among the
117. Everything else is exact source text: 74 `numeric` + 4 `decimal` + 4 `int` fields, some with
**12 decimal places**, keep CVM's published scale for a downstream `Decimal`; and `PRAZO` is
`varchar` holding `DD/MM/YYYY` strings that must never be parsed as dates. Pass `path_raw` to keep
the raw `.csv` for a datalake's bronze layer.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import ClassVar

import pandas as pd

from filings_cvm._internal.config.contracts import FileContract
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.http_downloader import download_file
from filings_cvm._internal.utils.provenance import hash_artifact, stamp_provenance
from filings_cvm._internal.utils.raw_workspace import raw_workspace
from filings_cvm._internal.utils.retry import LogEmitter, RetryPolicy
from filings_cvm._internal.utils.tabular_reader import read_table


# The dataset's directory; both artifacts live here. The yearly one takes ``{year}``.
_DIR_URL = "https://dados.cvm.gov.br/dados/FI/DOC/EXTRATO/DADOS/"
_YEARLY_URL = _DIR_URL + "extrato_fi_{year}.csv"
_SNAPSHOT_URL = _DIR_URL + "extrato_fi.csv"

# The sole ISO date column — the META declares exactly one ``date`` field among the 117. It sits in
# the tail both regimes share, so it provably cannot differ between them. ⚠️ ``PRAZO`` looks like a
# date (``01/03/2033``) and is deliberately **not** here: the META types it ``varchar``, and an
# ISO-only coercion would either drop it or misread day/month.
_DATE_COLS: tuple[str, ...] = ("DT_COMPTC",)

# Reader-owned default retry/backoff (CVM's open-data portal throttles under load): 5 attempts on a
# capped exponential schedule (~2, 4, 8, 10 s). A per-instance ``retry_policy=`` still overrides.
_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class _BaseExtratoReader(IngestionReader):
	"""Private base for every FI/DOC/EXTRATO reader — download, parse, stamp.

	A concrete reader sets :attr:`_CONTRACT` and :attr:`_LABEL`, and supplies ``self._str_url`` and
	``self._str_filename`` during construction.

	Methods
	-------
	read(int_timeout_s)
		Download and parse this reader's artifact into a validated DataFrame.
	"""

	_CONTRACT: ClassVar[FileContract]
	_LABEL: ClassVar[str]

	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY

	def __init__(
		self,
		path_raw: Path | None = None,
		retry_policy: RetryPolicy | None = None,
		cls_logger: LogEmitter | None = None,
	) -> None:
		"""Initialise the reader for the fixed-URL snapshot.

		Parameters
		----------
		path_raw : pathlib.Path, optional
			Directory in which to **persist** the raw ``.csv`` for a bronze layer. Created if
			absent. When ``None`` (the default) the artifact goes to a temporary directory
			and is discarded, leaving nothing on disk. CVM overwrites the snapshot in place,
			so a persisted copy is the only record of what it said that day.
		retry_policy : RetryPolicy, optional
			Retry/backoff schedule forwarded to the download seam. When ``None`` (the default) this
			reader's own :attr:`_RETRY_POLICY` class attribute is used.
		cls_logger : LogEmitter, optional
			Injected log sink (``log_message(message, level)``). Defaults to a stdlib-backed
			:class:`LogEmitter`, so no logging import is forced on consumers.
		"""
		self._path_raw = path_raw
		self._retry_policy = retry_policy if retry_policy is not None else self._RETRY_POLICY
		self._cls_logger = cls_logger if cls_logger is not None else LogEmitter()
		self._str_url = _SNAPSHOT_URL
		self._str_filename = "extrato_fi.csv"

	def read(self, int_timeout_s: int = 60) -> pd.DataFrame:
		"""Download and parse this reader's artifact into a typed DataFrame.

		The CSV is fetched to a throwaway directory (or ``path_raw``) and read through the tabular
		seam, which enforces this reader's :class:`FileContract` before the types are applied.
		``DT_COMPTC`` becomes a pure ``date``; every other column is exact source text.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60.

		Returns
		-------
		pd.DataFrame
			The parsed extract. See each concrete reader for its grain.

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ContractError
			If the CSV violates this reader's contract.
		"""
		self._cls_logger.log_message(
			f"Downloading Extrato FI ({self._LABEL}) from {self._str_url}", "info"
		)
		dict_dtypes = {
			str_col: "str"
			for str_col in self._CONTRACT.tuple_required
			if str_col not in _DATE_COLS
		}
		with raw_workspace(self._path_raw) as path_dir:
			path_csv = download_file(
				self._str_url,
				path_dir / self._str_filename,
				int_timeout_s,
				retry_policy=self._retry_policy,
			)
			str_content_hash = hash_artifact(path_csv)
			df_ = read_table(
				path_csv,
				"",
				dict_dtypes,
				self._CONTRACT,
				list_date_cols=_DATE_COLS,
				str_csv_sep=";",
				str_encoding="ISO-8859-1",
				int_csv_quoting=csv.QUOTE_NONE,
			)
		self._cls_logger.log_message(f"Loaded {len(df_)} Extrato FI ({self._LABEL}) rows", "info")
		return stamp_provenance(df_, self._str_url, self._CONTRACT, str_content_hash)


class _BaseExtratoYearlyReader(_BaseExtratoReader):
	"""Private base for the two **yearly** FI/DOC/EXTRATO readers.

	Adds the yearly partition and the regime window on top of :class:`_BaseExtratoReader`.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the reference year's filings into a validated DataFrame (inherited).
	"""

	# Inclusive year window this reader's schema covers. ``None`` is open-ended.
	_FIRST_YEAR: ClassVar[int | None]
	_LAST_YEAR: ClassVar[int | None]
	_SIBLING: ClassVar[str]

	def __init__(
		self,
		date_ref: date | None = None,
		path_raw: Path | None = None,
		retry_policy: RetryPolicy | None = None,
		cls_logger: LogEmitter | None = None,
	) -> None:
		"""Initialise the reader for one reference **year**.

		Parameters
		----------
		date_ref : datetime.date, optional
			Any day within the reference **year** — only its year selects the yearly dump. Defaults
			to today for an open regime, and to the **last year it covers** for a closed one, where
			"today" is not a year this reader can serve. The current year's file is updated as
			filings arrive; pass a past year for a settled one.
		path_raw : pathlib.Path, optional
			Directory in which to **persist** the raw ``extrato_fi_AAAA.csv`` for a bronze layer.
			Created if absent. When ``None`` (the default) it is fetched into a temporary directory
			and discarded.
		retry_policy : RetryPolicy, optional
			Retry/backoff schedule forwarded to the download seam. When ``None`` (the default) this
			reader's own :attr:`_RETRY_POLICY` class attribute is used.
		cls_logger : LogEmitter, optional
			Injected log sink (``log_message(message, level)``). Defaults to a stdlib-backed
			:class:`LogEmitter`.

		Raises
		------
		ValueError
			If ``date_ref``'s year falls outside this reader's regime window. The message names the
			sibling reader that serves that year, which a downstream ``ContractError`` about a
			missing column would not.
		"""
		super().__init__(path_raw=path_raw, retry_policy=retry_policy, cls_logger=cls_logger)
		self._date_ref = date_ref if date_ref is not None else self._default_date_ref()
		int_year = self._date_ref.year
		if (self._FIRST_YEAR is not None and int_year < self._FIRST_YEAR) or (
			self._LAST_YEAR is not None and int_year > self._LAST_YEAR
		):
			raise ValueError(
				f"{type(self).__name__} covers {self._LABEL} years "
				f"{self._FIRST_YEAR or '...'}-{self._LAST_YEAR or '...'}; {int_year} is outside "
				f"it — use {self._SIBLING} for that year"
			)
		self._str_url = _YEARLY_URL.format(year=int_year)
		self._str_filename = f"extrato_fi_{int_year}.csv"

	@classmethod
	def _default_date_ref(cls) -> date:
		"""Return the reference year to use when the caller passes none.

		Today, for a regime CVM is still publishing. For a **closed** regime, today is not a year
		this reader can serve, so the default is the last year it covers — a reader whose only
		no-argument behaviour is to raise is one no generic caller can construct.

		Returns
		-------
		datetime.date
			The first day of the default reference year.
		"""
		if cls._LAST_YEAR is None:
			return date.today()
		return date(cls._LAST_YEAR, 1, 1)
