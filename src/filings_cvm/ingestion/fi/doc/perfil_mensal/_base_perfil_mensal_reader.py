"""Shared base for the CVM FI/DOC/PERFIL_MENSAL (monthly fund profile) ingestion readers.

`perfil_mensal_fi_AAAAMM.csv` is a **plain CSV, not a ZIP**, **partitioned by month**, carrying one
row per fund/class per competency month: shareholder counts by investor category, VaR and stress
figures, derivative notionals, and the concentration blocks for counterparties (*comitentes*) and
issuers.

⚠️ **One filename pattern, two schemas.** RCVM 175's fund/class split changed the leading key block
mid-series — `CNPJ_FUNDO` (106 columns, through `202311`) became `TP_FUNDO_CLASSE` +
`CNPJ_FUNDO_CLASSE` (107 columns, from `202312`). The other 105 columns are identical, measured. So
the download → parse → stamp logic lives here once, and the two public readers differ only in their
contract and the month window they serve.

This is a **private** base (leading underscore, its own file): consumers import the concrete
`PerfilMensalReader` / `PerfilMensalPre175Reader` adapters, never this class.

Each reader **refuses a month outside its own regime** before downloading, naming its sibling. The
alternative is a 13 MB download that ends in a `ContractError` about a missing column, which does
not tell a caller that the other reader is the one they want.

`DT_COMPTC` and `DT_COTA_TAXA_PERFM` are coerced to pure `date` (both are `date` in the META and
100% ISO where populated; `DT_COTA_TAXA_PERFM` arrives ~84% blank, and blank becomes `NaT`). Every
other column is exact source text — the 53 `numeric` and 17 `int` fields keep CVM's exact decimal
text for a downstream `Decimal` cast, and the five `CENARIO_FPR_*` fields are free text despite
looking numeric. Pass `path_raw` to keep the raw `.csv` on disk for a datalake's bronze layer.
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


# CVM open-data **monthly** dump; ``{ym}`` is the reference month ``AAAAMM``. A plain CSV.
_BASE_URL = "https://dados.cvm.gov.br/dados/FI/DOC/PERFIL_MENSAL/DADOS/perfil_mensal_fi_{ym}.csv"

# The two ISO date columns, coerced to pure ``date``. Declared **once** here rather than per
# subclass because both live in the 105-column tail the two regimes share — the regime split
# touched only the leading key block, so the date columns provably cannot differ between them.
_DATE_COLS: tuple[str, ...] = ("DT_COMPTC", "DT_COTA_TAXA_PERFM")

# First month CVM publishes at all (measured from the directory listing). A month before this has
# no reader, so the window guard must say that rather than point at a sibling that also lacks it.
_SERIES_FIRST_YM = 201901

# Reader-owned default retry/backoff (CVM's open-data portal throttles under load): 5 attempts on a
# capped exponential schedule (~2, 4, 8, 10 s). Both readers inherit it via ``_RETRY_POLICY``; a
# per-instance ``retry_policy=`` still overrides.
_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class _BasePerfilMensalReader(IngestionReader):
	"""Private base for the two FI/DOC/PERFIL_MENSAL readers.

	A concrete reader sets :attr:`_CONTRACT`, :attr:`_LABEL`, :attr:`_SIBLING` and the month
	window (:attr:`_FIRST_YM` / :attr:`_LAST_YM`); everything else — the shared
	download/parse/stamp — lives here.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the reference month's profile into a validated DataFrame.
	"""

	# Set by each concrete subclass. Declared here so the shared code can reference them.
	_CONTRACT: ClassVar[FileContract]
	_LABEL: ClassVar[str]
	_SIBLING: ClassVar[str]

	# Inclusive month window this reader's schema covers, as ``AAAAMM``. ``None`` is open-ended.
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
			Any day within the reference **month** — only its year and month select the monthly
			dump. Defaults to today for the open regime, and to the **last month it covers** for a
			closed one, where "today" is not a month this reader can serve. The current month's
			file may not yet be published; pass a past month for complete data.
		path_raw : pathlib.Path, optional
			Directory in which to **persist** the raw ``perfil_mensal_fi_AAAAMM.csv`` for a bronze
			layer. Created if absent. When ``None`` (the default) the artifact is fetched into a
			temporary directory and discarded, so the read leaves nothing on disk.
		retry_policy : RetryPolicy, optional
			Retry/backoff schedule forwarded to the download seam. When ``None`` (the default) this
			reader's own :attr:`_RETRY_POLICY` class attribute is used. Pass a :class:`RetryPolicy`
			to override it for this one instance.
		cls_logger : LogEmitter, optional
			Injected log sink (``log_message(message, level)``). Defaults to a stdlib-backed
			:class:`LogEmitter`, so no logging import is forced on consumers.

		Raises
		------
		ValueError
			If ``date_ref`` falls outside this reader's regime window. The message names the
			sibling reader that serves that month, which a downstream ``ContractError`` about a
			missing column would not.
		"""
		self._date_ref = date_ref if date_ref is not None else self._default_date_ref()
		int_ym = self._date_ref.year * 100 + self._date_ref.month
		if (self._FIRST_YM is not None and int_ym < self._FIRST_YM) or (
			self._LAST_YM is not None and int_ym > self._LAST_YM
		):
			# A month before the series exists has no reader at all — naming the sibling there
			# would send the caller to one that equally lacks it.
			str_remedy = (
				f"CVM publishes no file before {_SERIES_FIRST_YM}"
				if int_ym < _SERIES_FIRST_YM
				else f"use {self._SIBLING} for that month"
			)
			raise ValueError(
				f"{type(self).__name__} covers {self._LABEL} months "
				f"{self._FIRST_YM or '...'}-{self._LAST_YM or '...'}; {int_ym} is outside it — "
				f"{str_remedy}"
			)
		self._path_raw = path_raw
		self._retry_policy = retry_policy if retry_policy is not None else self._RETRY_POLICY
		self._cls_logger = cls_logger if cls_logger is not None else LogEmitter()
		self._str_url = _BASE_URL.format(ym=self._date_ref.strftime("%Y%m"))

	@classmethod
	def _default_date_ref(cls) -> date:
		"""Return the reference month to use when the caller passes none.

		Today, for a regime CVM is still publishing. For a **closed** regime, today is not a month
		this reader can serve, so the default is the last month it covers — a reader whose only
		no-argument behaviour is to raise is one no generic caller can construct.

		Returns
		-------
		datetime.date
			The first day of the default reference month.
		"""
		if cls._LAST_YM is None:
			return date.today()
		return date(cls._LAST_YM // 100, cls._LAST_YM % 100, 1)

	def read(self, int_timeout_s: int = 60) -> pd.DataFrame:
		"""Download and parse the reference month's fund profile into a typed DataFrame.

		The CSV is fetched to a throwaway directory (or ``path_raw``) and read through the tabular
		seam, which enforces this reader's :class:`FileContract` before applying the declared
		types. ``DT_COMPTC`` and ``DT_COTA_TAXA_PERFM`` become pure ``date`` objects (blank becomes
		``NaT``); every other column is exact source text.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60.

		Returns
		-------
		pd.DataFrame
			One row per fund/class per competency month. **No grain is asserted.**

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ContractError
			If the CSV violates this reader's contract.
		"""
		str_ym = self._date_ref.strftime("%Y%m")
		self._cls_logger.log_message(
			f"Downloading Perfil Mensal FI ({self._LABEL}) from {self._str_url}", "info"
		)
		dict_dtypes = {
			str_col: "str"
			for str_col in self._CONTRACT.tuple_required
			if str_col not in _DATE_COLS
		}
		with raw_workspace(self._path_raw) as path_dir:
			path_csv = download_file(
				self._str_url,
				path_dir / f"perfil_mensal_fi_{str_ym}.csv",
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
		self._cls_logger.log_message(
			f"Loaded {len(df_)} Perfil Mensal FI ({self._LABEL}) rows from {str_ym}", "info"
		)
		return stamp_provenance(df_, self._str_url, self._CONTRACT, str_content_hash)
