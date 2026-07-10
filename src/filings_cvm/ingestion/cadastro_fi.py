"""CVM Cadastro de Fundos (CAD/FI) — ingestion (leitura) reader.

Downloads the CVM open-data fund registry (``cad_fi.csv``) and returns it as a typed,
contract-validated :class:`pandas.DataFrame`: the registry of every fund CVM has ever
registered, with its administrator, manager, auditor, custodian and current situation.

No reference month
------------------
Unlike every other reader in this library, CAD/FI is **a current-state snapshot, not a
monthly dump**: a bare ``.csv`` at a fixed URL, with no ``AAAAMM`` partition. So this reader
takes **no** ``date_ref`` — there is no month to select, and asking for one would imply a
history the artifact does not carry. Two sibling artifacts *do* carry history and are out of
scope here (each warrants its own reader): ``cad_fi_hist.zip`` (the change log) and
``registro_fundo_classe.zip`` (the post-Resolução CVM 175 fund/class/subclass registry).

Persist ``path_raw`` on every run if you need the history: each snapshot is the only record
of what the registry said on the day you fetched it, and CVM overwrites the file in place.

There is no unique key — do not use this as a lookup table
----------------------------------------------------------
``CNPJ_FUNDO`` is **not unique**: 10,947 of the 46,809 rows share a CNPJ with another row,
because a fund keeps its CNPJ across regulatory-regime migrations and is re-registered under
a new ``TP_FUNDO`` with a fresh ``CD_CVM``. So one CNPJ legitimately appears as, say, a
cancelled ``FIF`` and a later ``FI``. Neither ``CD_CVM`` alone nor any combination of
``(CNPJ_FUNDO, TP_FUNDO, DT_REG)`` is unique either.

The reader therefore asserts **no grain** and performs no de-duplication: picking a "current"
row per CNPJ is a domain decision (latest ``DT_REG``? ``SIT != "CANCELADA"``?) that belongs to
the consumer, not to a reader whose job is to return what CVM published. A
``df.set_index("CNPJ_FUNDO")`` or a ``merge`` on that column alone will silently fan out rows.

Most rows are historical: ``SIT`` is ``CANCELADA`` on 46,569 of them, and 46,570 carry a
``DT_CANCEL``. Filter on ``SIT`` before treating this as a list of live funds.

Typing
------
Every column is text (``str``) except the nine ``DT_*`` date columns, coerced to pure ``date``
objects (blanks become ``NaT``). Money and fee columns keep their exact CVM decimal text —
never coerced to ``float`` — so no precision is lost; a consumer converts to ``Decimal`` where
it computes. The dtype map is derived from the contract, so the two cannot drift apart.

``CPF_CNPJ_GESTOR`` holds a **CPF** where ``PF_PJ_GESTOR == "PF"`` (47 rows), so it is read as
text and is not validated as a CNPJ. Use ``_internal.utils.br_identifiers`` per row if needed.

Network and CSV parsing are delegated to this library's own ``_internal.utils`` seams
(``http_downloader``, ``tabular_reader``) — never a vendor framework — so the single I/O
boundary is :func:`download_file` and tests mock only there.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from filings_cvm._internal.config.contracts.cad_fi import CAD_FI
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.http_downloader import download_file
from filings_cvm._internal.utils.raw_workspace import raw_workspace
from filings_cvm._internal.utils.retry import LogEmitter
from filings_cvm._internal.utils.tabular_reader import read_table


# CVM open-data registry snapshot. Fixed URL: CVM overwrites this file in place.
_URL = "https://dados.cvm.gov.br/dados/FI/CAD/DADOS/cad_fi.csv"

_FILENAME = "cad_fi.csv"

# Coerced to pure ``date`` objects; all nine parse cleanly on the real file, and the many
# blanks (20,282 for ``DT_INI_ATIV``) become ``NaT``.
_DATE_COLS: tuple[str, ...] = (
	"DT_REG",
	"DT_CONST",
	"DT_CANCEL",
	"DT_INI_SIT",
	"DT_INI_ATIV",
	"DT_INI_EXERC",
	"DT_FIM_EXERC",
	"DT_INI_CLASSE",
	"DT_PATRIM_LIQ",
)

# Every non-date column is exact source text. Derived from the contract so a column added
# there cannot be silently left untyped, and the two lists cannot drift. ``apply_dtypes``
# requires the dtype and date sets to be disjoint, which this comprehension guarantees.
_DTYPES: dict[str, str] = {
	str_col: "str" for str_col in CAD_FI.tuple_required if str_col not in _DATE_COLS
}


class CadastroFiReader(IngestionReader):
	"""Read the CVM CAD/FI open-data registry snapshot into a typed DataFrame.

	Concrete :class:`IngestionReader` for ``cad_fi.csv``. Takes no reference month: the
	artifact is a current-state snapshot, not a monthly dump.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the registry snapshot into a validated DataFrame.
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
			Directory in which to **persist** the raw ``cad_fi.csv`` for a datalake's bronze
			layer. Created if absent. When ``None`` (the default) the artifact is fetched
			into a temporary directory and discarded, so the read leaves nothing on disk.

			Persisting matters more here than for the monthly dumps: CVM overwrites this
			file in place, so a snapshot kept on disk is the **only** record of what the
			registry said on the day it was fetched. It cannot be re-fetched.
		cls_logger : LogEmitter, optional
			Injected log sink (``log_message(message, level)``). Defaults to a stdlib
			-backed :class:`LogEmitter`, so no logging import is forced on consumers.
		"""
		self._path_raw = path_raw
		self._cls_logger = cls_logger if cls_logger is not None else LogEmitter()
		self._str_url = _URL

	def read(self, int_timeout_s: int = 60) -> pd.DataFrame:
		"""Download and parse the registry snapshot into a typed DataFrame.

		The CSV is fetched to a throwaway directory (or to ``path_raw``) and read through the
		tabular seam, which enforces the :data:`CAD_FI` contract — all 41 required columns
		plus a coercible ``CNPJ_FUNDO`` — before applying the declared types.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60. Higher than the
			monthly readers' 30: the snapshot is ~18 MB and unzipped.

		Returns
		-------
		pd.DataFrame
			One row per registry entry, 41 columns. **Not keyed by ``CNPJ_FUNDO``** — a fund
			re-registered under a new regime appears more than once. The nine ``DT_*``
			columns hold ``datetime.date`` (or ``NaT``); every other column is exact source
			text.

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ContractError
			If the CSV violates the :data:`CAD_FI` contract.
		"""
		self._cls_logger.log_message(f"Downloading CAD/FI from {self._str_url}", "info")
		with raw_workspace(self._path_raw) as path_dir:
			path_csv = download_file(self._str_url, path_dir / _FILENAME, int_timeout_s)
			df_ = read_table(
				path_csv,
				"",
				_DTYPES,
				CAD_FI,
				list_date_cols=_DATE_COLS,
				str_csv_sep=";",
				str_encoding="ISO-8859-1",
				int_csv_quoting=csv.QUOTE_NONE,
			)
		self._cls_logger.log_message(
			f"Loaded {len(df_)} registry entries from CAD/FI "
			f"covering {df_['CNPJ_FUNDO'].nunique()} distinct CNPJs",
			"info",
		)
		return df_
