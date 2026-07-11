"""Shared base for the CVM *Informe Mensal FII* (INF_MENSAL) ingestion readers.

``inf_mensal_fii_AAAA.zip`` (dataset ``FII/DOC/INF_MENSAL``) ships **3 members** — ``geral``
(cadastro e administrador), ``ativo_passivo`` (composição do ativo e do passivo) and
``complemento`` (cotistas, patrimônio e rentabilidade). All three are keyed by
``CNPJ_Fundo_Classe`` + ``Data_Referencia`` + ``Versao``, differing only in which table they carry.

**The dump is partitioned by YEAR, not by month — despite being the *monthly* report.** One
``inf_mensal_fii_2025.zip`` holds the twelve monthly rows of 2025 (``Data_Referencia`` is the
month's first day), and each member's file name embeds the year: ``inf_mensal_fii_geral_2025.csv``.
So this reader's ``date_ref`` selects the **year** — only ``date_ref.year`` is read, the month and
day are ignored. This is the trap the name invites: the FI and FIDC monthly dumps partition by
``AAAAMM``, this one does not. Filter to a single month in the returned frame, on
``Data_Referencia``.

Rather than repeat the download → unzip → select-member → read logic in each of the 3 public
readers, that logic lives here once. This is a **private** base (leading underscore, its own file):
consumers import the 3 concrete ``InfMensalFii*Reader`` adapters, never this class. Each concrete
reader is a thin subclass that sets four class attributes — the member's stem, its
:class:`FileContract`, its date columns, and a human label — and inherits everything else.

All 3 readers download the *same* yearly archive, so a ``path_raw`` written by any one serves the
others. The grain is one row per (fundo, mês, versão): a fund that refiled a month appears more
than once for it, so **no unique key is asserted** — de-duplicate on ``Versao`` downstream if you
need the latest filing.
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


# CVM open-data **yearly** dump; ``{yyyy}`` is the reference year. Shared by all 3 readers — the
# same archive holds every member.
_BASE_URL = "https://dados.cvm.gov.br/dados/FII/DOC/INF_MENSAL/DADOS/inf_mensal_fii_{yyyy}.zip"

# Reader-owned default retry/backoff (CVM's open-data portal throttles under load): 5 attempts on
# a capped exponential schedule (~2, 4, 8, 10 s). Shared by the 3 readers, which inherit it via
# ``_RETRY_POLICY``; a per-instance ``retry_policy=`` still overrides.
_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class _BaseInfMensalFiiReader(IngestionReader):
	"""Private base for the 3 Informe Mensal FII table readers.

	A concrete reader sets :attr:`_MEMBER_STEM`, :attr:`_CONTRACT`, :attr:`_DATE_COLS` and
	:attr:`_LABEL`; everything else — the shared download/unzip/parse — lives here.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse this reader's member for the reference **year**.
	"""

	# Set by each concrete subclass. Declared here so the shared ``read`` can reference them.
	_MEMBER_STEM: ClassVar[str]
	_CONTRACT: ClassVar[FileContract]
	_DATE_COLS: ClassVar[tuple[str, ...]]
	_LABEL: ClassVar[str]

	# Per-reader default retry and backoff schedule, per the project-wide standard. The 3 readers
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
		"""Initialise the reader for one reference **year**.

		Parameters
		----------
		date_ref : datetime.date, optional
			Any day within the reference **year** — only ``date_ref.year`` is read; the month and
			day are ignored, because the dump is partitioned by year even though it is the
			*monthly* report. Defaults to today. The current year's file grows as months are
			published, so it is partial by definition — pass a past year for a complete one.
		path_raw : pathlib.Path, optional
			Directory in which to **persist** the raw ``inf_mensal_fii_AAAA.zip`` and every CSV
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
		downstream ``Decimal`` cast.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60. The archive is ~1.5 MB.

		Returns
		-------
		pd.DataFrame
			The year's rows for this table — **all twelve months**, one row per (fundo, mês,
			versão). **No unique key is asserted:** a refiled month repeats. Filter on
			``Data_Referencia`` for a single month.

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
			f"Downloading Informe Mensal FII ({self._LABEL}) from {self._str_url}", "info"
		)
		dict_dtypes = {
			str_col: "str"
			for str_col in self._CONTRACT.tuple_required
			if str_col not in self._DATE_COLS
		}
		with raw_workspace(self._path_raw) as path_dir:
			path_zip = download_file(
				self._str_url,
				path_dir / f"inf_mensal_fii_{str_year}.zip",
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
			f"Loaded {len(df_)} {self._LABEL} rows from Informe Mensal FII {str_year}", "info"
		)
		return stamp_provenance(df_, self._str_url, self._CONTRACT, str_content_hash)
