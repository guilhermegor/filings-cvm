"""Shared base for the CVM *Informe Anual FII* (INF_ANUAL) ingestion readers.

``inf_anual_fii_AAAA.zip`` (dataset ``FII/DOC/INF_ANUAL``) ships **12 members** — the tables of the
FII annual report: cadastro (``geral``, ``complemento``), the assets acquired/transacted and their
book value, the shareholder distribution, the responsible director and service providers (with
their professional experience), the fund's lawsuits, and the shareholders' representative. Every
member is keyed by ``CNPJ_Fundo_Classe`` + ``Data_Referencia`` + ``Versao``, differing only in
which table it carries.

**Partitioned by year** — and here that is *natural*: this is the annual report, so one archive per
year is exactly what it says. (Contrast the FII monthly and quarterly dumps, which are *also*
yearly archives — there the yearly partition is the trap.) ``date_ref`` selects the year; only
``date_ref.year`` is read.

Rather than repeat the download → unzip → select-member → read logic in each of the 12 public
readers, that logic lives here once. This is a **private** base (leading underscore, its own file):
consumers import the 12 concrete ``InfAnualFii*Reader`` adapters, never this class. Each concrete
reader is a thin subclass that sets four class attributes — the member's stem, its
:class:`FileContract`, its date columns, and a human label — and inherits everything else.

All 12 readers download the *same* yearly archive, so a ``path_raw`` written by any one serves the
others. Most members are **long** (one row per ativo / transação / processo / prestador / diretor),
so **no unique key is asserted**.
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


# CVM open-data **yearly** dump; ``{yyyy}`` is the reference year. Shared by all 12 readers.
_BASE_URL = "https://dados.cvm.gov.br/dados/FII/DOC/INF_ANUAL/DADOS/inf_anual_fii_{yyyy}.zip"

# Reader-owned default retry/backoff (CVM's open-data portal throttles under load): 5 attempts on
# a capped exponential schedule (~2, 4, 8, 10 s). Shared by the 12 readers, which inherit it via
# ``_RETRY_POLICY``; a per-instance ``retry_policy=`` still overrides.
_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class _BaseInfAnualFiiReader(IngestionReader):
	"""Private base for the 12 Informe Anual FII table readers.

	A concrete reader sets :attr:`_MEMBER_STEM`, :attr:`_CONTRACT`, :attr:`_DATE_COLS` and
	:attr:`_LABEL`; everything else — the shared download/unzip/parse — lives here.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse this reader's member for the reference year.
	"""

	# Set by each concrete subclass. Declared here so the shared ``read`` can reference them.
	_MEMBER_STEM: ClassVar[str]
	_CONTRACT: ClassVar[FileContract]
	_DATE_COLS: ClassVar[tuple[str, ...]]
	_LABEL: ClassVar[str]

	# Per-reader default retry and backoff schedule, per the project-wide standard. The 12 readers
	# share one archive, so all of them inherit the default declared above. A policy passed to the
	# constructor still wins for that instance.
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY

	def __init__(
		self,
		date_ref: date | None = None,
		path_raw: Path | None = None,
		retry_policy: RetryPolicy | None = None,
		cls_logger: LogEmitter | None = None,
	) -> None:
		"""Initialise the reader for one reference year.

		Parameters
		----------
		date_ref : datetime.date, optional
			Any day within the reference year — only ``date_ref.year`` is read; the month and day
			are ignored. Defaults to today. The current year's report may not be filed yet — pass
			a past year for complete data.
		path_raw : pathlib.Path, optional
			Directory in which to **persist** the raw ``inf_anual_fii_AAAA.zip`` and every CSV
			extracted from it — not just the member read — for a datalake's bronze layer. Created
			if absent. When ``None`` (the default) the artifact is fetched into a temporary
			directory and discarded.
		retry_policy : RetryPolicy, optional
			Retry/backoff schedule forwarded to the download seam. When ``None`` (the default)
			this reader's own :attr:`_RETRY_POLICY` class attribute is used. Pass a
			:class:`RetryPolicy` to override it for this one instance.
		cls_logger : LogEmitter, optional
			Injected log sink (``log_message(message, level)``). Defaults to a stdlib-backed
			:class:`LogEmitter`, so no logging import is forced on consumers.
		"""
		self._date_ref = date_ref or date.today()
		self._path_raw = path_raw
		self._retry_policy = retry_policy if retry_policy is not None else self._RETRY_POLICY
		self._cls_logger = cls_logger if cls_logger is not None else LogEmitter()
		self._str_url = _BASE_URL.format(yyyy=self._date_ref.strftime("%Y"))

	def read(self, int_timeout_s: int = 60) -> pd.DataFrame:
		"""Download, extract, and parse this reader's member for the reference year.

		The yearly ZIP is fetched to a throwaway directory (or ``path_raw``) and every member
		extracted; this reader's member — ``{stem}_AAAA.csv`` — is selected by exact name and read
		through the tabular seam, which enforces its :class:`FileContract` (every declared column
		plus a coercible ``CNPJ_Fundo_Classe``) before applying the declared types. Every declared
		date column becomes a pure ``date`` (blanks become ``NaT``); every other column is exact
		source text (``str``) — money, quantity and percentage fields keep full precision for a
		downstream ``Decimal`` cast, and any ``Link_*`` column is returned as text, never followed.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60. The archive is ~3 MB.

		Returns
		-------
		pd.DataFrame
			The year's rows for this table. **No unique key is asserted:** most members are long
			(one row per ativo / transação / processo / prestador / diretor).

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ContractError
			If the CSV violates this reader's contract.
		ValueError
			If the archive holds no member for this table in the reference year.
		"""
		str_year = self._date_ref.strftime("%Y")
		self._cls_logger.log_message(
			f"Downloading Informe Anual FII ({self._LABEL}) from {self._str_url}", "info"
		)
		dict_dtypes = {
			str_col: "str"
			for str_col in self._CONTRACT.tuple_required
			if str_col not in self._DATE_COLS
		}
		with raw_workspace(self._path_raw) as path_dir:
			path_zip = download_file(
				self._str_url,
				path_dir / f"inf_anual_fii_{str_year}.zip",
				int_timeout_s,
				retry_policy=self._retry_policy,
			)
			str_content_hash = hash_artifact(path_zip)
			path_csv = find_member(
				extract_all(path_zip, path_dir), f"{self._MEMBER_STEM}_{str_year}.csv"
			)
			df_ = read_table(
				path_csv,
				"",
				dict_dtypes,
				self._CONTRACT,
				list_date_cols=self._DATE_COLS,
				str_csv_sep=";",
				str_encoding="ISO-8859-1",
				int_csv_quoting=csv.QUOTE_NONE,
			)
		self._cls_logger.log_message(
			f"Loaded {len(df_)} {self._LABEL} rows from Informe Anual FII {str_year}", "info"
		)
		return stamp_provenance(df_, self._str_url, self._CONTRACT, str_content_hash)
