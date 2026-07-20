"""Shared base for the CVM ADM_CART/CAD (portfolio-manager registry) ingestion readers.

`cad_adm_cart.zip` ships **five members** — `cad_adm_cart_pf.csv` and `cad_adm_cart_pj.csv` (the
natural- and legal-person managers) plus `cad_adm_cart_diretor.csv`, `cad_adm_cart_resp.csv` and
`cad_adm_cart_socios.csv` (the managers' directors, responsible officers and partners). This is the
first five-member root of this mould; the members differ only in their columns, so the download →
unzip → select-member → read logic lives here once rather than being repeated in each reader.

This is a **private** base (leading underscore, its own file): consumers import the concrete
`AdmCartPfReader` / `AdmCartPjReader` / `AdmCartDiretorReader` / `AdmCartRespReader` /
`AdmCartSociosReader` adapters, never this class. Each concrete reader is a thin subclass that sets
four class attributes — the member filename, its `FileContract`, its date columns, and a log label
— and inherits everything else.

⚠️ Three of the five members carry **no date column at all** (`diretor`, `resp`, `socios`), so they
declare `_DATE_COLS = ()` and every column of theirs is read as exact source text. The shared
``read`` handles that without a branch: the derived dtype map simply covers the whole contract.

Like the other CAD readers this is a **current-state snapshot** (fixed URL, no `AAAAMM` partition),
so the readers take **no `date_ref`**, and CVM overwrites the file in place — persist `path_raw` to
keep a day's snapshot. All five readers download the *same* archive, so a `path_raw` written by one
serves the rest. No grain is asserted.
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


# CVM open-data portfolio-manager-registry snapshot ZIP, shared by all five readers. Fixed URL: CVM
# overwrites this file in place.
_URL = "https://dados.cvm.gov.br/dados/ADM_CART/CAD/DADOS/cad_adm_cart.zip"

_ZIP_FILENAME = "cad_adm_cart.zip"

# Reader-owned default retry/backoff (CVM's open-data portal throttles under load): 5 attempts on
# a capped exponential schedule (~2, 4, 8, 10 s). All readers inherit it via ``_RETRY_POLICY``; a
# per-instance ``retry_policy=`` still overrides.
_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class _BaseAdmCartReader(IngestionReader):
	"""Private base for the five ADM_CART/CAD registry readers.

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

	# Per-reader default retry and backoff schedule. All five readers share one archive, so they
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
			Directory in which to **persist** the raw ``cad_adm_cart.zip`` and every CSV extracted
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
		:class:`FileContract` before applying the declared types. Any ``DT_*`` columns become pure
		``date`` objects; every other column is exact source text — including ``CEP`` and ``TEL``,
		which the CVM META declares ``numeric`` but which are identifiers, not quantities. For the
		three members with no date column the whole contract is read as text.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60.

		Returns
		-------
		pd.DataFrame
			The registry member — one row per manager (or director/officer/partner). **No grain is
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
			f"Downloading ADM_CART/CAD ({self._LABEL}) from {self._str_url}", "info"
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
			f"Loaded {len(df_)} {self._LABEL} rows from ADM_CART/CAD", "info"
		)
		return stamp_provenance(df_, self._str_url, self._CONTRACT, str_content_hash)
