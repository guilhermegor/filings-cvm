"""Shared base for the CVM FI/DOC/ENTREGA (document delivery index) ingestion readers.

`fi_entrega_documento_AAAAMM.zip` is a **two-member ZIP**, **partitioned by month** (series
`202501` onward): the all-documents index and the daily-fund index. Both members share one
11-column header in every month measured, so the two public readers differ only in member name and
contract. The download -> parse -> stamp logic lives here once.

Private base (own `_` file): consumers import the concrete readers, never this class. A month
before the series is refused before downloading.

The two competency dates are coerced to pure `date`; everything else, including the
millisecond `Data_Hora_Entrega` and the `ID_Documento`, stays exact source text. Pass `path_raw`
to keep the raw `.zip` (and the one extracted CSV) for a bronze layer. Only this reader's
member is extracted, so the small index never unpacks the ~178 MB daily CSV beside it.
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
from filings_cvm._internal.utils.zip_extractor import extract_members, find_member


_BASE_URL = "https://dados.cvm.gov.br/dados/FI/DOC/ENTREGA/DADOS/fi_entrega_documento_{ym}.zip"

_DATE_COLS: tuple[str, ...] = ("Data_Inicio_Competencia", "Data_Fim_Competencia")

# First month CVM publishes (measured: 202412 and every earlier probe answer 404).
_SERIES_FIRST_YM = 202501

_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class _BaseEntregaReader(IngestionReader):
	"""Private base for the two FI/DOC/ENTREGA readers.

	A concrete reader sets :attr:`_CONTRACT`, :attr:`_LABEL` and :attr:`_MEMBER_INFIX` (the part of
	the member name between ``fi_entrega_documento`` and ``_AAAAMM.csv``).

	Methods
	-------
	read(int_timeout_s)
		Download, unzip and parse the reference month's delivery index into a DataFrame.
	"""

	_CONTRACT: ClassVar[FileContract]
	_LABEL: ClassVar[str]
	_MEMBER_INFIX: ClassVar[str]

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
			Any day within the reference month. Defaults to today; the current month is published
			while still open.
		path_raw : pathlib.Path, optional
			Directory in which to persist the raw ``fi_entrega_documento_AAAAMM.zip`` and its
			extracted CSV. Created if absent. When ``None`` the artifact is discarded after the
			read.
		retry_policy : RetryPolicy, optional
			Retry/backoff schedule; defaults to this reader's :attr:`_RETRY_POLICY`.
		cls_logger : LogEmitter, optional
			Injected log sink; defaults to a stdlib-backed :class:`LogEmitter`.

		Raises
		------
		ValueError
			If ``date_ref`` predates the series (``202501``).
		"""
		self._date_ref = date_ref if date_ref is not None else date.today()
		int_ym = self._date_ref.year * 100 + self._date_ref.month
		if int_ym < _SERIES_FIRST_YM:
			raise ValueError(
				f"{type(self).__name__}: CVM publishes no file before {_SERIES_FIRST_YM}; "
				f"{int_ym} is outside the series"
			)
		self._path_raw = path_raw
		self._retry_policy = retry_policy if retry_policy is not None else self._RETRY_POLICY
		self._cls_logger = cls_logger if cls_logger is not None else LogEmitter()
		self._str_url = _BASE_URL.format(ym=self._date_ref.strftime("%Y%m"))

	def read(self, int_timeout_s: int = 60) -> pd.DataFrame:
		"""Download, extract and parse the reference month's delivery index.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60.

		Returns
		-------
		pd.DataFrame
			One row per delivery. **No unique key is asserted** (a re-presentation is a new row).
			The two competency columns are pure ``date``; every other column is exact text.

		Raises
		------
		OSError
			If the download fails.
		ContractError
			If the CSV violates this reader's contract.
		ValueError
			If the archive holds no member for this reader.
		"""
		str_ym = self._date_ref.strftime("%Y%m")
		self._cls_logger.log_message(
			f"Downloading Entrega FI ({self._LABEL}) from {self._str_url}", "info"
		)
		dict_dtypes = {
			str_col: "str"
			for str_col in self._CONTRACT.tuple_required
			if str_col not in _DATE_COLS
		}
		with raw_workspace(self._path_raw) as path_dir:
			path_zip = download_file(
				self._str_url,
				path_dir / f"fi_entrega_documento_{str_ym}.zip",
				int_timeout_s,
				retry_policy=self._retry_policy,
			)
			str_content_hash = hash_artifact(path_zip)
			str_member = f"fi_entrega_documento{self._MEMBER_INFIX}_{str_ym}.csv"
			path_csv = find_member(
				extract_members(path_zip, path_dir, [str_member]),
				str_member,
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
			f"Loaded {len(df_)} Entrega FI ({self._LABEL}) rows from {str_ym}", "info"
		)
		return stamp_provenance(df_, self._str_url, self._CONTRACT, str_content_hash)
