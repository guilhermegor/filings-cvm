"""Shared base for the CVM *Informe Mensal OTS* (INF_MENSAL_OTS) ingestion readers.

``inf_mensal_ots_AAAA.zip`` (dataset ``SECURIT/DOC/INF_MENSAL_OTS``) ships **8 members** — the
sections of the monthly report of the *Operações de Securitização* that are neither CRA nor CRI:
geral, ativo/passivo, classe, direitos creditórios, desembolso, fluxo de caixa, derivativos and
cedente/devedor. Every member shares the four-column key prefix (``CNPJ_Securitizadora``,
``Codigo_Identificacao_Certificado``, ``Data_Referencia``, ``Versao``) then carries its own
section-specific columns. The 8 are a **uniform family** — same artifact, same key — differing only
in which section each carries.

Rather than repeat the download → unzip → select-member → read logic in each of the 8 public
readers, that logic lives here once. This is a **private** base (leading underscore, its own file):
consumers import the 8 concrete ``InfMensalOts*Reader`` adapters, never this class. Each concrete
reader is a thin subclass that sets four class attributes — the member's stem (``_MEMBER_STEM``),
its :class:`FileContract`, its date columns (``_DATE_COLS``) and a human ``_LABEL``.

⚠️ **Yearly-partitioned despite being a monthly report.** The archive is
``inf_mensal_ots_AAAA.zip`` and its members are ``inf_mensal_ots_<section>_AAAA.csv``, so
``date_ref`` selects the **year** (only ``date_ref.year`` is read) — the FII pattern, not the FIDC
one. A year's file holds every month's rows, keyed by ``Data_Referencia``.

**Date columns are per-member, not shared** (hence ``_DATE_COLS`` on each subclass, with no default
here): every member has ``Data_Referencia``, ``geral`` adds three more and ``classe`` one. Notably
``Indice_Subordinacao_Data_Base`` (in ``classe``) is **not** a date despite its name — its real
values are numeric — so it is deliberately absent from that reader's ``_DATE_COLS``.

All 8 readers download the *same* yearly archive, so a ``path_raw`` written by any one serves the
others. No grain is asserted: ``classe`` and ``cedente_devedor`` are naturally long (many rows per
certificate).
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


# CVM open-data **yearly** dump; ``{yyyy}`` is the reference year. Shared by all 8 readers — the
# same archive holds every member.
_BASE_URL = (
	"https://dados.cvm.gov.br/dados/SECURIT/DOC/INF_MENSAL_OTS/DADOS/inf_mensal_ots_{yyyy}.zip"
)

# Reader-owned default retry/backoff for the OTS yearly dump, declared here as one source of truth
# and assigned by each of the 8 readers as its ``_RETRY_POLICY`` class attribute. CVM's open-data
# portal throttles under load, so the default is patient — 5 attempts on a capped exponential
# schedule (~2, 4, 8, 10 s). It is a **per-reader override point**: a section needing more or less
# patience sets a different policy on its own class, and a caller can still override per-instance
# via the ``retry_policy`` constructor argument.
_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class _BaseInfMensalOtsReader(IngestionReader):
	"""Private base for the 8 Informe Mensal OTS section readers.

	A concrete reader sets :attr:`_MEMBER_STEM`, :attr:`_CONTRACT`, :attr:`_DATE_COLS` and
	:attr:`_LABEL`; everything else — the shared download/unzip/parse — lives here.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse this reader's section member into a validated DataFrame.
	"""

	# Set by each concrete subclass. Declared here so the shared ``read`` can reference them.
	_MEMBER_STEM: ClassVar[str]
	_CONTRACT: ClassVar[FileContract]
	_LABEL: ClassVar[str]

	# Member-specific. Every section has the shared reference date, but geral carries three more
	# date columns and classe one, so each subclass sets its own and the base declares no default.
	_DATE_COLS: ClassVar[tuple[str, ...]]

	# Per-reader default retry and backoff schedule. Every concrete subclass assigns one — the
	# shared default above, or its own tuned value. A retry_policy passed to the constructor still
	# overrides it for that instance. The base keeps it None and declares no default itself.
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = None

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
			day are ignored, because the dump is partitioned by year even though the report is
			monthly. Defaults to today. The current year's file grows as informes are delivered, so
			it is partial — pass a past year for a complete one.
		path_raw : pathlib.Path, optional
			Directory in which to **persist** the raw ``inf_mensal_ots_AAAA.zip`` and every CSV
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
		"""Download, extract, and parse this reader's section into a typed DataFrame.

		The yearly ZIP is fetched to a throwaway directory (or ``path_raw``) and every member
		extracted; this reader's member — ``{stem}_AAAA.csv`` — is selected by exact name and read
		through the tabular seam, which enforces its :class:`FileContract` (every declared column
		plus a coercible ``CNPJ_Securitizadora``) before applying the declared types. This member's
		date columns become pure ``date`` objects; every other column is exact source text
		(``str``) — monetary, quantity and percent fields keep full precision for a downstream
		``Decimal`` cast.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60.

		Returns
		-------
		pd.DataFrame
			The year's rows for this section. **No grain is asserted:** ``classe`` and
			``cedente_devedor`` carry many rows per certificate.

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ContractError
			If the CSV violates this reader's contract.
		ValueError
			If the archive holds no member for this section in the reference year.
		"""
		str_year = self._date_ref.strftime("%Y")
		self._cls_logger.log_message(
			f"Downloading Informe Mensal OTS ({self._LABEL}) from {self._str_url}", "info"
		)
		dict_dtypes = {
			str_col: "str"
			for str_col in self._CONTRACT.tuple_required
			if str_col not in self._DATE_COLS
		}
		with raw_workspace(self._path_raw) as path_dir:
			path_zip = download_file(
				self._str_url,
				path_dir / f"inf_mensal_ots_{str_year}.zip",
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
			f"Loaded {len(df_)} {self._LABEL} rows from Informe Mensal OTS {str_year}", "info"
		)
		return stamp_provenance(df_, self._str_url, self._CONTRACT, str_content_hash)
