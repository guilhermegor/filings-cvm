"""Shared base for the CVM CIA_ABERTA/DOC/ITR (*Informações Trimestrais*) readers.

`itr_cia_aberta_AAAA.zip` holds **19 members and 3.640.994 rows** in 2025 — three times the DFP
and the largest artifact in this library. It carries the filing index,
eight statement types each published in a *consolidado* and an *individual* variant, plus the share
composition and the reviewer's opinion. They differ only in their columns and date columns, so the
download → unzip → select-member → read logic lives here once.

This is a **private** base (leading underscore, its own file): consumers import the concrete
`ItrCiaAberta*Reader` adapters, never this class. Each concrete reader sets four class attributes —
the member stem, its `FileContract`, its date columns and a log label — and inherits the rest.

The dump is **partitioned by year**, so `date_ref` selects the *year* and the member filename
carries it. Every reader downloads the *same* archive, so a `path_raw` written by one serves all.

⚠️ **`VL_CONTA` is money and stays exact text.** It arrives with ten decimal places
(`2398719197.0000000000`), which is precisely where a binary float drops published digits silently
— the same failure already measured on VLMO. `bin/check_dtypes.py` enforces it; convert to
`Decimal` downstream.

⚠️⚠️ **The value's scale lives in a *different column*.** `ESCALA_MOEDA` is `MIL` or `UNIDADE`, so
`VL_CONTA` is expressed in thousands whenever it says `MIL`. Summing `VL_CONTA` without reading
`ESCALA_MOEDA` is wrong by a factor of a thousand. The readers stay thin and **do not rescale** —
that is a downstream decision, and rescaling here would destroy the published figure.

⚠️ **No unique key is asserted.** `ORDEM_EXERC` (`ÚLTIMO` / `PENÚLTIMO`) means each account appears
twice per filing — the current period and the comparative one.

⚠️ **Unlike FCA and FRE, every member here uses the index's naming** (`CNPJ_CIA`, `DT_REFER`), not
a CamelCase satellite convention. That is a measured property of this dataset, not a portal rule.

⚠️⚠️ **Eighteen of these nineteen members have headers byte-identical to DFP's — and exactly one
does not.** The quarterly filing is subject to a *revisão especial*, not a full audit, so `parecer`
spells its fifth column `TP_RELAT_ESP` where DFP spells it `TP_RELAT_AUD`. Same width, same
position, seven of eight names in common. Copying the sibling dataset's contract would be wrong in
exactly one column and pass everything except the pinned header — which is why every contract here
is generated from **this** dataset's own published header.
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


# CVM open-data **yearly** dump; ``{yyyy}`` is the reference year. Shared by every ITR reader.
_BASE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_{yyyy}.zip"

# Reader-owned default retry/backoff (CVM's open-data portal throttles under load): 5 attempts on a
# capped exponential schedule (~2, 4, 8, 10 s). A per-instance ``retry_policy=`` still overrides.
_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class _BaseItrReader(IngestionReader):
	"""Private base for every CIA_ABERTA/DOC/ITR reader.

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
			filename carries it. Defaults to today. The current year's file is published as
			companies file, so pass a past year for a complete series.
		path_raw : pathlib.Path, optional
			Directory in which to **persist** the raw ``itr_cia_aberta_AAAA.zip`` and the CSVs
			extracted from it, for a datalake's bronze layer. Created if absent. When ``None``
			(the default) the artifact is fetched into a temporary directory and discarded. Every
			ITR reader downloads the same archive, so a directory written by one serves the rest.
		retry_policy : RetryPolicy, optional
			Retry/backoff schedule forwarded to the download seam. When ``None`` (the default)
			this reader's own :attr:`_RETRY_POLICY` class attribute is used.
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
		seam, which enforces this reader's contract before applying the declared types. This
		reader's date columns become pure ``date`` (a blank cell becomes ``NaT``); every other
		column is exact source text, ``VL_CONTA`` included.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60.

		Returns
		-------
		pd.DataFrame
			This member's rows. **No unique key is asserted** — see the module docstring on
			``ORDEM_EXERC``.

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
			f"Downloading ITR CIA_ABERTA ({self._LABEL}) from {self._str_url}", "info"
		)
		# Every non-date column is exact source text, money and counts included. Derived from the
		# contract so a column added there cannot be silently left untyped, and so the two lists
		# cannot drift; ``apply_dtypes`` requires the sets to be disjoint.
		dict_dtypes = {
			str_col: "str"
			for str_col in self._CONTRACT.tuple_required
			if str_col not in self._DATE_COLS
		}
		with raw_workspace(self._path_raw) as path_dir:
			path_zip = download_file(
				self._str_url,
				path_dir / f"itr_cia_aberta_{str_year}.zip",
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
			f"Loaded {len(df_)} {self._LABEL} rows from ITR CIA_ABERTA {str_year}", "info"
		)
		return stamp_provenance(df_, self._str_url, self._CONTRACT, str_content_hash)
