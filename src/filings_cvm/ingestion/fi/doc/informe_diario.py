"""CVM Informe Diário FIF — ingestion (leitura) reader.

Downloads the monthly CVM open-data dump of *fundos de investimento* daily reports
(``inf_diario_fi_AAAAMM.zip`` from the CVM open-data portal), extracts its CSV, and
returns it as a typed, contract-validated :class:`pandas.DataFrame`. This is the
*reading* half of the standard; building the file to *send* to CVM lives in the
``submission`` section (``submission/informe_diario.py``) — and note the two touch
**different artifacts**: submission produces the ``DOC_ARQ`` XML, while this reader
consumes the flat open-data CSV export.

Network, unzip, and CSV parsing are delegated to this library's own ``_internal.utils``
seams (``http_downloader``, ``zip_extractor``, ``tabular_reader``) — never a vendor
framework — so the single I/O boundary is :func:`download_file` and tests mock only
there. Monetary columns are kept as their exact source text (``str``), never coerced to
``float``, so no precision is lost on the way in; a consumer converts to ``Decimal`` at
the point it computes.

Pass ``path_raw`` to keep the downloaded ``.zip`` and its extracted CSV on disk (a
datalake's bronze layer); omit it and they live in a temporary directory that is discarded.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import pandas as pd

from filings_cvm._internal.config.contracts.informe_diario_fif import INFORME_DIARIO_FIF
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.http_downloader import download_file
from filings_cvm._internal.utils.provenance import hash_artifact, stamp_provenance
from filings_cvm._internal.utils.raw_workspace import raw_workspace
from filings_cvm._internal.utils.retry import LogEmitter, RetryPolicy
from filings_cvm._internal.utils.tabular_reader import read_table
from filings_cvm._internal.utils.zip_extractor import extract_all


# CVM open-data monthly dump; ``{ym}`` is the reference month formatted ``AAAAMM``.
_BASE_URL = "https://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/inf_diario_fi_{ym}.zip"

# Explicit column types (never pandas' inference). Monetary columns stay ``str`` — the exact
# CVM decimal text — to avoid float precision loss; ``NR_COTST`` uses the nullable ``Int64`` so
# a blank shareholder count parses instead of raising. ``DT_COMPTC`` is a date column and so is
# declared in ``_DATE_COLS`` (not here — the two sets must stay disjoint for ``apply_dtypes``).
_DTYPES: dict[str, str] = {
	"TP_FUNDO_CLASSE": "str",
	"CNPJ_FUNDO_CLASSE": "str",
	"ID_SUBCLASSE": "str",
	"VL_TOTAL": "str",
	"VL_QUOTA": "str",
	"VL_PATRIM_LIQ": "str",
	"CAPTC_DIA": "str",
	"RESG_DIA": "str",
	"NR_COTST": "Int64",
}
_DATE_COLS: tuple[str, ...] = ("DT_COMPTC",)


class InformeDiarioReader(IngestionReader):
	"""Read the CVM Informe Diário FIF open-data dump into a typed DataFrame.

	Concrete :class:`IngestionReader` for the monthly ``inf_diario_fi`` open-data dump.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference month into a validated DataFrame.
	"""

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
			Any day within the reference month; only its year and month select the
			monthly dump. Defaults to today. The current month's file may not yet be
			published or may be partial — pass a past month for complete data.
		path_raw : pathlib.Path, optional
			Directory in which to **persist** the raw artifact — the downloaded ``.zip``
			and the CSV extracted from it — for a datalake's bronze layer. Created if
			absent. When ``None`` (the default) the artifact is fetched into a temporary
			directory and discarded, so the read leaves nothing on disk.
		retry_policy : RetryPolicy, optional
			Forwarded to the download seam as its retry/backoff schedule; by
			default the seam's throttle-tolerant policy. Pass a
			:class:`RetryPolicy` for a source needing more (or less) patience.
		cls_logger : LogEmitter, optional
			Injected log sink (``log_message(message, level)``). Defaults to a stdlib
			-backed :class:`LogEmitter`, so no logging import is forced on consumers.
		"""
		self._date_ref = date_ref or date.today()
		self._path_raw = path_raw
		self._retry_policy = retry_policy
		self._cls_logger = cls_logger if cls_logger is not None else LogEmitter()
		self._str_url = _BASE_URL.format(ym=self._date_ref.strftime("%Y%m"))

	def read(self, int_timeout_s: int = 30) -> pd.DataFrame:
		"""Download, extract, and parse the reference month into a typed DataFrame.

		The ZIP is fetched to a throwaway directory, its CSV member extracted, and read
		through the tabular seam — which enforces the :data:`INFORME_DIARIO_FIF` contract
		(required columns + a coercible CNPJ column) before applying the declared types.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 30.

		Returns
		-------
		pd.DataFrame
			The month's rows, with declared column types applied.

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ContractError
			If the CSV violates the :data:`INFORME_DIARIO_FIF` contract.
		ValueError
			If the downloaded ZIP holds no CSV member.
		"""
		self._cls_logger.log_message(
			f"Downloading Informe Diário FIF from {self._str_url}", "info"
		)
		with raw_workspace(self._path_raw) as path_dir:
			str_zip = f"inf_diario_fi_{self._date_ref.strftime('%Y%m')}.zip"
			path_zip = download_file(
				self._str_url, path_dir / str_zip, int_timeout_s, retry_policy=self._retry_policy
			)
			str_content_hash = hash_artifact(path_zip)
			path_csv = self._extract_csv(path_zip, path_dir)
			df_ = read_table(
				path_csv,
				"",
				_DTYPES,
				INFORME_DIARIO_FIF,
				list_date_cols=_DATE_COLS,
				str_csv_sep=";",
				str_encoding="ISO-8859-1",
				int_csv_quoting=csv.QUOTE_NONE,
			)
		self._cls_logger.log_message(f"Loaded {len(df_)} rows from Informe Diário FIF", "info")
		return stamp_provenance(df_, self._str_url, INFORME_DIARIO_FIF, str_content_hash)

	@staticmethod
	def _extract_csv(path_zip: Path, path_dest: Path) -> Path:
		"""Extract ``path_zip`` into ``path_dest`` and return its first CSV member.

		Parameters
		----------
		path_zip : pathlib.Path
			The downloaded ZIP archive.
		path_dest : pathlib.Path
			Destination directory for the extracted members.

		Returns
		-------
		pathlib.Path
			Path to the extracted CSV file.

		Raises
		------
		ValueError
			If the archive contains no ``.csv`` member.
		"""
		for path_member in extract_all(path_zip, path_dest):
			if path_member.suffix.lower() == ".csv":
				return path_member
		raise ValueError(f"No CSV member found in {path_zip.name}")
