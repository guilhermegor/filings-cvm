"""CVM Lâmina carteira FIF — ingestion (leitura) reader.

Downloads the monthly CVM open-data Lâmina dump (``lamina_fi_AAAAMM.zip``), extracts its
``lamina_fi_carteira_AAAAMM.csv`` member, and returns it as a typed, contract-validated
:class:`pandas.DataFrame`: each fund's portfolio broken down by **asset type**, as a
percentage of net worth.

Relation to the other portfolio readers
---------------------------------------
Three CVM artifacts describe a fund's holdings, at three granularities. They are separate
readers because they are separate files, not three views of one:

- :class:`~filings_cvm.ingestion.CdaReader` (``cda_fi_*.zip``) — one row *per security
  held*, with its market value. The position-level truth.
- **This reader** (``lamina_fi_carteira_*.csv``) — one row *per asset type* per fund
  (fund × ``TP_ATIVO``), carrying only ``PR_PL_ATIVO``, the share of net worth. The
  allocation summary CVM itself publishes on the fact sheet.
- ``lamina_fi_*.csv`` — the fact sheet proper. A different member of *this same archive*,
  and the subject of its own reader.

``PR_PL_ATIVO`` is a **signed** percentage and the shares do **not** sum to 100: a fund
may hold short or leveraged exposure. Across 2025-04 the per-fund total ranged from
-37.08 to 1123.00 (median 100.03). So no "shares total 100%" invariant is asserted here —
it would reject perfectly valid leveraged funds.

Typing
------
``PR_PL_ATIVO`` stays ``str`` — the exact CVM decimal text — like every money and quantity
column in this library. A percentage feeding a weighted aggregate suffers the same silent
float drift as a price, so the consumer converts to ``Decimal`` where it computes.

Network, unzip, and CSV parsing are delegated to this library's own ``_internal.utils``
seams (``http_downloader``, ``zip_extractor``, ``tabular_reader``) — never a vendor
framework — so the single I/O boundary is :func:`download_file` and tests mock only there.

Pass ``path_raw`` to keep the downloaded ``.zip`` and its extracted CSVs on disk (a
datalake's bronze layer); omit it and they live in a temporary directory that is discarded.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import pandas as pd

from filings_cvm._internal.config.contracts.lamina_carteira_fif import LAMINA_CARTEIRA_FIF
from filings_cvm._internal.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.http_downloader import download_file
from filings_cvm._internal.utils.raw_workspace import raw_workspace
from filings_cvm._internal.utils.retry import LogEmitter
from filings_cvm._internal.utils.tabular_reader import read_table
from filings_cvm._internal.utils.zip_extractor import extract_all


# CVM open-data monthly dump; ``{ym}`` is the reference month formatted ``AAAAMM``.
_BASE_URL = "https://dados.cvm.gov.br/dados/FI/DOC/LAMINA/DADOS/lamina_fi_{ym}.zip"

# The member to read. The archive also holds ``lamina_fi_AAAAMM.csv`` and two
# ``lamina_fi_rentab_*`` series; matching on this longer prefix excludes all three.
_PREFIX_CARTEIRA = "lamina_fi_carteira_"

# Explicit column types (never pandas' inference). Every column is text: the identifying
# keys must not be inferred (a masked CNPJ must not become a float), and ``PR_PL_ATIVO``
# keeps its exact CVM decimal text. ``DT_COMPTC`` is a date column and so is declared in
# ``_DATE_COLS`` — the two sets must stay disjoint for ``apply_dtypes``.
_DTYPES: dict[str, str] = {
	"TP_FUNDO_CLASSE": "str",
	"CNPJ_FUNDO_CLASSE": "str",
	"ID_SUBCLASSE": "str",
	"DENOM_SOCIAL": "str",
	"TP_ATIVO": "str",
	"PR_PL_ATIVO": "str",
}
_DATE_COLS: tuple[str, ...] = ("DT_COMPTC",)


class LaminaCarteiraReader(IngestionReader):
	"""Read the CVM Lâmina carteira FIF open-data CSV into a typed DataFrame.

	Concrete :class:`IngestionReader` for the ``lamina_fi_carteira`` member of the monthly
	Lâmina dump: one row per fund per asset type, with that type's share of net worth.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference month into a validated DataFrame.
	"""

	def __init__(
		self,
		date_ref: date | None = None,
		path_raw: Path | None = None,
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
			and every CSV extracted from it, not just the member read — for a datalake's
			bronze layer. Created if absent. When ``None`` (the default) the artifact is
			fetched into a temporary directory and discarded, so the read leaves nothing
			on disk.
		cls_logger : LogEmitter, optional
			Injected log sink (``log_message(message, level)``). Defaults to a stdlib
			-backed :class:`LogEmitter`, so no logging import is forced on consumers.
		"""
		self._date_ref = date_ref or date.today()
		self._path_raw = path_raw
		self._cls_logger = cls_logger if cls_logger is not None else LogEmitter()
		self._str_url = _BASE_URL.format(ym=self._date_ref.strftime("%Y%m"))

	def read(self, int_timeout_s: int = 30) -> pd.DataFrame:
		"""Download, extract, and parse the reference month into a typed DataFrame.

		The ZIP is fetched to a throwaway directory and every member extracted (so a
		``path_raw`` bronze layer keeps the whole artifact, not the slice this reader
		happens to want). The ``carteira`` member is then read through the tabular seam,
		which enforces the :data:`LAMINA_CARTEIRA_FIF` contract — required columns plus a
		coercible CNPJ column — before applying the declared types.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 30.

		Returns
		-------
		pd.DataFrame
			One row per fund per asset type (fund × ``TP_ATIVO``), with ``PR_PL_ATIVO``
			carrying that type's signed share of the fund's net worth as exact source
			text.

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ContractError
			If the CSV violates the :data:`LAMINA_CARTEIRA_FIF` contract.
		ValueError
			If the archive holds no ``lamina_fi_carteira_*`` member.
		"""
		self._cls_logger.log_message(
			f"Downloading Lâmina carteira FIF from {self._str_url}", "info"
		)
		with raw_workspace(self._path_raw) as path_dir:
			str_zip = f"lamina_fi_{self._date_ref.strftime('%Y%m')}.zip"
			path_zip = download_file(self._str_url, path_dir / str_zip, int_timeout_s)
			path_csv = self._find_carteira(extract_all(path_zip, path_dir))
			df_ = read_table(
				path_csv,
				"",
				_DTYPES,
				LAMINA_CARTEIRA_FIF,
				list_date_cols=_DATE_COLS,
				str_csv_sep=";",
				str_encoding="ISO-8859-1",
				int_csv_quoting=csv.QUOTE_NONE,
			)
		self._cls_logger.log_message(
			f"Loaded {len(df_)} allocation rows from Lâmina carteira FIF "
			f"across {df_['TP_ATIVO'].nunique()} asset types",
			"info",
		)
		return df_

	@staticmethod
	def _find_carteira(list_members: list[Path]) -> Path:
		"""Return the archive's ``carteira`` member.

		Parameters
		----------
		list_members : list of pathlib.Path
			The archive's extracted members.

		Returns
		-------
		pathlib.Path
			Path to the extracted ``lamina_fi_carteira_*.csv``.

		Raises
		------
		ValueError
			If the archive contains no such member.
		"""
		for path_member in list_members:
			if path_member.name.startswith(_PREFIX_CARTEIRA):
				return path_member
		raise ValueError("No Lâmina carteira member found in the archive")
