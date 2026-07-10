"""CVM Registro de Classe (RCVM 175) — ingestion (leitura) reader.

Downloads the CVM open-data registry (``registro_fundo_classe.zip``), extracts its
``registro_classe.csv`` member, and returns it as a typed, contract-validated
:class:`pandas.DataFrame`: the **class** level of the post-**Resolução CVM 175**
fund → class → subclass hierarchy.

Relation to the other registro readers
--------------------------------------
This member is foreign-keyed to the fund by ``ID_Registro_Fundo`` (resolves 100% against
:class:`~filings_cvm.ingestion.RegistroFundoReader` on the real file) and is itself referenced
by the subclass via ``ID_Registro_Classe``
(:class:`~filings_cvm.ingestion.RegistroSubclasseReader`).
The three readers are **not** joined into one frame — the hierarchy is one-to-many, so a join
fans rows out; join on the surrogate keys yourself. All three download the same archive, so a
``path_raw`` written by any one serves the others.

Like the other registro readers this is a **current-state snapshot**, so the reader takes **no
``date_ref``**. ``ID_Registro_Classe`` is effectively unique (3 of 36,389 rows repeat it), but
the reader still asserts **no grain** and does not de-duplicate — it returns what CVM published.

Typing
------
Every column is text (``str``) except the five ``Data_*`` columns, coerced to pure ``date``
objects (blanks become ``NaT``). ``Patrimonio_Liquido`` keeps its exact CVM decimal text —
never ``float``. ``CNPJ_Classe`` (bare digits) is the only CNPJ-validated column;
``CNPJ_Auditor``, ``CNPJ_Custodiante`` and ``CNPJ_Controlador`` are counterparty identifiers,
read as text. The dtype map is derived from the contract, so the two cannot drift apart.

Network, unzip, and CSV parsing are delegated to this library's own ``_internal.utils`` seams
— never a vendor framework — so the single I/O boundary is :func:`download_file`.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from filings_cvm._internal.config.contracts.registro_classe import REGISTRO_CLASSE
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.http_downloader import download_file
from filings_cvm._internal.utils.raw_workspace import raw_workspace
from filings_cvm._internal.utils.retry import LogEmitter
from filings_cvm._internal.utils.tabular_reader import read_table
from filings_cvm._internal.utils.zip_extractor import extract_all, find_member


# CVM open-data registry snapshot ZIP, shared by all three registro readers.
_URL = "https://dados.cvm.gov.br/dados/FI/CAD/DADOS/registro_fundo_classe.zip"

_ZIP_FILENAME = "registro_fundo_classe.zip"
_MEMBER = "registro_classe.csv"

# Coerced to pure ``date`` objects; all five parse cleanly on the real file.
_DATE_COLS: tuple[str, ...] = (
	"Data_Registro",
	"Data_Constituicao",
	"Data_Inicio",
	"Data_Inicio_Situacao",
	"Data_Patrimonio_Liquido",
)

# Every non-date column is exact source text. Derived from the contract so the two cannot drift.
_DTYPES: dict[str, str] = {
	str_col: "str" for str_col in REGISTRO_CLASSE.tuple_required if str_col not in _DATE_COLS
}


class RegistroClasseReader(IngestionReader):
	"""Read the CVM Registro de Classe (RCVM 175) open-data snapshot into a typed DataFrame.

	Concrete :class:`IngestionReader` for the ``registro_classe.csv`` member of
	``registro_fundo_classe.zip``. Takes no reference month: the artifact is a current-state
	snapshot.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the class registry into a validated DataFrame.
	"""

	def __init__(
		self,
		path_raw: Path | None = None,
		cls_logger: LogEmitter | None = None,
	) -> None:
		"""Initialise the reader.

		Parameters
		----------
		path_raw : pathlib.Path, optional
			Directory in which to **persist** the raw ``registro_fundo_classe.zip`` and every
			CSV extracted from it, for a datalake's bronze layer. Created if absent. When
			``None`` (the default) the artifact is fetched into a temporary directory and
			discarded. CVM overwrites the file in place, so a persisted snapshot is the only
			record of what the registry said that day.
		cls_logger : LogEmitter, optional
			Injected log sink (``log_message(message, level)``). Defaults to a stdlib-backed
			:class:`LogEmitter`, so no logging import is forced on consumers.
		"""
		self._path_raw = path_raw
		self._cls_logger = cls_logger if cls_logger is not None else LogEmitter()
		self._str_url = _URL

	def read(self, int_timeout_s: int = 60) -> pd.DataFrame:
		"""Download, extract, and parse the class registry into a typed DataFrame.

		The ZIP is fetched to a throwaway directory (or ``path_raw``) and every member
		extracted; the ``registro_classe.csv`` member is read through the tabular seam, which
		enforces the :data:`REGISTRO_CLASSE` contract — all 30 columns plus a coercible
		``CNPJ_Classe`` — before applying the declared types.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60. The archive is ~6.6 MB.

		Returns
		-------
		pd.DataFrame
			One row per class registration, 30 columns, foreign-keyed to the fund by
			``ID_Registro_Fundo``. The five ``Data_*`` columns hold ``datetime.date`` (or
			``NaT``); every other column is exact source text.

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ContractError
			If the CSV violates the :data:`REGISTRO_CLASSE` contract.
		ValueError
			If the archive holds no ``registro_classe.csv`` member.
		"""
		self._cls_logger.log_message(f"Downloading Registro Classe from {self._str_url}", "info")
		with raw_workspace(self._path_raw) as path_dir:
			path_zip = download_file(self._str_url, path_dir / _ZIP_FILENAME, int_timeout_s)
			path_csv = find_member(extract_all(path_zip, path_dir), _MEMBER)
			df_ = read_table(
				path_csv,
				"",
				_DTYPES,
				REGISTRO_CLASSE,
				list_date_cols=_DATE_COLS,
				str_csv_sep=";",
				str_encoding="ISO-8859-1",
				int_csv_quoting=csv.QUOTE_NONE,
			)
		self._cls_logger.log_message(
			f"Loaded {len(df_)} class registrations from Registro Classe", "info"
		)
		return df_
