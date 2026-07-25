"""Shared base for the CVM CIA_ABERTA/DOC/VLMO (securities held and traded) ingestion readers.

`vlmo_cia_aberta_AAAA.zip` ships **two members**, and ⚠️ unlike the registry+satellite mould of
INTERMED / COORD_OFERTA they are an **index and its content**:

- `vlmo_cia_aberta_AAAA.csv` (12 cols) — one row per **document** filed, the IPE shape plus
  `Motivo_Reapresentacao`, carrying a `Link_Download`.
- `vlmo_cia_aberta_con_AAAA.csv` (17 cols) — one row per **movement** of securities held by the
  company, its controller or its controlled entities.

Either way they differ only in their columns, so the download → unzip → select-member → read logic
lives here once rather than being repeated in each public reader.

This is a **private** base (leading underscore, its own file): consumers import the concrete
`VlmoCiaAbertaReader` / `VlmoCiaAbertaConReader` adapters, never this class. Each concrete
reader is a thin subclass that sets four class attributes — the member stem, its
`FileContract`, its date columns, and a log label — and inherits everything else.

The dump is **partitioned by year**, so `date_ref` selects the *year* (only `date_ref.year` is
read) and the member filename carries it. Both readers download the *same* archive, so a
`path_raw` written by one serves the other.

⚠️ **Money and quantity stay exact text.** `Preco_Unitario` and `Volume` arrive with **10 decimal
places** (`61961072.9999543100`) and `Quantidade` is a plain integer; the META declares them
`decimal`/`decimal`/`bigint`. Every non-date column is typed `str`, so those digits are returned
**as published** — a binary float would destroy them irreversibly and silently, and the trailing
`…99995` is upstream float residue that is not ours to re-round. Enforced by `bin/check_dtypes.py`;
a consumer that wants arithmetic converts to `Decimal` downstream.
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


# CVM open-data **yearly** dump; ``{yyyy}`` is the reference year. Shared by both readers.
_BASE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/VLMO/DADOS/vlmo_cia_aberta_{yyyy}.zip"

# Reader-owned default retry/backoff (CVM's open-data portal throttles under load): 5 attempts on a
# capped exponential schedule (~2, 4, 8, 10 s). Both readers inherit it via ``_RETRY_POLICY``; a
# per-instance ``retry_policy=`` still overrides.
_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class _BaseVlmoReader(IngestionReader):
	"""Private base for the two CIA_ABERTA/DOC/VLMO readers.

	A concrete reader sets :attr:`_MEMBER_STEM`, :attr:`_CONTRACT`, :attr:`_DATE_COLS` and
	:attr:`_LABEL`; everything else — the shared download/unzip/parse — lives here.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse this reader's member into a validated DataFrame.
	"""

	# Set by each concrete subclass. Declared here so the shared ``read`` can reference them.
	_MEMBER_STEM: ClassVar[str]
	_CONTRACT: ClassVar[FileContract]
	_DATE_COLS: ClassVar[tuple[str, ...]]
	_LABEL: ClassVar[str]

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
			Any day within the reference **year** — only ``date_ref.year`` is read; the member
			filename carries it. Defaults to today. The current year's file is published
			incrementally, so pass a past year for a complete series.
		path_raw : pathlib.Path, optional
			Directory in which to **persist** the raw ``vlmo_cia_aberta_AAAA.zip`` and the CSVs
			extracted from it, for a datalake's bronze layer. Created if absent. When ``None`` (the
			default) the artifact is fetched into a temporary directory and discarded. Both readers
			download the same archive, so a directory written by one serves the other.
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
		self._str_url = _BASE_URL.format(yyyy=self._date_ref.strftime("%Y"))

	def read(self, int_timeout_s: int = 60) -> pd.DataFrame:
		"""Download, extract, and parse this reader's member into a typed DataFrame.

		The yearly ZIP is fetched to a throwaway directory (or ``path_raw``), every member
		extracted, and ``<stem>_AAAA.csv`` selected by exact name and read through the tabular
		seam, which enforces this reader's contract before applying the declared types. The date
		columns become pure ``date`` (a blank one — ``Data_Movimentacao`` is ~58% empty — becomes
		``NaT``, it does not raise); every other column is exact source text.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60.

		Returns
		-------
		pd.DataFrame
			This member's rows. **No unique key is asserted** by the reader.

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ContractError
			If the CSV violates this reader's contract.
		ValueError
			If the archive holds no member for this table in the reference year.
		"""
		str_year = self._date_ref.strftime("%Y")
		self._cls_logger.log_message(
			f"Downloading VLMO CIA_ABERTA ({self._LABEL}) from {self._str_url}", "info"
		)
		# Every non-date column is exact source text, money and quantity included. Derived
		# from the contract so a column added there cannot be silently left untyped, and so the two
		# lists cannot drift; ``apply_dtypes`` requires the sets to be disjoint.
		dict_dtypes = {
			str_col: "str"
			for str_col in self._CONTRACT.tuple_required
			if str_col not in self._DATE_COLS
		}
		with raw_workspace(self._path_raw) as path_dir:
			path_zip = download_file(
				self._str_url,
				path_dir / f"vlmo_cia_aberta_{str_year}.zip",
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
			f"Loaded {len(df_)} {self._LABEL} rows from VLMO CIA_ABERTA {str_year}", "info"
		)
		return stamp_provenance(df_, self._str_url, self._CONTRACT, str_content_hash)
