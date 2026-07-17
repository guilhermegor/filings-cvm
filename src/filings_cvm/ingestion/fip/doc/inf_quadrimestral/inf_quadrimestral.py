"""CVM Informe Quadrimestral FIP — ingestion (leitura) reader.

Downloads the CVM open-data **four-monthly report of Fundos de Investimento em Participações**
(``inf_quadrimestral_fip_AAAA.csv``, dataset ``FIP/DOC/INF_QUADRIMESTRAL``) and returns it as a
typed, contract-validated :class:`pandas.DataFrame`.

This is the **post-RCVM 175** report (from 2024, replacing the quarterly
:class:`InfTrimestralFipReader`): one row per fund/class per competency period, carrying the same
net-worth, capital and subscriber-breakdown fields as the quarterly report. The only structural
difference is the first two columns — RCVM 175 splits the fund into fund/class, so
``TP_FUNDO_CLASSE`` + ``CNPJ_FUNDO_CLASSE`` replace the single ``CNPJ_FUNDO`` of the pre-175 form.

Two shape notes, both reflected below:

- The dump is **partitioned by year** — ``inf_quadrimestral_fip_2024.csv`` — so this reader's
  ``date_ref`` selects the *year* (only ``date_ref.year`` is read), even though the report is
  filed every four months.
- It is a **plain CSV, not a ZIP** — the downloaded file is read directly.

Only ``DT_COMPTC`` is coerced to a pure ``date``; every other column — including the money and
quota amounts — is exact source text (money/quantity values stay ``str`` and are never parsed to
float here, so no precision is lost before a downstream layer decides its own scale).

Network and CSV parsing are delegated to this library's own ``_internal.utils`` seams
(``http_downloader``, ``tabular_reader``) — never a vendor framework — so the single I/O boundary
is :func:`download_file` and tests mock only there.

Pass ``path_raw`` to keep the downloaded ``.csv`` on disk (a datalake's bronze layer); omit it and
it lives in a temporary directory that is discarded.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import ClassVar

import pandas as pd

from filings_cvm._internal.config.contracts.inf_quadrimestral_fip import INF_QUADRIMESTRAL_FIP
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.http_downloader import download_file
from filings_cvm._internal.utils.provenance import hash_artifact, stamp_provenance
from filings_cvm._internal.utils.raw_workspace import raw_workspace
from filings_cvm._internal.utils.retry import LogEmitter, RetryPolicy
from filings_cvm._internal.utils.tabular_reader import read_table


# CVM open-data **yearly** dump; ``{yyyy}`` is the reference year. A plain CSV, not a ZIP.
_BASE_URL = "https://dados.cvm.gov.br/dados/FIP/DOC/INF_QUADRIMESTRAL/DADOS/inf_quadrimestral_fip_{yyyy}.csv"

# The sole ISO date column (competency date); coerced to a pure ``date``. Everything else is exact
# source text.
_DATE_COLS: tuple[str, ...] = ("DT_COMPTC",)

# Every non-date column is exact source text. Derived from the contract so a column added there
# cannot be silently left untyped, and the two lists cannot drift. ``apply_dtypes`` requires the
# dtype and date sets to be disjoint, which this comprehension guarantees.
_DTYPES: dict[str, str] = {
	str_col: "str" for str_col in INF_QUADRIMESTRAL_FIP.tuple_required if str_col not in _DATE_COLS
}

# Reader-owned default retry/backoff (CVM's open-data portal throttles under load): 5 attempts on
# a capped exponential schedule (~2, 4, 8, 10 s). Per-reader tunable via ``_RETRY_POLICY``; a
# per-instance ``retry_policy=`` still overrides.
_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class InfQuadrimestralFipReader(IngestionReader):
	"""Read the CVM Informe Quadrimestral FIP open-data dump into a typed DataFrame.

	Concrete :class:`IngestionReader` for the yearly ``inf_quadrimestral_fip`` CSV — the post-RCVM
	175 four-monthly FIP report, one row per fund/class per competency period.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the reference year's report into a validated DataFrame.
	"""

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
			day are ignored, because the dump is partitioned by year. Defaults to today. The report
			starts in 2024 (it replaced the quarterly form), so pass 2024 onward for data; the
			current year's file grows as documents are delivered, so it is partial by definition.
		path_raw : pathlib.Path, optional
			Directory in which to **persist** the raw ``inf_quadrimestral_fip_AAAA.csv`` for a
			datalake's bronze layer. Created if absent. When ``None`` (the default) the artifact is
			fetched into a temporary directory and discarded, so the read leaves nothing on disk.
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
		"""Download and parse the reference year's report into a typed DataFrame.

		The CSV is fetched to a throwaway directory (or ``path_raw``) and read through the tabular
		seam, which enforces the :data:`INF_QUADRIMESTRAL_FIP` contract (all 55 columns, with a
		coercible ``CNPJ_FUNDO_CLASSE``) before applying the declared types. ``DT_COMPTC`` becomes
		a pure ``date``; every other column — including the money and quota amounts — is exact
		source text.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60.

		Returns
		-------
		pd.DataFrame
			One row per fund/class per competency period. **No unique key is asserted:** a fund
			reports once per period, and multiple share classes repeat the fund across rows.

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ContractError
			If the CSV violates the :data:`INF_QUADRIMESTRAL_FIP` contract.
		"""
		str_year = self._date_ref.strftime("%Y")
		self._cls_logger.log_message(
			f"Downloading Informe Quadrimestral FIP from {self._str_url}", "info"
		)
		with raw_workspace(self._path_raw) as path_dir:
			path_csv = download_file(
				self._str_url,
				path_dir / f"inf_quadrimestral_fip_{str_year}.csv",
				int_timeout_s,
				retry_policy=self._retry_policy,
			)
			str_content_hash = hash_artifact(path_csv)
			df_ = read_table(
				path_csv,
				"",
				_DTYPES,
				INF_QUADRIMESTRAL_FIP,
				list_date_cols=_DATE_COLS,
				str_csv_sep=";",
				str_encoding="ISO-8859-1",
				int_csv_quoting=csv.QUOTE_NONE,
			)
		self._cls_logger.log_message(
			f"Loaded {len(df_)} Informe Quadrimestral FIP rows from {str_year}", "info"
		)
		return stamp_provenance(df_, self._str_url, INF_QUADRIMESTRAL_FIP, str_content_hash)
