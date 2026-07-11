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
from typing import ClassVar

import pandas as pd

from filings_cvm._internal.config.contracts.lamina_carteira_fif import LAMINA_CARTEIRA_FIF
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.http_downloader import download_file
from filings_cvm._internal.utils.provenance import hash_artifact, stamp_provenance
from filings_cvm._internal.utils.raw_workspace import raw_workspace
from filings_cvm._internal.utils.retry import LogEmitter, RetryPolicy
from filings_cvm._internal.utils.tabular_reader import read_table
from filings_cvm._internal.utils.zip_extractor import extract_all, find_member


# CVM open-data monthly dump; ``{ym}`` is the reference month formatted ``AAAAMM``.
_BASE_URL = "https://dados.cvm.gov.br/dados/FI/DOC/LAMINA/DADOS/lamina_fi_{ym}.zip"

# The member to read, named exactly. The archive also holds ``lamina_fi_AAAAMM.csv`` and two
# ``lamina_fi_rentab_*`` series, so a prefix match would be ambiguous — see ``find_member``.
_MEMBER_CARTEIRA = "lamina_fi_carteira_{ym}.csv"

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


# Reader-owned default retry/backoff (CVM's open-data portal throttles under load): 5 attempts on
# a capped exponential schedule (~2, 4, 8, 10 s). Per-reader tunable via ``_RETRY_POLICY``; a
# per-instance ``retry_policy=`` still overrides.
_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class LaminaCarteiraReader(IngestionReader):
	"""Read the CVM Lâmina carteira FIF open-data CSV into a typed DataFrame.

	Concrete :class:`IngestionReader` for the ``lamina_fi_carteira`` member of the monthly
	Lâmina dump: one row per fund per asset type, with that type's share of net worth.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference month into a validated DataFrame.
	"""

	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY

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
			and every CSV extracted from it, not just the member read — for a datalake's
			bronze layer. Created if absent. When ``None`` (the default) the artifact is
			fetched into a temporary directory and discarded, so the read leaves nothing
			on disk.
		retry_policy : RetryPolicy, optional
			Retry/backoff schedule forwarded to the download seam. When ``None``
			(the default) this reader's own :attr:`_RETRY_POLICY` class attribute
			is used. Pass a :class:`RetryPolicy` to override it for this one
			instance.
		cls_logger : LogEmitter, optional
			Injected log sink (``log_message(message, level)``). Defaults to a stdlib
			-backed :class:`LogEmitter`, so no logging import is forced on consumers.
		"""
		self._date_ref = date_ref or date.today()
		self._path_raw = path_raw
		self._retry_policy = retry_policy if retry_policy is not None else self._RETRY_POLICY
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
			If the archive holds no ``lamina_fi_carteira_AAAAMM.csv`` member.
		"""
		self._cls_logger.log_message(
			f"Downloading Lâmina carteira FIF from {self._str_url}", "info"
		)
		str_ym = self._date_ref.strftime("%Y%m")
		with raw_workspace(self._path_raw) as path_dir:
			path_zip = download_file(
				self._str_url,
				path_dir / f"lamina_fi_{str_ym}.zip",
				int_timeout_s,
				retry_policy=self._retry_policy,
			)
			str_content_hash = hash_artifact(path_zip)
			list_members = extract_all(path_zip, path_dir)
			path_csv = find_member(list_members, _MEMBER_CARTEIRA.format(ym=str_ym))
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
		return stamp_provenance(df_, self._str_url, LAMINA_CARTEIRA_FIF, str_content_hash)
