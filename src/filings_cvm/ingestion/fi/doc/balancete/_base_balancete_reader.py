"""Shared base for the CVM FI/DOC/BALANCETE (monthly trial balance) ingestion readers.

`balancete_fi_AAAAMM.zip` is a **single-member ZIP**, **partitioned by month** (series `201501`
onward), carrying one row per fund/class per competency month per account.

⚠️ **One filename pattern, two schemas.** The leading key changed mid-series -- `CNPJ_FUNDO`
(5 columns, through `202310`) became `TP_FUNDO_CLASSE` + `CNPJ_FUNDO_CLASSE` (6 columns, from
`202311`). The cut was measured over the published headers; it is one month before the Perfil
Mensal's, so it is not inherited from that dataset. The download -> parse -> stamp logic lives here
once; the two public readers differ only in contract and month window.

Private base (own `_` file): consumers import the concrete readers, never this class. Each reader
**refuses a month outside its regime** before downloading, naming its sibling -- otherwise the
caller pays a 14 MB download for a `ContractError` about a missing column.

Only `DT_COMPTC` is coerced (to a pure `date`); the account balance and code stay exact source
text. Pass `path_raw` to keep the raw `.zip` (and the extracted CSV) for a bronze layer.
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
from filings_cvm._internal.utils.zip_extractor import extract_all, find_member


_BASE_URL = "https://dados.cvm.gov.br/dados/FI/DOC/BALANCETE/DADOS/balancete_fi_{ym}.zip"

_DATE_COLS: tuple[str, ...] = ("DT_COMPTC",)

# First month CVM publishes (measured from the directory listing).
_SERIES_FIRST_YM = 201501

_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class _BaseBalanceteReader(IngestionReader):
	"""Private base for the two FI/DOC/BALANCETE readers.

	A concrete reader sets :attr:`_CONTRACT`, :attr:`_LABEL`, :attr:`_SIBLING` and the inclusive
	month window (:attr:`_FIRST_YM` / :attr:`_LAST_YM`).

	Methods
	-------
	read(int_timeout_s)
		Download, unzip and parse the reference month's balancete into a validated DataFrame.
	"""

	_CONTRACT: ClassVar[FileContract]
	_LABEL: ClassVar[str]
	_SIBLING: ClassVar[str]
	_FIRST_YM: ClassVar[int | None]
	_LAST_YM: ClassVar[int | None]

	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY

	def __init__(
		self,
		date_ref: date | None = None,
		path_raw: Path | None = None,
		retry_policy: RetryPolicy | None = None,
		cls_logger: LogEmitter | None = None,
	) -> None:
		"""Initialise the reader for one reference **month**.

		Parameters
		----------
		date_ref : datetime.date, optional
			Any day within the reference month. Defaults to today for the open regime and to the
			last month covered for the closed one. The current month may not be published yet.
		path_raw : pathlib.Path, optional
			Directory in which to persist the raw ``balancete_fi_AAAAMM.zip`` and its extracted
			CSV. Created if absent. When ``None`` the artifact is discarded after the read.
		retry_policy : RetryPolicy, optional
			Retry/backoff schedule; defaults to this reader's :attr:`_RETRY_POLICY`.
		cls_logger : LogEmitter, optional
			Injected log sink; defaults to a stdlib-backed :class:`LogEmitter`.

		Raises
		------
		ValueError
			If ``date_ref`` is outside this reader's window. The message names the sibling reader
			when it serves that month, and says so plainly when the month predates the series.
		"""
		self._date_ref = date_ref if date_ref is not None else self._default_date_ref()
		int_ym = self._date_ref.year * 100 + self._date_ref.month
		if (self._FIRST_YM is not None and int_ym < self._FIRST_YM) or (
			self._LAST_YM is not None and int_ym > self._LAST_YM
		):
			str_remedy = (
				f"CVM publishes no file before {_SERIES_FIRST_YM}"
				if int_ym < _SERIES_FIRST_YM
				else f"use {self._SIBLING} for that month"
			)
			raise ValueError(
				f"{type(self).__name__} covers {self._LABEL} months "
				f"{self._FIRST_YM or '...'}-{self._LAST_YM or '...'}; {int_ym} is outside it - "
				f"{str_remedy}"
			)
		self._path_raw = path_raw
		self._retry_policy = retry_policy if retry_policy is not None else self._RETRY_POLICY
		self._cls_logger = cls_logger if cls_logger is not None else LogEmitter()
		self._str_url = _BASE_URL.format(ym=self._date_ref.strftime("%Y%m"))

	@classmethod
	def _default_date_ref(cls) -> date:
		"""Return today for an open regime, or the last covered month for a closed one.

		Returns
		-------
		datetime.date
			The default reference date.
		"""
		if cls._LAST_YM is None:
			return date.today()
		return date(cls._LAST_YM // 100, cls._LAST_YM % 100, 1)

	def read(self, int_timeout_s: int = 60) -> pd.DataFrame:
		"""Download, extract and parse the reference month's balancete.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60.

		Returns
		-------
		pd.DataFrame
			One row per fund/class per competency month per account. **No unique key is
			asserted.** ``DT_COMPTC`` is a pure ``date``; every other column is exact text.

		Raises
		------
		OSError
			If the download fails.
		ContractError
			If the CSV violates this reader's contract.
		ValueError
			If the archive holds no ``balancete_fi_AAAAMM.csv``.
		"""
		str_ym = self._date_ref.strftime("%Y%m")
		self._cls_logger.log_message(
			f"Downloading Balancete FI ({self._LABEL}) from {self._str_url}", "info"
		)
		dict_dtypes = {
			str_col: "str"
			for str_col in self._CONTRACT.tuple_required
			if str_col not in _DATE_COLS
		}
		with raw_workspace(self._path_raw) as path_dir:
			path_zip = download_file(
				self._str_url,
				path_dir / f"balancete_fi_{str_ym}.zip",
				int_timeout_s,
				retry_policy=self._retry_policy,
			)
			str_content_hash = hash_artifact(path_zip)
			path_csv = find_member(extract_all(path_zip, path_dir), f"balancete_fi_{str_ym}.csv")
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
		self._cls_logger.log_message(
			f"Loaded {len(df_)} Balancete FI ({self._LABEL}) rows from {str_ym}", "info"
		)
		return stamp_provenance(df_, self._str_url, self._CONTRACT, str_content_hash)
