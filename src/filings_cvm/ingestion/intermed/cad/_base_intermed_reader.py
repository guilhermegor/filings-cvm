"""Shared base for the CVM INTERMED/CAD (market-intermediary registry) ingestion readers.

`cad_intermed.zip` ships **two members** — `cad_intermed.csv` (the intermediary registry) and
`cad_intermed_resp.csv` (its responsible-officer table). ⚠️ Unlike the AUDITOR / AGENTE_FIDUC /
AGENTE_AUTON / INVNR siblings of this mould, the two members are **not a `pf`/`pj` split**; they
are two related tables of the same registry, both keyed by the intermediary's `CNPJ`. Either way
they differ only in their columns, so the download → unzip → select-member → read logic lives here
once rather than being repeated in each public reader.

This is a **private** base (leading underscore, its own file): consumers import the concrete
`IntermedReader` / `IntermedRespReader` adapters, never this class. Each concrete reader is a thin
subclass that sets four class attributes — the member filename, its `FileContract`, its date
columns, and a log label — and inherits everything else.

Like the other CAD readers this is a **current-state snapshot** (fixed URL, no `AAAAMM` partition),
so the readers take **no `date_ref`**, and CVM overwrites the file in place — persist `path_raw` to
keep a day's snapshot. Both readers download the *same* archive, so a `path_raw` written by one
serves the other. No grain is asserted.
"""

from __future__ import annotations

import csv
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


# CVM open-data market-intermediary-registry snapshot ZIP, shared by both readers. Fixed URL: CVM
# overwrites this file in place.
_URL = "https://dados.cvm.gov.br/dados/INTERMED/CAD/DADOS/cad_intermed.zip"

_ZIP_FILENAME = "cad_intermed.zip"

# Reader-owned default retry/backoff (CVM's open-data portal throttles under load): 5 attempts on
# a capped exponential schedule (~2, 4, 8, 10 s). Both readers inherit it via ``_RETRY_POLICY``; a
# per-instance ``retry_policy=`` still overrides.
_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class _BaseIntermedReader(IngestionReader):
	"""Private base for the two INTERMED/CAD registry readers.

	A concrete reader sets :attr:`_MEMBER`, :attr:`_CONTRACT`, :attr:`_DATE_COLS` and
	:attr:`_LABEL`; everything else — the shared download/unzip/parse — lives here.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse this reader's registry member into a validated DataFrame.
	"""

	# Set by each concrete subclass. Declared here so the shared ``read`` can reference them.
	_MEMBER: ClassVar[str]
	_CONTRACT: ClassVar[FileContract]
	_DATE_COLS: ClassVar[tuple[str, ...]]
	_LABEL: ClassVar[str]

	# Per-reader default retry and backoff schedule. Both readers share one archive, so they
	# inherit this default; a subclass may still assign its own, and a retry_policy passed to the
	# constructor overrides it for that instance.
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY

	def __init__(
		self,
		path_raw: Path | None = None,
		retry_policy: RetryPolicy | None = None,
		cls_logger: LogEmitter | None = None,
	) -> None:
		"""Initialise the reader.

		Parameters
		----------
		path_raw : pathlib.Path, optional
			Directory in which to **persist** the raw ``cad_intermed.zip`` and every CSV extracted
			from it — not just the member read — for a bronze layer. Created if absent. When
			``None`` (the default) the artifact is fetched into a temporary directory and
			discarded. CVM overwrites the file in place, so a persisted snapshot is the only
			record of what the registry said that day.
		retry_policy : RetryPolicy, optional
			Retry/backoff schedule forwarded to the download seam. When ``None`` (the default) this
			reader's own :attr:`_RETRY_POLICY` class attribute is used. Pass a :class:`RetryPolicy`
			to override it for this one instance.
		cls_logger : LogEmitter, optional
			Injected log sink (``log_message(message, level)``). Defaults to a stdlib-backed
			:class:`LogEmitter`, so no logging import is forced on consumers.
		"""
		self._path_raw = path_raw
		self._retry_policy = retry_policy if retry_policy is not None else self._RETRY_POLICY
		self._cls_logger = cls_logger if cls_logger is not None else LogEmitter()
		self._str_url = _URL

	def read(self, int_timeout_s: int = 60) -> pd.DataFrame:
		"""Download, extract, and parse this reader's registry member into a typed DataFrame.

		The ZIP is fetched to a throwaway directory (or ``path_raw``) and every member extracted;
		this reader's member is read through the tabular seam, which enforces its
		:class:`FileContract` before applying the declared types. The ``DT_*`` columns become pure
		``date`` objects; every other column is exact source text — including ``CEP``, ``TEL``,
		``FAX``, ``DDD_*`` and ``CD_CVM``, which the CVM META declares ``numeric``/``char`` but
		which are identifiers, not quantities.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60.

		Returns
		-------
		pd.DataFrame
			The registry member — one row per registered intermediary (or officer). **No grain is
			asserted.**

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ContractError
			If the CSV violates this reader's contract.
		ValueError
			If the archive holds no member named :attr:`_MEMBER`.
		"""
		self._cls_logger.log_message(
			f"Downloading INTERMED/CAD ({self._LABEL}) from {self._str_url}", "info"
		)
		dict_dtypes = {
			str_col: "str"
			for str_col in self._CONTRACT.tuple_required
			if str_col not in self._DATE_COLS
		}
		with raw_workspace(self._path_raw) as path_dir:
			path_zip = download_file(
				self._str_url,
				path_dir / _ZIP_FILENAME,
				int_timeout_s,
				retry_policy=self._retry_policy,
			)
			str_content_hash = hash_artifact(path_zip)
			path_csv = find_member(extract_all(path_zip, path_dir), self._MEMBER)
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
			f"Loaded {len(df_)} {self._LABEL} rows from INTERMED/CAD", "info"
		)
		return stamp_provenance(df_, self._str_url, self._CONTRACT, str_content_hash)
