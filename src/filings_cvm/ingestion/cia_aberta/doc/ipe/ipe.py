"""CVM IPE CIA_ABERTA — ingestion (leitura) reader.

Downloads the CVM open-data **index of periodic and occasional filings** of listed companies
(*Informações Periódicas e Eventuais*) — ``ipe_cia_aberta_AAAA.zip`` (dataset
``CIA_ABERTA/DOC/IPE``) — and returns its single CSV member as a typed, contract-validated
:class:`pandas.DataFrame`. One row per document a company filed with CVM in the year.

**This is an index, not a document.** Each row describes one filing — the company's identity, the
reference and delivery dates, the document's taxonomy (``Categoria`` / ``Tipo`` / ``Especie`` /
``Assunto``), its delivery protocol and version, and a ``Link_Download`` pointing at the actual
document on CVM's RAD portal. The reader **returns the link as text and does not follow it**:
fetching the linked document is a downstream concern, and the reader stays thin (the same
principle as every other reader here — parse the artifact CVM publishes, nothing more).

Three shape notes, all reflected below:

- The dump is **partitioned by year** — ``ipe_cia_aberta_2025.zip`` — so this reader's
  ``date_ref`` selects the *year* (only ``date_ref.year`` is read).
- It is a **single-member ZIP**: the archive is fetched, every member extracted, and
  ``ipe_cia_aberta_AAAA.csv`` selected by exact name before parsing. Unlike DFIN (a loose CSV),
  and unlike the sibling ``CAD`` snapshot, which has no year at all.
- ⚠️ ``CNPJ_Companhia`` legitimately carries the placeholder ``00.000.000/0000-00`` for foreign
  issuers with no Brazilian CNPJ (44 of 49,277 rows in 2025; **zero** malformed). It is returned
  **exactly as published** — never repaired — and the contract still lists it as a CNPJ column,
  because that check requires *at least one* valid CNPJ, not all of them.

``Data_Referencia`` and ``Data_Entrega`` are coerced to pure ``date``; every other column —
including ``Codigo_CVM``, ``Versao`` and ``Link_Download`` — is exact source text. ``Codigo_CVM``
is ``Domínio: Numérico`` in the META but stays ``str`` (it is an identifier, not a quantity), and
``Versao`` is ``smallint`` there but likewise stays text, matching ``DfinFiiReader``.

Network and CSV parsing are delegated to this library's own ``_internal.utils`` seams
(``http_downloader``, ``zip_extractor``, ``tabular_reader``) — never a vendor framework — so the
single I/O boundary is :func:`download_file` and tests mock only there.

Pass ``path_raw`` to keep the raw ``.zip`` (and its extracted CSV) on disk for a datalake's bronze
layer; omit it and the artifact lives in a temporary directory that is discarded.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import ClassVar

import pandas as pd

from filings_cvm._internal.config.contracts.ipe_cia_aberta import IPE_CIA_ABERTA
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.http_downloader import download_file
from filings_cvm._internal.utils.provenance import hash_artifact, stamp_provenance
from filings_cvm._internal.utils.raw_workspace import raw_workspace
from filings_cvm._internal.utils.retry import LogEmitter, RetryPolicy
from filings_cvm._internal.utils.tabular_reader import read_table
from filings_cvm._internal.utils.zip_extractor import extract_all, find_member


# CVM open-data **yearly** dump; ``{yyyy}`` is the reference year. A ZIP of one CSV member.
_BASE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_{yyyy}.zip"

# The two ISO date columns, both declared ``date`` by the META and 100% ``AAAA-MM-DD`` in the real
# file; coerced to pure ``date``. Everything else — including ``Link_Download``, ``Codigo_CVM`` and
# ``Versao`` — is exact source text.
_DATE_COLS: tuple[str, ...] = ("Data_Referencia", "Data_Entrega")

# Every non-date column is exact source text. Derived from the contract so a column added there
# cannot be silently left untyped, and the two lists cannot drift. ``apply_dtypes`` requires the
# dtype and date sets to be disjoint, which this comprehension guarantees.
_DTYPES: dict[str, str] = {
	str_col: "str" for str_col in IPE_CIA_ABERTA.tuple_required if str_col not in _DATE_COLS
}

# Reader-owned default retry/backoff (CVM's open-data portal throttles under load): 5 attempts on a
# capped exponential schedule (~2, 4, 8, 10 s). Per-reader tunable via ``_RETRY_POLICY``; a
# per-instance ``retry_policy=`` still overrides.
_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class IpeCiaAbertaReader(IngestionReader):
	"""Read the CVM IPE CIA_ABERTA yearly open-data dump into a typed DataFrame.

	Concrete :class:`IngestionReader` for the yearly ``ipe_cia_aberta`` ZIP — the index of the
	periodic and occasional documents listed companies filed with CVM, one row per filing.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's IPE index into a validated DataFrame.
	"""

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
			Any day within the reference **year** — only its year selects the yearly dump.
			Defaults to today. The current year's file is published incrementally, so pass a past
			year for a complete series.
		path_raw : pathlib.Path, optional
			Directory in which to **persist** the raw ``ipe_cia_aberta_AAAA.zip`` and the CSV
			extracted from it, for a datalake's bronze layer. Created if absent. When ``None`` (the
			default) the artifact is fetched into a temporary directory and discarded.
		retry_policy : RetryPolicy, optional
			Retry/backoff schedule forwarded to the download seam. When ``None`` (the default) this
			reader's own :attr:`_RETRY_POLICY` class attribute is used. Pass a :class:`RetryPolicy`
			to override it for this one instance.
		cls_logger : LogEmitter, optional
			Injected log sink (``log_message(message, level)``). Defaults to a stdlib-backed
			:class:`LogEmitter`, so no logging import is forced on consumers.
		"""
		self._date_ref = date_ref or date.today()
		self._path_raw = path_raw
		self._retry_policy = retry_policy if retry_policy is not None else self._RETRY_POLICY
		self._cls_logger = cls_logger if cls_logger is not None else LogEmitter()
		self._str_url = _BASE_URL.format(yyyy=self._date_ref.year)

	def read(self, int_timeout_s: int = 60) -> pd.DataFrame:
		"""Download, extract, and parse the reference year's IPE index into a typed DataFrame.

		The yearly ZIP is fetched to a throwaway directory (or ``path_raw``), every member
		extracted, and ``ipe_cia_aberta_AAAA.csv`` selected by exact name and read through the
		tabular seam, which enforces the :data:`IPE_CIA_ABERTA` contract (all 13 columns, with a
		coercible ``CNPJ_Companhia``) before applying the declared types. ``Data_Referencia`` and
		``Data_Entrega`` become pure ``date``; every other column is exact source text.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60.

		Returns
		-------
		pd.DataFrame
			One row per document filed in the reference year. **No unique key is asserted** by the
			reader, though the natural grain is company × protocol × version.

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ContractError
			If the CSV violates the :data:`IPE_CIA_ABERTA` contract.
		ValueError
			If the archive holds no ``ipe_cia_aberta_AAAA.csv`` for the reference year.
		"""
		int_year = self._date_ref.year
		self._cls_logger.log_message(f"Downloading IPE CIA_ABERTA from {self._str_url}", "info")
		with raw_workspace(self._path_raw) as path_dir:
			path_zip = download_file(
				self._str_url,
				path_dir / f"ipe_cia_aberta_{int_year}.zip",
				int_timeout_s,
				retry_policy=self._retry_policy,
			)
			str_content_hash = hash_artifact(path_zip)
			path_csv = find_member(
				extract_all(path_zip, path_dir), f"ipe_cia_aberta_{int_year}.csv"
			)
			df_ = read_table(
				path_csv,
				"",
				_DTYPES,
				IPE_CIA_ABERTA,
				list_date_cols=_DATE_COLS,
				str_csv_sep=";",
				str_encoding="ISO-8859-1",
				int_csv_quoting=csv.QUOTE_NONE,
			)
		self._cls_logger.log_message(
			f"Loaded {len(df_)} IPE CIA_ABERTA rows from {int_year}", "info"
		)
		return stamp_provenance(df_, self._str_url, IPE_CIA_ABERTA, str_content_hash)
