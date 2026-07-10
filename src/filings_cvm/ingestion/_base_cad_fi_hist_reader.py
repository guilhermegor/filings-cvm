"""Shared base for the CVM CAD/FI *histórico* (change-log) ingestion readers.

`cad_fi_hist.zip` ships **19 members**, one per mutable attribute of the legacy CAD/FI
registry (situação, denominação, taxa de administração, gestor, …). Each member is a
per-attribute **change-log**: `CNPJ_FUNDO`, `DT_REG`, the attribute's value column(s), and its
effective-date columns (`DT_INI_*`, usually `DT_FIM_*`). The 19 are a **uniform family** — same
entity, same kind of frame — differing only in which attribute's history they carry.

Rather than repeat the download → unzip → select-member → read logic in each of the 19 public
readers, that logic lives here once. This is a **private** base (leading underscore, its own
file): consumers import the 19 concrete `CadastroFiHist*Reader` adapters, never this class. Each
concrete reader is a thin subclass that sets three class attributes — the member filename, its
`FileContract`, and its date columns — and inherits everything else.

Like the other CAD readers this is a **current-state snapshot** (fixed URL, no `AAAAMM`
partition), so the readers take **no `date_ref`**, and CVM overwrites the file in place — persist
`path_raw` to keep a day's snapshot. All 19 readers download the *same* archive, so a `path_raw`
written by any one serves the others. No grain is asserted: a change-log naturally has many rows
per fund.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import ClassVar

import pandas as pd

from filings_cvm._internal.config.contracts import FileContract
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.http_downloader import download_file
from filings_cvm._internal.utils.raw_workspace import raw_workspace
from filings_cvm._internal.utils.retry import LogEmitter
from filings_cvm._internal.utils.tabular_reader import read_table
from filings_cvm._internal.utils.zip_extractor import extract_all, find_member


# CVM open-data registry-history snapshot ZIP, shared by all 19 readers. Fixed URL: CVM
# overwrites this file in place.
_URL = "https://dados.cvm.gov.br/dados/FI/CAD/DADOS/cad_fi_hist.zip"

_ZIP_FILENAME = "cad_fi_hist.zip"


class _BaseCadFiHistReader(IngestionReader):
	"""Private base for the 19 CAD/FI change-log readers.

	A concrete reader sets :attr:`_MEMBER`, :attr:`_CONTRACT`, :attr:`_DATE_COLS` and
	:attr:`_LABEL`; everything else — the shared download/unzip/parse — lives here.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse this reader's change-log member into a validated DataFrame.
	"""

	# Set by each concrete subclass. Declared here so the shared ``read`` can reference them.
	_MEMBER: ClassVar[str]
	_CONTRACT: ClassVar[FileContract]
	_DATE_COLS: ClassVar[tuple[str, ...]]
	_LABEL: ClassVar[str]

	def __init__(
		self,
		path_raw: Path | None = None,
		cls_logger: LogEmitter | None = None,
	) -> None:
		"""Initialise the reader.

		Parameters
		----------
		path_raw : pathlib.Path, optional
			Directory in which to **persist** the raw ``cad_fi_hist.zip`` and every CSV
			extracted from it — not just the member read — for a datalake's bronze layer.
			Created if absent. When ``None`` (the default) the artifact is fetched into a
			temporary directory and discarded. CVM overwrites the file in place, so a persisted
			snapshot is the only record of what the registry history said that day.
		cls_logger : LogEmitter, optional
			Injected log sink (``log_message(message, level)``). Defaults to a stdlib-backed
			:class:`LogEmitter`, so no logging import is forced on consumers.
		"""
		self._path_raw = path_raw
		self._cls_logger = cls_logger if cls_logger is not None else LogEmitter()
		self._str_url = _URL

	def read(self, int_timeout_s: int = 60) -> pd.DataFrame:
		"""Download, extract, and parse this reader's change-log member into a typed DataFrame.

		The ZIP is fetched to a throwaway directory (or ``path_raw``) and every member
		extracted; this reader's member is read through the tabular seam, which enforces its
		:class:`FileContract` — every declared column plus a coercible ``CNPJ_FUNDO`` — before
		applying the declared types. Every ``DT_*`` column becomes a pure ``date``; every other
		column is exact source text.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60. The archive is ~18 MB.

		Returns
		-------
		pd.DataFrame
			The attribute's change-log — one row per (fund, effective period). **No grain is
			asserted:** a fund appears once per historical value of the attribute.

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
			f"Downloading CAD/FI histórico ({self._LABEL}) from {self._str_url}", "info"
		)
		dict_dtypes = {
			str_col: "str"
			for str_col in self._CONTRACT.tuple_required
			if str_col not in self._DATE_COLS
		}
		with raw_workspace(self._path_raw) as path_dir:
			path_zip = download_file(self._str_url, path_dir / _ZIP_FILENAME, int_timeout_s)
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
			f"Loaded {len(df_)} {self._LABEL} change-log rows from CAD/FI histórico", "info"
		)
		return df_
