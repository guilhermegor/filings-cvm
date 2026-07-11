"""CVM CDA FIF — ingestion (leitura) reader.

Downloads the monthly CVM open-data dump of the *Demonstrativo de Composição e
Diversificação das Aplicações* (``cda_fi_AAAAMM.zip``), consolidates its asset blocks,
and returns them as a typed, contract-validated :class:`pandas.DataFrame`. This is the
*reading* half of the standard; building the CDA file to *send* to CVM lives in the
``submission`` section — and the two touch **different artifacts**: submission produces
the ``DOC_ARQ`` XML, while this reader consumes the flat open-data CSV export.

Shape of the result
-------------------
The archive ships ten CSV members at **two different grains**:

- ``cda_fi_BLC_1`` … ``cda_fi_BLC_8`` — one row *per asset held*
  (fund × date × asset). Each block is a different asset-type layout, so their
  block-specific columns differ; only the four identifying columns are shared.
- ``cda_fi_PL`` — one row *per fund* (fund × date), carrying just ``VL_PATRIM_LIQ``.
- ``cda_fie`` — a distinct FIE layout (its own ``ID_DOC``, inline ``VL_PATRIM_LIQ``,
  exterior-asset columns). **Out of scope here**; it warrants its own reader.

Stacking those grains into one frame would leave ``VL_PATRIM_LIQ`` populated only on PL
rows and every holdings column null beside it — a frame that passes any column contract
yet silently double-counts under ``groupby().sum()``. So the blocks are concatenated
(tagged with a ``BLOCO`` column) and the fund's net worth is **left-joined on** as a
column instead. The result holds one grain — fund × date × asset — and makes the
*diversificação* half of CDA directly computable as
``VL_MERC_POS_FINAL / VL_PATRIM_LIQ``.

Typing
------
Because the blocks are heterogeneous, only the four shared columns are declared: a dtype
map naming a column absent from some block would raise ``KeyError`` in ``apply_dtypes``.
Every other column is left as the exact source text by the tabular seam's text-first read
— which is also what the money and quantity columns want: never coerced to ``float``, so
no precision is lost on the way in. A consumer converts to ``Decimal`` where it computes.

Network, unzip, and CSV parsing are delegated to this library's own ``_internal.utils``
seams (``http_downloader``, ``zip_extractor``, ``tabular_reader``) — never a vendor
framework — so the single I/O boundary is :func:`download_file` and tests mock only there.

Pass ``path_raw`` to keep the downloaded ``.zip`` and its extracted CSVs on disk (a
datalake's bronze layer); omit it and they live in a temporary directory that is discarded.
"""

from __future__ import annotations

from collections.abc import Sequence
import csv
from datetime import date
from pathlib import Path

import pandas as pd

from filings_cvm._internal.config.contracts.cda_fif import CDA_FIF
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.http_downloader import download_file
from filings_cvm._internal.utils.provenance import hash_artifact, stamp_provenance
from filings_cvm._internal.utils.raw_workspace import raw_workspace
from filings_cvm._internal.utils.retry import LogEmitter, RetryPolicy
from filings_cvm._internal.utils.tabular_reader import read_table
from filings_cvm._internal.utils.zip_extractor import extract_all


# CVM open-data monthly dump; ``{ym}`` is the reference month formatted ``AAAAMM``.
_BASE_URL = "https://dados.cvm.gov.br/dados/FI/DOC/CDA/DADOS/cda_fi_{ym}.zip"

# Member-name prefixes inside the archive. ``cda_fie_*`` is deliberately excluded: it is a
# different layout, not a ninth block. Note ``cda_fi_`` is *not* a prefix of ``cda_fie_``,
# so these two tests cannot accidentally capture it.
_PREFIX_BLOCK = "cda_fi_BLC_"
_PREFIX_PL = "cda_fi_PL_"

# The columns every member shares. Declared ``str`` so the identifying keys are never
# inferred (a masked CNPJ must not become a float, a zero-padded code must not become int).
_DTYPES_SHARED: dict[str, str] = {
	"TP_FUNDO_CLASSE": "str",
	"CNPJ_FUNDO_CLASSE": "str",
	"DENOM_SOCIAL": "str",
}
# Kept ``str`` for the same reason the holdings' money columns are: exact CVM decimal text.
_DTYPES_PL: dict[str, str] = {**_DTYPES_SHARED, "VL_PATRIM_LIQ": "str"}

_DATE_COLS: tuple[str, ...] = ("DT_COMPTC",)

# The fund's identity on a reference date — the grain of the PL member, and therefore the
# join key. ``DENOM_SOCIAL`` is excluded: it is a label carried by both sides, not a key.
_JOIN_KEYS: tuple[str, ...] = ("TP_FUNDO_CLASSE", "CNPJ_FUNDO_CLASSE", "DT_COMPTC")

# Name of the synthetic column tagging which asset block a holdings row came from.
_COL_BLOCK = "BLOCO"

# How many unmatched CNPJs to name in the coverage warning before summarising the rest —
# enough to start diagnosing, few enough to keep one log line readable.
_MAX_UNMATCHED_SAMPLE = 5


class CdaReader(IngestionReader):
	"""Read the CVM CDA FIF open-data dump into one typed, single-grain DataFrame.

	Concrete :class:`IngestionReader` for the monthly ``cda_fi`` open-data dump. The
	eight asset blocks are consolidated and the fund's ``VL_PATRIM_LIQ`` joined on, so
	each row is one asset position with its fund's net worth beside it.

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
			and every CSV extracted from it — for a datalake's bronze layer. Created if
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
		"""Download, extract, and consolidate the reference month into a typed DataFrame.

		The ZIP is fetched to a throwaway directory and every member extracted. Each
		``BLC_*`` block is read through the tabular seam — which enforces the
		:data:`CDA_FIF` contract (required columns + a coercible CNPJ column) before
		applying the declared types — tagged with its block name, and concatenated. The
		``PL`` member is then left-joined on to supply each row's ``VL_PATRIM_LIQ``.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 30.

		Returns
		-------
		pd.DataFrame
			One row per asset position (fund × date × asset), with a ``BLOCO`` column
			naming its source block and a ``VL_PATRIM_LIQ`` column carrying the fund's
			net worth on that date. The union of the blocks' columns is present; a
			column that a given block does not define is ``NaN`` on that block's rows.

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ContractError
			If any member violates the :data:`CDA_FIF` contract.
		ValueError
			If the archive holds no ``BLC_*`` block or no ``PL`` member.
		pandas.errors.MergeError
			If the ``PL`` member does not have one row per fund per date.
		"""
		self._cls_logger.log_message(f"Downloading CDA FIF from {self._str_url}", "info")
		with raw_workspace(self._path_raw) as path_dir:
			str_zip = f"cda_fi_{self._date_ref.strftime('%Y%m')}.zip"
			path_zip = download_file(
				self._str_url, path_dir / str_zip, int_timeout_s, retry_policy=self._retry_policy
			)
			str_content_hash = hash_artifact(path_zip)
			list_members = sorted(extract_all(path_zip, path_dir))
			df_holdings = self._read_blocks(list_members)
			df_pl = self._read_pl(list_members)

		# The validate keyword makes pandas itself assert the PL grain. A duplicated
		# fund/date there would fan out holdings rows and inflate every downstream sum.
		df_ = df_holdings.merge(df_pl, on=list(_JOIN_KEYS), how="left", validate="many_to_one")
		self._check_pl_coverage(df_)

		self._cls_logger.log_message(
			f"Loaded {len(df_)} asset positions from CDA FIF "
			f"across {df_[_COL_BLOCK].nunique()} blocks",
			"info",
		)
		return stamp_provenance(df_, self._str_url, CDA_FIF, str_content_hash)

	def _check_pl_coverage(self, df_merged: pd.DataFrame) -> None:
		"""Warn about holdings rows that matched no ``PL`` row, naming the funds.

		A holdings row whose fund is absent from the ``PL`` member emerges from the join
		with a null ``VL_PATRIM_LIQ``. Nothing downstream would complain — the frame is
		still contract-valid and correctly typed — but every ``VL_MERC_POS_FINAL /
		VL_PATRIM_LIQ`` a consumer computes for that fund silently yields ``NaN``, and any
		"share of net worth" aggregate quietly under-reports.

		The reader **warns rather than raises**: one fund missing from ``PL`` should not
		cost the caller the month's other ~25k good rows. The consumer keeps the frame and
		decides — drop the affected funds, or accept the nulls. Empirically the join was
		total for 2025-04 (all 25,281 holdings keys matched), so any warning here means the
		dump is malformed or CVM changed the layout, and the message names the CNPJs so a
		log-sniffing routine can open an issue against concrete funds.

		Parameters
		----------
		df_merged : pd.DataFrame
			The holdings frame after the ``PL`` left-join.
		"""
		sr_unmatched = df_merged["VL_PATRIM_LIQ"].isna()
		int_rows = int(sr_unmatched.sum())
		if int_rows == 0:
			return

		list_cnpjs = sorted(set(df_merged.loc[sr_unmatched, "CNPJ_FUNDO_CLASSE"]))
		str_sample = ", ".join(list_cnpjs[:_MAX_UNMATCHED_SAMPLE])
		int_hidden = len(list_cnpjs) - _MAX_UNMATCHED_SAMPLE
		str_more = f" (+{int_hidden} more)" if int_hidden > 0 else ""
		self._cls_logger.log_message(
			f"{int_rows} CDA holdings row(s) across {len(list_cnpjs)} fund(s) matched no PL "
			f"row: {str_sample}{str_more}. VL_PATRIM_LIQ is null for them, so any ratio "
			"against net worth will be NaN.",
			"warning",
		)

	@staticmethod
	def _read_blocks(list_members: Sequence[Path]) -> pd.DataFrame:
		"""Read every ``BLC_*`` block, tag each with its name, and concatenate them.

		Parameters
		----------
		list_members : sequence of pathlib.Path
			The archive's extracted members.

		Returns
		-------
		pd.DataFrame
			The blocks stacked, with a ``BLOCO`` column. ``sort=False`` keeps the union
			of columns in first-seen order rather than alphabetising them.

		Raises
		------
		ValueError
			If the archive contains no ``BLC_*`` member.
		"""
		list_frames: list[pd.DataFrame] = []
		for path_member in list_members:
			if not path_member.name.startswith(_PREFIX_BLOCK):
				continue
			df_block = read_table(
				path_member,
				"",
				_DTYPES_SHARED,
				CDA_FIF,
				list_date_cols=_DATE_COLS,
				str_csv_sep=";",
				str_encoding="ISO-8859-1",
				int_csv_quoting=csv.QUOTE_NONE,
			)
			# "cda_fi_BLC_1_202504" -> "BLC_1"; the layout that produced these columns.
			list_parts = path_member.stem.split("_")
			df_block[_COL_BLOCK] = f"{list_parts[2]}_{list_parts[3]}"
			list_frames.append(df_block)

		if not list_frames:
			raise ValueError("No CDA BLC_* block found in the archive")
		return pd.concat(list_frames, ignore_index=True, sort=False)

	@staticmethod
	def _read_pl(list_members: Sequence[Path]) -> pd.DataFrame:
		"""Read the ``PL`` member, returning just the join keys and ``VL_PATRIM_LIQ``.

		``DENOM_SOCIAL`` is dropped: the holdings blocks already carry it, and keeping it
		on both sides of the merge would collide into ``DENOM_SOCIAL_x``/``_y``.

		Parameters
		----------
		list_members : sequence of pathlib.Path
			The archive's extracted members.

		Returns
		-------
		pd.DataFrame
			One row per fund per date, with the fund's net worth as exact source text.

		Raises
		------
		ValueError
			If the archive contains no ``PL`` member.
		"""
		for path_member in list_members:
			if not path_member.name.startswith(_PREFIX_PL):
				continue
			df_pl = read_table(
				path_member,
				"",
				_DTYPES_PL,
				CDA_FIF,
				list_date_cols=_DATE_COLS,
				str_csv_sep=";",
				str_encoding="ISO-8859-1",
				int_csv_quoting=csv.QUOTE_NONE,
			)
			return df_pl[[*_JOIN_KEYS, "VL_PATRIM_LIQ"]]
		raise ValueError("No CDA PL member found in the archive")
