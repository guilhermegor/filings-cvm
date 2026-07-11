"""CVM Registro de Fundo (RCVM 175) — ingestion (leitura) reader.

Downloads the CVM open-data post-**Resolução CVM 175** registry
(``registro_fundo_classe.zip``), extracts its ``registro_fundo.csv`` member, and returns it
as a typed, contract-validated :class:`pandas.DataFrame`: the **fund** level of the
fund → class → subclass hierarchy that replaced the flat CAD/FI registry.

Why this, not ``cad_fi.csv``
----------------------------
This is where **live** funds are. On the same day, ``registro_fundo.csv`` held 34,172 funds
``Em Funcionamento Normal`` against 22 in the legacy ``cad_fi.csv`` (which is ~99.5%
cancelled). Reach for :class:`~filings_cvm.ingestion.CadastroFiReader` only for the historical
pre-175 registry; reach for this for the current one.

Three readers, one archive
--------------------------
``registro_fundo_classe.zip`` ships three members at three grains, each with its own reader:

- **this reader** — ``registro_fundo.csv``, the fund (``ID_Registro_Fundo``).
- :class:`~filings_cvm.ingestion.RegistroClasseReader` — ``registro_classe.csv``, the class
  (``ID_Registro_Classe``), foreign-keyed to the fund by ``ID_Registro_Fundo``.
- :class:`~filings_cvm.ingestion.RegistroSubclasseReader` — ``registro_subclasse.csv``, the
  subclass (``ID_Subclasse``), foreign-keyed to the class by ``ID_Registro_Classe``.

They are **not** joined into one frame: the hierarchy is one-to-many (a fund has many classes,
a class many subclasses), so a join would fan the fund's rows out — the grain-mixing trap the
CDA reader documents. Join on the surrogate keys yourself, at the grain you need. All three
download the same archive, so a ``path_raw`` written by any one serves the others.

No reference month, near-unique key
-----------------------------------
Like CAD/FI this is a **current-state snapshot** (a fixed URL, no ``AAAAMM`` partition), so the
reader takes **no ``date_ref``**, and CVM overwrites the file in place — persist ``path_raw``
to keep a day's snapshot. ``ID_Registro_Fundo`` is *nearly* unique but not perfectly (1,121 of
89,124 rows repeat it), so the reader asserts **no grain** and does not de-duplicate; treat a
key collision as the source's, not the reader's.

Typing
------
Every column is text (``str``) except the eight ``Data_*`` columns, coerced to pure ``date``
objects (blanks become ``NaT``). ``Patrimonio_Liquido`` keeps its exact CVM decimal text —
never ``float`` — so no precision is lost. ``CPF_CNPJ_Gestor`` holds a **CPF** where
``Tipo_Pessoa_Gestor == "PF"`` (211 rows), so it is read as text and never validated as a CNPJ.
The dtype map is derived from the contract, so the two cannot drift apart.

Network, unzip, and CSV parsing are delegated to this library's own ``_internal.utils`` seams
— never a vendor framework — so the single I/O boundary is :func:`download_file`.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from filings_cvm._internal.config.contracts.registro_fundo import REGISTRO_FUNDO
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.http_downloader import download_file
from filings_cvm._internal.utils.provenance import hash_artifact, stamp_provenance
from filings_cvm._internal.utils.raw_workspace import raw_workspace
from filings_cvm._internal.utils.retry import LogEmitter, RetryPolicy
from filings_cvm._internal.utils.tabular_reader import read_table
from filings_cvm._internal.utils.zip_extractor import extract_all, find_member


# CVM open-data registry snapshot ZIP, shared by all three registro readers. Fixed URL:
# CVM overwrites this file in place.
_URL = "https://dados.cvm.gov.br/dados/FI/CAD/DADOS/registro_fundo_classe.zip"

_ZIP_FILENAME = "registro_fundo_classe.zip"
_MEMBER = "registro_fundo.csv"

# Coerced to pure ``date`` objects; all eight parse cleanly on the real file, and the blanks
# (37,258 for ``Data_Cancelamento``) become ``NaT``.
_DATE_COLS: tuple[str, ...] = (
	"Data_Registro",
	"Data_Constituicao",
	"Data_Cancelamento",
	"Data_Inicio_Situacao",
	"Data_Adaptacao_RCVM175",
	"Data_Inicio_Exercicio_Social",
	"Data_Fim_Exercicio_Social",
	"Data_Patrimonio_Liquido",
)

# Every non-date column is exact source text. Derived from the contract so a column added
# there cannot be silently left untyped, and the two lists cannot drift.
_DTYPES: dict[str, str] = {
	str_col: "str" for str_col in REGISTRO_FUNDO.tuple_required if str_col not in _DATE_COLS
}


class RegistroFundoReader(IngestionReader):
	"""Read the CVM Registro de Fundo (RCVM 175) open-data snapshot into a typed DataFrame.

	Concrete :class:`IngestionReader` for the ``registro_fundo.csv`` member of
	``registro_fundo_classe.zip``. Takes no reference month: the artifact is a current-state
	snapshot.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the fund registry into a validated DataFrame.
	"""

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
			Directory in which to **persist** the raw ``registro_fundo_classe.zip`` and every
			CSV extracted from it — not just the member read — for a datalake's bronze layer.
			Created if absent. When ``None`` (the default) the artifact is fetched into a
			temporary directory and discarded. CVM overwrites the file in place, so a persisted
			snapshot is the only record of what the registry said that day.
		retry_policy : RetryPolicy, optional
			Forwarded to the download seam as its retry/backoff schedule; by
			default the seam's throttle-tolerant policy. Pass a
			:class:`RetryPolicy` for a source needing more (or less) patience.
		cls_logger : LogEmitter, optional
			Injected log sink (``log_message(message, level)``). Defaults to a stdlib-backed
			:class:`LogEmitter`, so no logging import is forced on consumers.
		"""
		self._path_raw = path_raw
		self._retry_policy = retry_policy
		self._cls_logger = cls_logger if cls_logger is not None else LogEmitter()
		self._str_url = _URL

	def read(self, int_timeout_s: int = 60) -> pd.DataFrame:
		"""Download, extract, and parse the fund registry into a typed DataFrame.

		The ZIP is fetched to a throwaway directory (or ``path_raw``) and every member
		extracted; the ``registro_fundo.csv`` member is read through the tabular seam, which
		enforces the :data:`REGISTRO_FUNDO` contract — all 21 columns plus a coercible
		``CNPJ_Fundo`` — before applying the declared types.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60. The archive is ~6.6 MB.

		Returns
		-------
		pd.DataFrame
			One row per fund registration, 21 columns. **Not strictly keyed by
			``ID_Registro_Fundo``** (1,121 rows repeat it). The eight ``Data_*`` columns hold
			``datetime.date`` (or ``NaT``); every other column is exact source text.

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ContractError
			If the CSV violates the :data:`REGISTRO_FUNDO` contract.
		ValueError
			If the archive holds no ``registro_fundo.csv`` member.
		"""
		self._cls_logger.log_message(f"Downloading Registro Fundo from {self._str_url}", "info")
		with raw_workspace(self._path_raw) as path_dir:
			path_zip = download_file(
				self._str_url,
				path_dir / _ZIP_FILENAME,
				int_timeout_s,
				retry_policy=self._retry_policy,
			)
			str_content_hash = hash_artifact(path_zip)
			path_csv = find_member(extract_all(path_zip, path_dir), _MEMBER)
			df_ = read_table(
				path_csv,
				"",
				_DTYPES,
				REGISTRO_FUNDO,
				list_date_cols=_DATE_COLS,
				str_csv_sep=";",
				str_encoding="ISO-8859-1",
				int_csv_quoting=csv.QUOTE_NONE,
			)
		self._cls_logger.log_message(
			f"Loaded {len(df_)} fund registrations from Registro Fundo", "info"
		)
		return stamp_provenance(df_, self._str_url, REGISTRO_FUNDO, str_content_hash)
