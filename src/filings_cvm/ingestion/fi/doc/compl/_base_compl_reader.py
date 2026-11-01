"""Shared base for the CVM FI/DOC/COMPL (fund complementary information) ingestion readers.

``compl_fi_AAAAMM.zip`` is a **4-member ZIP**, **partitioned by month**, and a **closed series**:
CVM published ``201801`` through ``201904`` (16 files) and nothing since. Every member keeps the
same header in all 16 months (measured), so there is one contract per member and no regime cut.

Members are selected by **exact** name: ``compl_fi_AAAAMM.csv`` is a prefix-stem of the other
three (``compl_fi_inf_…``, ``compl_fi_inf_cotst_…``, ``compl_fi_prest_…``).

Private base (own ``_`` file): consumers import the concrete readers, never this class. A month
outside the published window is refused **before** the download, instead of surfacing as a 404.
Only ``DT_COMPTC`` is coerced (to a pure ``date``); every other column is exact source text.
Pass ``path_raw`` to keep the raw ``.zip`` and the extracted CSVs for a bronze layer.
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


_BASE_URL = "https://dados.cvm.gov.br/dados/FI/DOC/COMPL/DADOS/compl_fi_{ym}.zip"

_DATE_COLS: tuple[str, ...] = ("DT_COMPTC",)

# Inclusive window of months CVM published (measured from the CKAN resource list).
_FIRST_YM = 201801
_LAST_YM = 201904

_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class _BaseComplReader(IngestionReader):
	"""Private base for the four FI/DOC/COMPL member readers.

	A concrete reader sets :attr:`_MEMBER_STEM`, :attr:`_CONTRACT` and :attr:`_LABEL`.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip and parse this reader's member into a validated DataFrame.
	"""

	_MEMBER_STEM: ClassVar[str]
	_CONTRACT: ClassVar[FileContract]
	_LABEL: ClassVar[str]

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
			Any day within the reference month (``201801`` to ``201904``). Defaults to the last
			published month, because the series is closed.
		path_raw : pathlib.Path, optional
			Directory in which to persist the raw ``compl_fi_AAAAMM.zip`` and its extracted CSVs.
			Created if absent. When ``None`` the artifact is discarded after the read.
		retry_policy : RetryPolicy, optional
			Retry/backoff schedule; defaults to this reader's :attr:`_RETRY_POLICY`.
		cls_logger : LogEmitter, optional
			Injected log sink; defaults to a stdlib-backed :class:`LogEmitter`.

		Raises
		------
		ValueError
			If ``date_ref`` falls outside ``201801``-``201904``.
		"""
		self._date_ref = (
			date_ref if date_ref is not None else date(_LAST_YM // 100, _LAST_YM % 100, 1)
		)
		int_ym = self._date_ref.year * 100 + self._date_ref.month
		if not _FIRST_YM <= int_ym <= _LAST_YM:
			raise ValueError(
				f"{type(self).__name__}: CVM published FI/DOC/COMPL only for months "
				f"{_FIRST_YM}-{_LAST_YM}; {int_ym} is outside the series"
			)
		self._path_raw = path_raw
		self._retry_policy = retry_policy if retry_policy is not None else self._RETRY_POLICY
		self._cls_logger = cls_logger if cls_logger is not None else LogEmitter()
		self._str_url = _BASE_URL.format(ym=self._date_ref.strftime("%Y%m"))

	def read(self, int_timeout_s: int = 60) -> pd.DataFrame:
		"""Download, extract and parse this reader's member for the reference month.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60.

		Returns
		-------
		pd.DataFrame
			One row per fund per competency month (per provider/means, depending on the member).
			**No unique key is asserted.** ``DT_COMPTC`` is a pure ``date``; every other column
			is exact text, empty cells staying empty.

		Raises
		------
		OSError
			If the download fails.
		ContractError
			If the CSV violates this reader's contract.
		ValueError
			If the archive holds no ``{stem}_AAAAMM.csv`` member.
		"""
		str_ym = self._date_ref.strftime("%Y%m")
		self._cls_logger.log_message(
			f"Downloading Complemento FI ({self._LABEL}) from {self._str_url}", "info"
		)
		dict_dtypes = {
			str_col: "str"
			for str_col in self._CONTRACT.tuple_required
			if str_col not in _DATE_COLS
		}
		with raw_workspace(self._path_raw) as path_dir:
			path_zip = download_file(
				self._str_url,
				path_dir / f"compl_fi_{str_ym}.zip",
				int_timeout_s,
				retry_policy=self._retry_policy,
			)
			str_content_hash = hash_artifact(path_zip)
			path_csv = find_member(
				extract_all(path_zip, path_dir), f"{self._MEMBER_STEM}_{str_ym}.csv"
			)
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
			f"Loaded {len(df_)} Complemento FI ({self._LABEL}) rows from {str_ym}", "info"
		)
		return stamp_provenance(df_, self._str_url, self._CONTRACT, str_content_hash)
