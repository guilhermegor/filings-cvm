"""CVM Lâmina FIF — ingestion (leitura) reader.

Downloads the monthly CVM open-data Lâmina dump (``lamina_fi_AAAAMM.zip``), extracts its
``lamina_fi_AAAAMM.csv`` member — the **fact sheet proper** — and returns it as a typed,
contract-validated :class:`pandas.DataFrame`: one row per fund class, with the 78 fields CVM
publishes on the lâmina (objective, investment policy, fees, redemption terms, five-year
performance, worked cost examples, SAC contacts).

Relation to the other Lâmina reader
-----------------------------------
:class:`~filings_cvm.ingestion.LaminaCarteiraReader` reads a **different member of this same
archive** — the allocation broken down by asset type. Both are downloaded together, so a
``path_raw`` bronze layer written by either reader serves the other without a re-fetch.

Why ``QUOTE_NONE`` is load-bearing here
---------------------------------------
The free-text fields (``OBJETIVO``, ``POLIT_INVEST``, ``TAXA_ADM_OBS``, …) contain stray,
unbalanced ``"`` characters. Under pandas' default ``QUOTE_MINIMAL`` the parser treats one of
them as opening a quoted field, swallows the following delimiters and row terminator, and
merges two records into one — on ``lamina_fi_202504.csv`` that yields a 142-field row and a
hard ``ParserError``. Read with ``QUOTE_NONE``, all 1,325 lines parse at exactly 78 fields.
CVM emits no quoting at all, so honouring quotes is simply wrong for these dumps; the
delimiter never appears inside a field.

Typing
------
Every column is text (``str``) except the four ``DT_*`` date columns, which are coerced to
pure ``date`` objects. Money, percentage, and day-count columns keep their exact CVM decimal
text — never coerced to ``float``, so no precision is lost on the way in. A consumer converts
to ``Decimal`` where it computes. The dtype map is derived from the contract rather than
retyped, so the two can never drift apart.

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

from filings_cvm._internal.config.contracts.lamina_fif import LAMINA_FIF
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.http_downloader import download_file
from filings_cvm._internal.utils.raw_workspace import raw_workspace
from filings_cvm._internal.utils.retry import LogEmitter
from filings_cvm._internal.utils.tabular_reader import read_table
from filings_cvm._internal.utils.zip_extractor import extract_all, find_member


# CVM open-data monthly dump; ``{ym}`` is the reference month formatted ``AAAAMM``.
_BASE_URL = "https://dados.cvm.gov.br/dados/FI/DOC/LAMINA/DADOS/lamina_fi_{ym}.zip"

# The member to read, named exactly. ``lamina_fi_AAAAMM.csv`` is a *prefix* of both
# ``lamina_fi_carteira_AAAAMM.csv`` and ``lamina_fi_rentab_*_AAAAMM.csv``, so a prefix match
# would pick whichever the archive happens to list first — see ``find_member``.
_MEMBER_LAMINA = "lamina_fi_{ym}.csv"

# Coerced to pure ``date`` objects; all four parse cleanly on the real dump, with blanks
# (77 of 1,324 rows for the two ``*_DESPESA`` columns) becoming ``NaT``.
_DATE_COLS: tuple[str, ...] = (
	"DT_COMPTC",
	"DT_INI_DESPESA",
	"DT_FIM_DESPESA",
	"DT_INI_ATIV_5ANO",
)

# Every non-date column is exact source text. Derived from the contract so a column added
# there cannot be silently left untyped, and the two lists cannot drift. ``apply_dtypes``
# requires the dtype and date sets to be disjoint, which this comprehension guarantees.
_DTYPES: dict[str, str] = {
	str_col: "str" for str_col in LAMINA_FIF.tuple_required if str_col not in _DATE_COLS
}


class LaminaReader(IngestionReader):
	"""Read the CVM Lâmina FIF open-data fact sheet into a typed DataFrame.

	Concrete :class:`IngestionReader` for the ``lamina_fi`` member of the monthly Lâmina
	dump: one row per fund class, 78 columns.

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
		happens to want). The lâmina member is then read through the tabular seam, which
		enforces the :data:`LAMINA_FIF` contract — all 78 required columns plus a
		coercible CNPJ column — before applying the declared types.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 30.

		Returns
		-------
		pd.DataFrame
			One row per fund class, 78 columns. Every column is exact source text except
			the four ``DT_*`` columns, which hold ``datetime.date`` (or ``NaT``).

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ContractError
			If the CSV violates the :data:`LAMINA_FIF` contract.
		ValueError
			If the archive holds no ``lamina_fi_AAAAMM.csv`` member.
		"""
		self._cls_logger.log_message(f"Downloading Lâmina FIF from {self._str_url}", "info")
		str_ym = self._date_ref.strftime("%Y%m")
		with raw_workspace(self._path_raw) as path_dir:
			path_zip = download_file(
				self._str_url, path_dir / f"lamina_fi_{str_ym}.zip", int_timeout_s
			)
			list_members = extract_all(path_zip, path_dir)
			path_csv = find_member(list_members, _MEMBER_LAMINA.format(ym=str_ym))
			df_ = read_table(
				path_csv,
				"",
				_DTYPES,
				LAMINA_FIF,
				list_date_cols=_DATE_COLS,
				str_csv_sep=";",
				str_encoding="ISO-8859-1",
				int_csv_quoting=csv.QUOTE_NONE,
			)
		self._cls_logger.log_message(f"Loaded {len(df_)} fund classes from Lâmina FIF", "info")
		return df_
