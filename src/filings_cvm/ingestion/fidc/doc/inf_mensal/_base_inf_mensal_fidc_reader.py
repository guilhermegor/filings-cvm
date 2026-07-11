"""Shared base for the CVM *Informe Mensal FIDC* (INF_MENSAL) ingestion readers.

``inf_mensal_fidc_AAAAMM.zip`` (dataset ``FIDC/DOC/INF_MENSAL``) ships **17 members** — the
tables of the FIDC monthly report: Tabelas I–X plus X's sub-tables (X.1, X.1.1, X.2 … X.7).
Every member shares the four-column key prefix (``TP_FUNDO_CLASSE``, ``CNPJ_FUNDO_CLASSE``,
``DENOM_SOCIAL``, ``DT_COMPTC``) then carries its own table-specific columns. The 17 are a
**uniform family** — same monthly artifact, same key, same one date column — differing only in
which table each carries.

Rather than repeat the download → unzip → select-member → read logic in each of the 17 public
readers, that logic lives here once. This is a **private** base (leading underscore, its own
file): consumers import the 17 concrete ``InfMensalFidcTab*Reader`` adapters, never this class.
Each concrete reader is a thin subclass that sets three class attributes — the member's stem
(``_MEMBER_STEM``), its :class:`FileContract`, and a human ``_LABEL`` — and inherits everything
else. The single date column ``DT_COMPTC`` is shared by every member, so it lives here as
:attr:`_DATE_COLS`, not on the subclasses.

Unlike the CAD snapshots, this dump is **monthly-partitioned**: the reader takes a ``date_ref``
whose year and month pick the ``inf_mensal_fidc_AAAAMM.zip`` and, inside it, the
``…_AAAAMM.csv`` member. All 17 readers download the *same* monthly archive, so a ``path_raw``
written by any one serves the others. No grain is asserted: the sub-tables (X.1, X.2, …) are
naturally long — many rows per fund, one per série/subclasse.
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


# CVM open-data monthly dump; ``{ym}`` is the reference month formatted ``AAAAMM``. Shared by all
# 17 readers — the same archive holds every member.
_BASE_URL = "https://dados.cvm.gov.br/dados/FIDC/DOC/INF_MENSAL/DADOS/inf_mensal_fidc_{ym}.zip"

# Reader-owned default retry/backoff for the FIDC monthly dump, declared here as one source of
# truth and assigned by each of the 17 readers as its ``_RETRY_POLICY`` class attribute. CVM's
# open-data portal throttles under load, so the default is patient — 5 attempts on a capped
# exponential schedule (~2, 4, 8, 10 s). It is a **per-reader override point**: a table needing
# more (or less) patience sets a different policy on its own class, and a caller can still override
# per-instance via the ``retry_policy`` constructor argument.
_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class _BaseInfMensalFidcReader(IngestionReader):
	"""Private base for the 17 Informe Mensal FIDC table readers.

	A concrete reader sets :attr:`_MEMBER_STEM`, :attr:`_CONTRACT` and :attr:`_LABEL`;
	everything else — the shared download/unzip/parse and the one ``DT_COMPTC`` date column —
	lives here.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse this reader's table member into a validated DataFrame.
	"""

	# Set by each concrete subclass. Declared here so the shared ``read`` can reference them.
	_MEMBER_STEM: ClassVar[str]
	_CONTRACT: ClassVar[FileContract]
	_LABEL: ClassVar[str]

	# Per-reader default retry and backoff schedule. Every concrete subclass assigns one — the
	# shared default below, or its own tuned value. A retry_policy passed to the constructor still
	# overrides it for that instance. The base keeps it None and declares no default itself.
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = None

	# Every member carries exactly one date column; shared, not per-subclass.
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_COMPTC",)

	def __init__(
		self,
		date_ref: date | None = None,
		path_raw: Path | None = None,
		retry_policy: RetryPolicy | None = None,
		cls_logger: LogEmitter | None = None,
	) -> None:
		"""Initialise the reader for one reference month.

		Parameters
		----------
		date_ref : datetime.date, optional
			Any day within the reference month; only its year and month select the monthly
			dump. Defaults to today. The current month's file may not yet be published or may
			be partial — pass a past month for complete data.
		path_raw : pathlib.Path, optional
			Directory in which to **persist** the raw ``inf_mensal_fidc_AAAAMM.zip`` and every
			CSV extracted from it — not just the member read — for a datalake's bronze layer.
			Created if absent. When ``None`` (the default) the artifact is fetched into a
			temporary directory and discarded.
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
		self._str_url = _BASE_URL.format(ym=self._date_ref.strftime("%Y%m"))

	def read(self, int_timeout_s: int = 60) -> pd.DataFrame:
		"""Download, extract, and parse this reader's table member into a typed DataFrame.

		The monthly ZIP is fetched to a throwaway directory (or ``path_raw``) and every member
		extracted; this reader's member — ``{stem}_AAAAMM.csv`` — is selected by exact name and
		read through the tabular seam, which enforces its :class:`FileContract` (every declared
		column plus a coercible ``CNPJ_FUNDO_CLASSE``) before applying the declared types.
		``DT_COMPTC`` becomes a pure ``date``; every other column is exact source text (``str``)
		— monetary and quantity fields keep full precision for a downstream ``Decimal`` cast.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60. The archive is ~2.5 MB.

		Returns
		-------
		pd.DataFrame
			The month's rows for this table. **No grain is asserted:** the sub-tables carry
			many rows per fund (one per série/subclasse).

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ContractError
			If the CSV violates this reader's contract.
		ValueError
			If the archive holds no member for this table in the reference month.
		"""
		str_ym = self._date_ref.strftime("%Y%m")
		self._cls_logger.log_message(
			f"Downloading Informe Mensal FIDC ({self._LABEL}) from {self._str_url}", "info"
		)
		dict_dtypes = {
			str_col: "str"
			for str_col in self._CONTRACT.tuple_required
			if str_col not in self._DATE_COLS
		}
		with raw_workspace(self._path_raw) as path_dir:
			path_zip = download_file(
				self._str_url,
				path_dir / f"inf_mensal_fidc_{str_ym}.zip",
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
				list_date_cols=self._DATE_COLS,
				str_csv_sep=";",
				str_encoding="ISO-8859-1",
				int_csv_quoting=csv.QUOTE_NONE,
			)
		self._cls_logger.log_message(
			f"Loaded {len(df_)} {self._LABEL} rows from Informe Mensal FIDC {str_ym}", "info"
		)
		return stamp_provenance(df_, self._str_url, self._CONTRACT, str_content_hash)
