"""Shared base for the CVM CIA_ABERTA/DOC/FCA (*Formulário Cadastral*) ingestion readers.

`fca_cia_aberta_AAAA.zip` ships **ten members**: an index (`fca_cia_aberta_AAAA.csv`) plus nine
detail tables — auditor, canal_divulgacao, departamento_acionistas, dri, endereco, escriturador,
geral, pais_estrangeiro_negociacao and valor_mobiliario. They differ only in their columns and date
columns, so the download → unzip → select-member → read logic lives here once.

This is a **private** base (leading underscore, its own file): consumers import the ten concrete
`Fca*Reader` adapters, never this class. Each concrete reader sets four class attributes — the
member stem, its `FileContract`, its date columns and a log label — and inherits everything else.

The dump is **partitioned by year**, so `date_ref` selects the *year* and the member filename
carries it. All ten readers download the *same* archive, so a `path_raw` written by one serves the
others.

⚠️ **The index member does not share its satellites' naming convention.** It uses `CNPJ_CIA` /
`DT_REFER` / `DT_RECEB` while every satellite uses `CNPJ_Companhia` / `Data_Referencia`. That is
why each subclass declares its own `_DATE_COLS` rather than inheriting a shared tuple — one
shared default would be wrong for exactly one member, in silence.

⚠️ **Personal data.** `dri.CPF_Responsavel`, `auditor.CPF_Responsavel_Tecnico` and the mixed
`auditor.CPF_CNPJ_Auditor` carry CPFs. They are returned as exact source text but are **never**
declared as CNPJ columns, and the committed fixtures are header-only for that reason.

Every non-date column is exact source text; blank date cells become `NaT` rather than raising,
which several members rely on (e.g. `auditor.Data_Fim_Atuacao_Responsavel_Tecnico` is 100% blank).
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


# CVM open-data **yearly** dump; ``{yyyy}`` is the reference year. Shared by all ten readers.
_BASE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_{yyyy}.zip"

# Reader-owned default retry/backoff (CVM's open-data portal throttles under load): 5 attempts on a
# capped exponential schedule (~2, 4, 8, 10 s). A per-instance ``retry_policy=`` still overrides.
_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class _BaseFcaReader(IngestionReader):
	"""Private base for the ten CIA_ABERTA/DOC/FCA readers.

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
			Directory in which to **persist** the raw ``fca_cia_aberta_AAAA.zip`` and the CSVs
			extracted from it, for a datalake's bronze layer. Created if absent. When ``None`` (the
			default) the artifact is fetched into a temporary directory and discarded. All ten
			readers download the same archive, so a directory written by one serves the others.
		retry_policy : RetryPolicy, optional
			Retry/backoff schedule forwarded to the download seam. When ``None`` (the default) this
			reader's own :attr:`_RETRY_POLICY` class attribute is used.
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
		reader's date columns become pure ``date`` (a blank cell becomes ``NaT``, it does not
		raise); every other column is exact source text.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60.

		Returns
		-------
		pd.DataFrame
			This member's rows. **No unique key is asserted** by the reader. One member
			(``departamento_acionistas``) is legitimately empty in some years.

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
			f"Downloading FCA CIA_ABERTA ({self._LABEL}) from {self._str_url}", "info"
		)
		# Every non-date column is exact source text, CPF and identifiers included. Derived
		# from the contract so a column added there cannot be silently left untyped, and so
		# the two lists cannot drift; ``apply_dtypes`` requires the sets to be disjoint.
		dict_dtypes = {
			str_col: "str"
			for str_col in self._CONTRACT.tuple_required
			if str_col not in self._DATE_COLS
		}
		with raw_workspace(self._path_raw) as path_dir:
			path_zip = download_file(
				self._str_url,
				path_dir / f"fca_cia_aberta_{str_year}.zip",
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
			f"Loaded {len(df_)} {self._LABEL} rows from FCA CIA_ABERTA {str_year}", "info"
		)
		return stamp_provenance(df_, self._str_url, self._CONTRACT, str_content_hash)
