"""CVM Cadastro de Companhias Estrangeiras — ingestion (leitura) reader.

Downloads the CVM open-data registry **snapshot** of the foreign companies registered with the
CVM (``cad_cia_estrang.csv``, dataset ``CIA_ESTRANG/CAD``) and returns it as a typed,
contract-validated :class:`pandas.DataFrame`. Inaugurates the ``cia_estrang/`` portal root and
**opens Wave 4** of the portal sweep (issue #41).

Like ``cad_fi.csv`` / ``cad_adm_fii.csv``, it is a bare CSV at a **fixed URL** that CVM overwrites
in place — hence there is **no** ``date_ref``, and a ``path_raw`` snapshot is the only record of
what the registry said on the day it was fetched (it cannot be re-fetched).

The seven ``DT_*`` columns are coerced to pure ``date`` (blanks become ``NaT``); ``MOTIVO_CANCEL``
is free text, and every other column is exact source text. Network and CSV parsing go through this
library's own ``_internal.utils`` seams, so the single I/O boundary is :func:`download_file`.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import ClassVar

import pandas as pd

from filings_cvm._internal.config.contracts.cad_cia_estrang import CAD_CIA_ESTRANG
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.http_downloader import download_file
from filings_cvm._internal.utils.provenance import hash_artifact, stamp_provenance
from filings_cvm._internal.utils.raw_workspace import raw_workspace
from filings_cvm._internal.utils.retry import LogEmitter, RetryPolicy
from filings_cvm._internal.utils.tabular_reader import read_table


# CVM open-data registry snapshot. Fixed URL: CVM overwrites this file in place.
_URL = "https://dados.cvm.gov.br/dados/CIA_ESTRANG/CAD/DADOS/cad_cia_estrang.csv"

_FILENAME = "cad_cia_estrang.csv"

# Coerced to pure ``date`` objects; blanks become ``NaT``. ``MOTIVO_CANCEL`` is deliberately absent
# — it is free text, not a date.
_DATE_COLS: tuple[str, ...] = (
	"DT_REG",
	"DT_CONST",
	"DT_CANCEL",
	"DT_INI_SIT",
	"DT_INI_CATEG",
	"DT_INI_SIT_EMISSOR",
	"DT_INI_RESP",
)

# Every non-date column is exact source text. Derived from the contract so a column added there
# cannot be silently left untyped, and the two lists cannot drift.
_DTYPES: dict[str, str] = {
	str_col: "str" for str_col in CAD_CIA_ESTRANG.tuple_required if str_col not in _DATE_COLS
}

# Reader-owned default retry/backoff (CVM's open-data portal throttles under load): 5 attempts on a
# capped exponential schedule (~2, 4, 8, 10 s). Per-reader tunable via ``_RETRY_POLICY``; a
# per-instance ``retry_policy=`` still overrides.
_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class CadastroCiaEstrangReader(IngestionReader):
	"""Read the CVM Cadastro de Companhias Estrangeiras registry snapshot into a typed DataFrame.

	Concrete :class:`IngestionReader` for ``cad_cia_estrang.csv``. Takes no reference date: the
	artifact is a current-state snapshot, not a partitioned dump.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the registry snapshot into a validated DataFrame.
	"""

	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY

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
			Directory in which to **persist** the raw ``cad_cia_estrang.csv`` for a datalake's
			bronze layer. Created if absent. When ``None`` (the default) the artifact is fetched
			into a temporary directory and discarded, so the read leaves nothing on disk.

			Persisting matters more here than for the partitioned dumps: CVM overwrites this file
			in place, so a snapshot kept on disk is the **only** record of what the registry said
			on the day it was fetched. It cannot be re-fetched.
		retry_policy : RetryPolicy, optional
			Retry/backoff schedule forwarded to the download seam. When ``None`` (the default) this
			reader's own :attr:`_RETRY_POLICY` class attribute is used. Pass a :class:`RetryPolicy`
			to override it for this one instance.
		cls_logger : LogEmitter, optional
			Injected log sink (``log_message(message, level)``). Defaults to a stdlib-backed
			:class:`LogEmitter`, so no logging import is forced on consumers.
		"""
		self._path_raw = path_raw
		self._retry_policy = retry_policy if retry_policy is not None else self._RETRY_POLICY
		self._cls_logger = cls_logger if cls_logger is not None else LogEmitter()
		self._str_url = _URL

	def read(self, int_timeout_s: int = 60) -> pd.DataFrame:
		"""Download and parse the registry snapshot into a typed DataFrame.

		The CSV is fetched to a throwaway directory (or ``path_raw``) and read through the tabular
		seam, which enforces the :data:`CAD_CIA_ESTRANG` contract (all 49 columns plus coercible
		``CNPJ`` / ``CNPJ_AUDITOR``) before applying the declared types. The seven ``DT_*`` columns
		become ``datetime.date`` (or ``NaT``); others are exact source text.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60.

		Returns
		-------
		pd.DataFrame
			One row per registered foreign company, 49 columns.

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ContractError
			If the CSV violates the :data:`CAD_CIA_ESTRANG` contract.
		"""
		self._cls_logger.log_message(
			f"Downloading Cadastro de Companhias Estrangeiras from {self._str_url}", "info"
		)
		with raw_workspace(self._path_raw) as path_dir:
			path_csv = download_file(
				self._str_url, path_dir / _FILENAME, int_timeout_s, retry_policy=self._retry_policy
			)
			str_content_hash = hash_artifact(path_csv)
			df_ = read_table(
				path_csv,
				"",
				_DTYPES,
				CAD_CIA_ESTRANG,
				list_date_cols=_DATE_COLS,
				str_csv_sep=";",
				str_encoding="ISO-8859-1",
				int_csv_quoting=csv.QUOTE_NONE,
			)
		self._cls_logger.log_message(
			f"Loaded {len(df_)} Cadastro de Companhias Estrangeiras rows", "info"
		)
		return stamp_provenance(df_, self._str_url, CAD_CIA_ESTRANG, str_content_hash)
