"""CVM Balancete FIE — ingestion (leitura) reader.

Downloads the CVM open-data **monthly accounting trial balance of the FIE** (*Fundos de
Investimento Especialmente constituídos*) — ``balancete_fie_AAAAMM.zip`` (dataset
``FIE/DOC/BALANCETE``) — and returns its single CSV member as a typed, contract-validated
:class:`pandas.DataFrame`. One row per fund/classe × competency month × account, carrying the
account balance (``VL_SALDO_BALCTE``).

Two shape notes, both reflected below:

- The dump is **partitioned by month** — ``balancete_fie_202606.zip`` — so this reader's
  ``date_ref`` selects the *year and month*. The series starts ``202401`` (post-RCVM 175), hence
  the ``TP_FUNDO_CLASSE`` / ``CNPJ_FUNDO_CLASSE`` naming.
- It is a **single-member ZIP**: the archive is fetched, every member extracted, and the
  ``balancete_fie_AAAAMM.csv`` selected by exact name before parsing.

Only ``DT_COMPTC`` is coerced to a pure ``date``; every other column — the account balance, the
account code — is exact source text (money stays ``str`` and is never parsed to float here, so no
precision is lost before a downstream layer decides its own scale). Pass ``path_raw`` to keep the
raw ``.zip`` (and its extracted CSV) on disk for a datalake's bronze layer.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import ClassVar

import pandas as pd

from filings_cvm._internal.config.contracts.balancete_fie import BALANCETE_FIE
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.http_downloader import download_file
from filings_cvm._internal.utils.provenance import hash_artifact, stamp_provenance
from filings_cvm._internal.utils.raw_workspace import raw_workspace
from filings_cvm._internal.utils.retry import LogEmitter, RetryPolicy
from filings_cvm._internal.utils.tabular_reader import read_table
from filings_cvm._internal.utils.zip_extractor import extract_all, find_member


# CVM open-data **monthly** dump; ``{ym}`` is the reference month formatted ``AAAAMM``. A ZIP.
_BASE_URL = "https://dados.cvm.gov.br/dados/FIE/DOC/BALANCETE/DADOS/balancete_fie_{ym}.zip"

# The sole ISO date column (competency date); coerced to a pure ``date``. Everything else is exact
# source text.
_DATE_COLS: tuple[str, ...] = ("DT_COMPTC",)

# Every non-date column is exact source text. Derived from the contract so a column added there
# cannot be silently left untyped, and the two lists cannot drift.
_DTYPES: dict[str, str] = {
	str_col: "str" for str_col in BALANCETE_FIE.tuple_required if str_col not in _DATE_COLS
}

# Reader-owned default retry/backoff (CVM's open-data portal throttles under load): 5 attempts on a
# capped exponential schedule (~2, 4, 8, 10 s). Per-reader tunable via ``_RETRY_POLICY``; a
# per-instance ``retry_policy=`` still overrides.
_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class BalanceteFieReader(IngestionReader):
	"""Read the CVM Balancete FIE monthly open-data dump into a typed DataFrame.

	Concrete :class:`IngestionReader` for the monthly ``balancete_fie`` ZIP — the post-RCVM 175
	trial balance, one row per fund/classe per competency month per account.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference month's balancete into a validated DataFrame.
	"""

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
			Any day within the reference **month** — only its year and month select the monthly
			dump. Defaults to today. The current month's file may not yet be published; pass a past
			month for complete data (the series starts ``202401``).
		path_raw : pathlib.Path, optional
			Directory in which to **persist** the raw ``balancete_fie_AAAAMM.zip`` and the CSV
			extracted from it, for a datalake's bronze layer. Created if absent. When ``None`` (the
			default) the artifact is fetched into a temporary directory and discarded.
		retry_policy : RetryPolicy, optional
			Retry/backoff schedule forwarded to the download seam. When ``None`` (the default) this
			reader's own :attr:`_RETRY_POLICY` class attribute is used. Pass a :class:`RetryPolicy`
			to override it for this one instance.
		cls_logger : LogEmitter, optional
			Injected log sink (``log_message(message, level)``). Defaults to a stdlib-backed
			:class:`LogEmitter`, so no logging import is forced on consumers.
		"""
		self._date_ref = date_ref or date.today()
		self._path_raw = path_raw
		self._retry_policy = retry_policy if retry_policy is not None else self._RETRY_POLICY
		self._cls_logger = cls_logger if cls_logger is not None else LogEmitter()
		self._str_url = _BASE_URL.format(ym=self._date_ref.strftime("%Y%m"))

	def read(self, int_timeout_s: int = 60) -> pd.DataFrame:
		"""Download, extract, and parse the reference month's balancete into a typed DataFrame.

		The monthly ZIP is fetched to a throwaway directory (or ``path_raw``), every member
		extracted, and ``balancete_fie_AAAAMM.csv`` selected by exact name and read through the
		tabular seam, which enforces the :data:`BALANCETE_FIE` contract (all 6 columns, with a
		coercible ``CNPJ_FUNDO_CLASSE``) before applying the declared types. ``DT_COMPTC`` becomes
		a pure ``date``; every other column is exact source text.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60.

		Returns
		-------
		pd.DataFrame
			One row per fund/classe per competency month per account. **No unique key is asserted**
			by the reader, though the natural grain is fund/classe × date × account.

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ContractError
			If the CSV violates the :data:`BALANCETE_FIE` contract.
		ValueError
			If the archive holds no ``balancete_fie_AAAAMM.csv`` for the reference month.
		"""
		str_ym = self._date_ref.strftime("%Y%m")
		self._cls_logger.log_message(f"Downloading Balancete FIE from {self._str_url}", "info")
		with raw_workspace(self._path_raw) as path_dir:
			path_zip = download_file(
				self._str_url,
				path_dir / f"balancete_fie_{str_ym}.zip",
				int_timeout_s,
				retry_policy=self._retry_policy,
			)
			str_content_hash = hash_artifact(path_zip)
			path_csv = find_member(extract_all(path_zip, path_dir), f"balancete_fie_{str_ym}.csv")
			df_ = read_table(
				path_csv,
				"",
				_DTYPES,
				BALANCETE_FIE,
				list_date_cols=_DATE_COLS,
				str_csv_sep=";",
				str_encoding="ISO-8859-1",
				int_csv_quoting=csv.QUOTE_NONE,
			)
		self._cls_logger.log_message(f"Loaded {len(df_)} Balancete FIE rows from {str_ym}", "info")
		return stamp_provenance(df_, self._str_url, BALANCETE_FIE, str_content_hash)
