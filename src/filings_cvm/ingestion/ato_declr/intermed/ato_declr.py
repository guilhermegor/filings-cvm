"""CVM Atos Declaratórios — ingestion (leitura) reader.

Downloads the CVM open-data list of declaratory acts that suspend irregular securities
intermediation (``ato_declr.csv``, dataset ``ATO_DECLR/INTERMED``) and returns it as a typed,
contract-validated :class:`pandas.DataFrame`. Inaugurates the ``ato_declr/`` portal root.

A bare CSV at a **fixed URL** that CVM overwrites in place — hence there is **no** ``date_ref``,
and a ``path_raw`` snapshot is the only record of what the list said the day it was fetched.

``Data_Ato_Declaratorio`` and ``Data_Publicacao_DOU`` are coerced to pure ``date``; every other
column is exact source text. ``CNPJ_CPF`` mixes CNPJs, CPFs and blanks and is returned as
published; ``Link_Download`` is text and is never followed.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import ClassVar

import pandas as pd

from filings_cvm._internal.config.contracts.ato_declr import ATO_DECLR
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.http_downloader import download_file
from filings_cvm._internal.utils.provenance import hash_artifact, stamp_provenance
from filings_cvm._internal.utils.raw_workspace import raw_workspace
from filings_cvm._internal.utils.retry import LogEmitter, RetryPolicy
from filings_cvm._internal.utils.tabular_reader import read_table


# CVM open-data snapshot. Fixed URL: CVM overwrites this file in place.
_URL = "https://dados.cvm.gov.br/dados/ATO_DECLR/INTERMED/DADOS/ato_declr.csv"

_FILENAME = "ato_declr.csv"

# Coerced to pure ``date`` objects (ISO ``AAAA-MM-DD``, never blank in the measured file).
_DATE_COLS: tuple[str, ...] = ("Data_Ato_Declaratorio", "Data_Publicacao_DOU")

# Every non-date column is exact source text, derived from the contract so they cannot drift.
_DTYPES: dict[str, str] = {
	str_col: "str" for str_col in ATO_DECLR.tuple_required if str_col not in _DATE_COLS
}

# Reader-owned default retry/backoff: 5 attempts on a capped exponential schedule (~2, 4, 8, 10 s).
_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class AtoDeclrReader(IngestionReader):
	"""Read the CVM Atos Declaratórios list into a typed DataFrame.

	Concrete :class:`IngestionReader` for ``ato_declr.csv``. Takes no reference date: the
	artifact is a current-state snapshot, not a partitioned dump.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the list into a validated DataFrame.
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
			Directory in which to **persist** the raw ``ato_declr.csv`` for a datalake's bronze
			layer. Created if absent. When ``None`` (the default) the artifact is fetched into a
			temporary directory and discarded. CVM overwrites the file in place, so a persisted
			copy is the only record of the list on the day it was fetched.
		retry_policy : RetryPolicy, optional
			Retry/backoff schedule forwarded to the download seam. When ``None`` (the default) this
			reader's own :attr:`_RETRY_POLICY` is used.
		cls_logger : LogEmitter, optional
			Injected log sink (``log_message(message, level)``). Defaults to a stdlib-backed
			:class:`LogEmitter`.
		"""
		self._path_raw = path_raw
		self._retry_policy = retry_policy if retry_policy is not None else self._RETRY_POLICY
		self._cls_logger = cls_logger if cls_logger is not None else LogEmitter()
		self._str_url = _URL

	def read(self, int_timeout_s: int = 60) -> pd.DataFrame:
		"""Download and parse the list into a typed DataFrame.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60.

		Returns
		-------
		pd.DataFrame
			One row per declaratory act and listed party, 7 source columns plus provenance.

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ContractError
			If the CSV violates the :data:`ATO_DECLR` contract.
		"""
		self._cls_logger.log_message(
			f"Downloading Atos Declaratórios from {self._str_url}", "info"
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
				ATO_DECLR,
				list_date_cols=_DATE_COLS,
				str_csv_sep=";",
				str_encoding="ISO-8859-1",
				int_csv_quoting=csv.QUOTE_NONE,
			)
		self._cls_logger.log_message(f"Loaded {len(df_)} Atos Declaratórios rows", "info")
		return stamp_provenance(df_, self._str_url, ATO_DECLR, str_content_hash)
