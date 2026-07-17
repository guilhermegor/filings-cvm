"""CVM Medidas Mensais FIE — ingestion (leitura) reader.

Downloads the CVM open-data **monthly headline measures of the FIE** (*Fundos de Investimento
Especialmente constituídos*) — ``medidas_mes_fie_AAAAMM.csv`` (dataset ``FIE/MEDIDAS``) — and
returns it as a typed, contract-validated :class:`pandas.DataFrame`. One row per fund × competency
month, carrying net worth (``VL_PATRIM_LIQ``) and the shareholder count (``NR_COTST``).

Two shape notes, both reflected below:

- The dump is **partitioned by month** — ``medidas_mes_fie_202606.csv`` — so this reader's
  ``date_ref`` selects the *year and month*.
- It is a **plain CSV, not a ZIP** — the downloaded file is read directly, like the FIP informes
  and the DFIN index. ``FIE/MEDIDAS`` is a sibling of ``FIE/DOC`` on the portal, so this reader
  lives at the ``fie/`` root rather than under ``fie/doc/``.

Only ``DT_COMPTC`` is coerced to a pure ``date``; every other column — net worth, shareholder
count — is exact source text (money and counts stay ``str`` and are never parsed to float/int here,
so no precision is lost before a downstream layer decides its own scale). Pass ``path_raw`` to keep
the raw ``.csv`` on disk for a datalake's bronze layer.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import ClassVar

import pandas as pd

from filings_cvm._internal.config.contracts.medidas_mes_fie import MEDIDAS_MES_FIE
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.http_downloader import download_file
from filings_cvm._internal.utils.provenance import hash_artifact, stamp_provenance
from filings_cvm._internal.utils.raw_workspace import raw_workspace
from filings_cvm._internal.utils.retry import LogEmitter, RetryPolicy
from filings_cvm._internal.utils.tabular_reader import read_table


# CVM open-data **monthly** dump; ``{ym}`` is the reference month ``AAAAMM``. A plain CSV.
_BASE_URL = "https://dados.cvm.gov.br/dados/FIE/MEDIDAS/DADOS/medidas_mes_fie_{ym}.csv"

# The sole ISO date column (competency date); coerced to a pure ``date``. Everything else is exact
# source text.
_DATE_COLS: tuple[str, ...] = ("DT_COMPTC",)

# Every non-date column is exact source text. Derived from the contract so a column added there
# cannot be silently left untyped, and the two lists cannot drift.
_DTYPES: dict[str, str] = {
	str_col: "str" for str_col in MEDIDAS_MES_FIE.tuple_required if str_col not in _DATE_COLS
}

# Reader-owned default retry/backoff (CVM's open-data portal throttles under load): 5 attempts on a
# capped exponential schedule (~2, 4, 8, 10 s). Per-reader tunable via ``_RETRY_POLICY``; a
# per-instance ``retry_policy=`` still overrides.
_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class MedidasMesFieReader(IngestionReader):
	"""Read the CVM Medidas Mensais FIE open-data dump into a typed DataFrame.

	Concrete :class:`IngestionReader` for the monthly ``medidas_mes_fie`` CSV — one row per fund
	per competency month, carrying net worth and the shareholder count.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the reference month's measures into a validated DataFrame.
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
			month for complete data.
		path_raw : pathlib.Path, optional
			Directory in which to **persist** the raw ``medidas_mes_fie_AAAAMM.csv`` for a bronze
			layer. Created if absent. When ``None`` (the default) the artifact is fetched into a
			temporary directory and discarded, so the read leaves nothing on disk.
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
		"""Download and parse the reference month's measures into a typed DataFrame.

		The CSV is fetched to a throwaway directory (or ``path_raw``) and read through the tabular
		seam, which enforces the :data:`MEDIDAS_MES_FIE` contract (all 6 columns, with a coercible
		``CNPJ_FUNDO``) before applying the declared types. ``DT_COMPTC`` becomes a pure ``date``;
		every other column — net worth, shareholder count — is exact source text.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60.

		Returns
		-------
		pd.DataFrame
			One row per fund per competency month.

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ContractError
			If the CSV violates the :data:`MEDIDAS_MES_FIE` contract.
		"""
		str_ym = self._date_ref.strftime("%Y%m")
		self._cls_logger.log_message(
			f"Downloading Medidas Mensais FIE from {self._str_url}", "info"
		)
		with raw_workspace(self._path_raw) as path_dir:
			path_csv = download_file(
				self._str_url,
				path_dir / f"medidas_mes_fie_{str_ym}.csv",
				int_timeout_s,
				retry_policy=self._retry_policy,
			)
			str_content_hash = hash_artifact(path_csv)
			df_ = read_table(
				path_csv,
				"",
				_DTYPES,
				MEDIDAS_MES_FIE,
				list_date_cols=_DATE_COLS,
				str_csv_sep=";",
				str_encoding="ISO-8859-1",
				int_csv_quoting=csv.QUOTE_NONE,
			)
		self._cls_logger.log_message(
			f"Loaded {len(df_)} Medidas Mensais FIE rows from {str_ym}", "info"
		)
		return stamp_provenance(df_, self._str_url, MEDIDAS_MES_FIE, str_content_hash)
