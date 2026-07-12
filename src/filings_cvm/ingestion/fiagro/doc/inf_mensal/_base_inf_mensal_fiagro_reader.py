"""Shared base for the CVM *Informe Mensal FIAGRO* (INF_MENSAL) ingestion readers.

``inf_mensal_fiagro_AAAAMM.zip`` (dataset ``FIAGRO/DOC/INF_MENSAL``) ships **2 members** — the
FIAGRO monthly report (``inf_mensal_fiagro_AAAAMM.csv``, 133 columns) and its per-subclasse
breakdown (``inf_mensal_fiagro_subclasse_AAAAMM.csv``, 6 columns). Both share the same monthly
artifact and the ``CNPJ_Classe`` key; they differ in which columns — and, unlike the FIDC family,
in **which date columns** — each carries. The informe proper has three (``Data_Referencia``,
``Data_Entrega``, ``Data_Registro``); the subclasse member has only ``Data_Referencia``.

Rather than repeat the download → unzip → select-member → read logic in each public reader, that
logic lives here once. This is a **private** base (leading underscore, its own file): consumers
import the two concrete ``InfMensalFiagro*Reader`` adapters, never this class. Each concrete
reader is a thin subclass that sets four class attributes — the member's stem (``_MEMBER_STEM``),
its :class:`FileContract`, its date columns (``_DATE_COLS``, member-specific here) and a human
``_LABEL`` — and inherits everything else.

The dump is **monthly-partitioned** (``inf_mensal_fiagro_AAAAMM.zip``, series from ``202505``):
the reader takes a ``date_ref`` whose year and month pick the archive and, inside it, the
``…_AAAAMM.csv`` member — selected by **exact** name so the informe stem (``inf_mensal_fiagro``)
never matches the subclasse member (``inf_mensal_fiagro_subclasse``), of which it is a prefix.
Both readers download the *same* monthly archive, so a ``path_raw`` written by either serves the
other. No grain is asserted: the subclasse member is naturally long (one row per subclasse).
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


# CVM open-data monthly dump; ``{ym}`` is the reference month formatted ``AAAAMM``. Shared by both
# readers — the same archive holds both members.
_BASE_URL = "https://dados.cvm.gov.br/dados/FIAGRO/DOC/INF_MENSAL/DADOS/inf_mensal_fiagro_{ym}.zip"

# Reader-owned default retry/backoff for the FIAGRO monthly dump, declared here as one source of
# truth and assigned by each reader as its ``_RETRY_POLICY`` class attribute. CVM's open-data
# portal throttles under load, so the default is patient — 5 attempts on a capped exponential
# schedule (~2, 4, 8, 10 s). It is a **per-reader override point**: a member needing more (or less)
# patience sets a different policy on its own class, and a caller can still override per-instance
# via the ``retry_policy`` constructor argument.
_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class _BaseInfMensalFiagroReader(IngestionReader):
	"""Private base for the two Informe Mensal FIAGRO member readers.

	A concrete reader sets :attr:`_MEMBER_STEM`, :attr:`_CONTRACT`, :attr:`_DATE_COLS` and
	:attr:`_LABEL`; everything else — the shared download/unzip/parse — lives here. Unlike the
	FIDC family, the two members carry **different** date columns, so ``_DATE_COLS`` is set per
	subclass rather than shared on the base.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse this reader's member into a validated DataFrame.
	"""

	# Set by each concrete subclass. Declared here so the shared ``read`` can reference them.
	_MEMBER_STEM: ClassVar[str]
	_CONTRACT: ClassVar[FileContract]
	_LABEL: ClassVar[str]

	# Member-specific here — the informe proper carries three date columns and the subclasse
	# member only one — so each subclass sets its own; the base declares no default.
	_DATE_COLS: ClassVar[tuple[str, ...]]

	# Per-reader default retry and backoff schedule. Each concrete subclass assigns one — the
	# shared default below, or its own tuned value. A retry_policy passed to the constructor still
	# overrides it for that instance. The base keeps it None and declares no default itself.
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = None

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
			be partial — pass a past month for complete data (the series starts ``202505``).
		path_raw : pathlib.Path, optional
			Directory in which to **persist** the raw ``inf_mensal_fiagro_AAAAMM.zip`` and every
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
		"""Download, extract, and parse this reader's member into a typed DataFrame.

		The monthly ZIP is fetched to a throwaway directory (or ``path_raw``) and every member
		extracted; this reader's member — ``{stem}_AAAAMM.csv`` — is selected by exact name and
		read through the tabular seam, which enforces its :class:`FileContract` (every declared
		column plus a coercible ``CNPJ_Classe``) before applying the declared types. This
		member's date columns become pure ``date`` objects; every other column is exact source
		text (``str``) — monetary, quantity, count and percent fields keep full precision for a
		downstream ``Decimal`` cast.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60. The archive is small.

		Returns
		-------
		pd.DataFrame
			The month's rows for this member. **No grain is asserted:** the subclasse member is
			naturally long (one row per subclasse of a class).

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ContractError
			If the CSV violates this reader's contract.
		ValueError
			If the archive holds no member for this reader in the reference month.
		"""
		str_ym = self._date_ref.strftime("%Y%m")
		self._cls_logger.log_message(
			f"Downloading Informe Mensal FIAGRO ({self._LABEL}) from {self._str_url}", "info"
		)
		dict_dtypes = {
			str_col: "str"
			for str_col in self._CONTRACT.tuple_required
			if str_col not in self._DATE_COLS
		}
		with raw_workspace(self._path_raw) as path_dir:
			path_zip = download_file(
				self._str_url,
				path_dir / f"inf_mensal_fiagro_{str_ym}.zip",
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
			f"Loaded {len(df_)} {self._LABEL} rows from Informe Mensal FIAGRO {str_ym}", "info"
		)
		return stamp_provenance(df_, self._str_url, self._CONTRACT, str_content_hash)
