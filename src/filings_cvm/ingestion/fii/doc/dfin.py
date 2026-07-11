"""CVM DFIN FII — ingestion (leitura) reader.

Downloads the CVM open-data **index of FII financial statements** (``dfin_fii_AAAA.csv``,
dataset ``FII/DOC/DFIN``) and returns it as a typed, contract-validated
:class:`pandas.DataFrame`.

**This is an index, not a statement.** Each row describes one financial statement a fund
delivered in the year — its reference and delivery dates, the auditor's opinion, and a
``Link_Download`` pointing at the actual document on B3's fnet portal. The reader **returns the
link as text and does not follow it**: fetching the linked statement is a downstream concern, and
the reader stays thin (the same principle as every other reader here — parse the artifact CVM
publishes, nothing more).

Two shape notes:

- The dump is **partitioned by year** — ``dfin_fii_2025.csv`` — so this reader's ``date_ref``
  selects the *year* (only ``date_ref.year`` is read).
- Unlike the FII monthly/quarterly/annual dumps, DFIN is a **plain CSV, not a ZIP** — there is no
  member to extract; the downloaded file is read directly, like the CAD/FI snapshot.

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

from filings_cvm._internal.config.contracts.dfin_fii import DFIN_FII
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.http_downloader import download_file
from filings_cvm._internal.utils.provenance import hash_artifact, stamp_provenance
from filings_cvm._internal.utils.raw_workspace import raw_workspace
from filings_cvm._internal.utils.retry import LogEmitter, RetryPolicy
from filings_cvm._internal.utils.tabular_reader import read_table


# CVM open-data **yearly** dump; ``{yyyy}`` is the reference year. A plain CSV, not a ZIP.
_BASE_URL = "https://dados.cvm.gov.br/dados/FII/DOC/DFIN/DADOS/dfin_fii_{yyyy}.csv"

# The two ISO date columns; coerced to pure ``date``. Everything else — including ``Link_Download``
# and ``Versao`` — is exact source text.
_DATE_COLS: tuple[str, ...] = ("Data_Referencia", "Data_Entrega")

# Every non-date column is exact source text. Derived from the contract so a column added there
# cannot be silently left untyped, and the two lists cannot drift. ``apply_dtypes`` requires the
# dtype and date sets to be disjoint, which this comprehension guarantees.
_DTYPES: dict[str, str] = {
	str_col: "str" for str_col in DFIN_FII.tuple_required if str_col not in _DATE_COLS
}

# Reader-owned default retry/backoff (CVM's open-data portal throttles under load): 5 attempts on
# a capped exponential schedule (~2, 4, 8, 10 s). Per-reader tunable via ``_RETRY_POLICY``; a
# per-instance ``retry_policy=`` still overrides.
_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class DfinFiiReader(IngestionReader):
	"""Read the CVM DFIN FII open-data index into a typed DataFrame.

	Concrete :class:`IngestionReader` for the yearly ``dfin_fii`` index CSV — the list of financial
	statements delivered by FII funds, one row per document.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the reference year's index into a validated DataFrame.
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
			day are ignored, because the dump is partitioned by year. Defaults to today. The
			current year's file grows as documents are delivered, so it is partial by definition —
			pass a past year for a complete one.
		path_raw : pathlib.Path, optional
			Directory in which to **persist** the raw ``dfin_fii_AAAA.csv`` for a datalake's bronze
			layer. Created if absent. When ``None`` (the default) the artifact is fetched into a
			temporary directory and discarded, so the read leaves nothing on disk.
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
		"""Download and parse the reference year's index into a typed DataFrame.

		The CSV is fetched to a throwaway directory (or ``path_raw``) and read through the tabular
		seam, which enforces the :data:`DFIN_FII` contract (all eight columns plus a coercible
		``CNPJ_Fundo_Classe``) before applying the declared types. ``Data_Referencia`` and
		``Data_Entrega`` become pure ``date`` objects; every other column — including
		``Link_Download`` — is exact source text.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60.

		Returns
		-------
		pd.DataFrame
			One row per delivered financial statement in the year. **No unique key is asserted:** a
			fund delivers many documents, and a refiled document repeats with a higher ``Versao``.
			``Link_Download`` is returned as text and is **not** followed.

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ContractError
			If the CSV violates the :data:`DFIN_FII` contract.
		"""
		str_year = self._date_ref.strftime("%Y")
		self._cls_logger.log_message(f"Downloading DFIN FII from {self._str_url}", "info")
		with raw_workspace(self._path_raw) as path_dir:
			path_csv = download_file(
				self._str_url,
				path_dir / f"dfin_fii_{str_year}.csv",
				int_timeout_s,
				retry_policy=self._retry_policy,
			)
			str_content_hash = hash_artifact(path_csv)
			df_ = read_table(
				path_csv,
				"",
				_DTYPES,
				DFIN_FII,
				list_date_cols=_DATE_COLS,
				str_csv_sep=";",
				str_encoding="ISO-8859-1",
				int_csv_quoting=csv.QUOTE_NONE,
			)
		self._cls_logger.log_message(f"Loaded {len(df_)} DFIN FII rows from {str_year}", "info")
		return stamp_provenance(df_, self._str_url, DFIN_FII, str_content_hash)
