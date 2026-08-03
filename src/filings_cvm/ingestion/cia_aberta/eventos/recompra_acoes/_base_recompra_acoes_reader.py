"""Shared base for the CVM CIA_ABERTA/EVENTOS/RECOMPRA_ACOES (share buy-back) ingestion readers.

`cia_aberta_recompra_acoes.zip` ships **three members** — `cia_aberta_recompra_acoes.csv` (the
buy-back programme), `..._intermediarios.csv` (the brokers engaged in it) and `..._quantidades.csv`
(the counts per share type and class). It is a **registry plus two satellites**, all joined by
`ID_Programa`, so they differ only in their columns and the download → unzip → select-member → read
logic lives here once.

⚠️⚠️ **This dataset does not follow its `DOC` neighbours, in four measured ways.**

1. It is a **snapshot**: the URL carries no year, so the readers take **no `date_ref`** — unlike
   all seven `CIA_ABERTA/DOC` datasets, which are `<ds>_cia_aberta_AAAA.zip`. One file holds the
   series from **1997** onward, and CVM overwrites it in place, so a persisted `path_raw` is the
   only record of what it said on a given day.
2. ⚠️ **The filename is inverted** — `cia_aberta_recompra_acoes.zip` puts the *root* first, where
   `dfp_cia_aberta_AAAA.zip` puts the *dataset* first. Deriving the name from the `DOC` pattern
   would miss.
3. ⚠️ Its columns are **CamelCase** (`CNPJ_Companhia`, `Data_Deliberacao`), like CGVN — **not** the
   `CNPJ_CIA` / `DT_REFER` of DFP, ITR, FCA and the FRE index. There is no root-wide convention,
   only per-dataset measurement.
4. ⚠️ **Two of the three members carry no date column at all** (`_DATE_COLS = ()`), the ADM_CART
   shape, and `quantidades` additionally has **no CNPJ column** — its `tuple_cnpj_cols` is empty
   because the source has none, not because one was overlooked.

The shared `read` already handles both: its dtype map is derived from `_CONTRACT` minus
`_DATE_COLS`, which degrades to "everything is text" without a special case.

This is a **private** base (leading underscore, its own file): consumers import the concrete
`RecompraAcoes*Reader` adapters, never this class. Each sets four class attributes — the member
filename, its `FileContract`, its date columns and a log label — and inherits the rest. All three
download the *same* archive, so a `path_raw` written by one serves the others. **No grain is
asserted.**
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import ClassVar

import pandas as pd

from filings_cvm._internal.config.contracts import FileContract
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.http_downloader import download_file
from filings_cvm._internal.utils.provenance import hash_artifact, stamp_provenance
from filings_cvm._internal.utils.raw_workspace import raw_workspace
from filings_cvm._internal.utils.retry import LogEmitter, RetryPolicy
from filings_cvm._internal.utils.tabular_reader import read_table
from filings_cvm._internal.utils.zip_extractor import extract_all, find_member


# CVM open-data recompra_acoes-platform-registry snapshot ZIP, shared by all three readers. Fixed
# URL: CVM overwrites this file in place.
_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/EVENTOS/RECOMPRA_ACOES/DADOS/cia_aberta_recompra_acoes.zip"

_ZIP_FILENAME = "cia_aberta_recompra_acoes.zip"

# Reader-owned default retry/backoff (CVM's open-data portal throttles under load): 5 attempts on
# a capped exponential schedule (~2, 4, 8, 10 s). All readers inherit it via ``_RETRY_POLICY``; a
# per-instance ``retry_policy=`` still overrides.
_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class _BaseRecompraAcoesReader(IngestionReader):
	"""Private base for the three CIA_ABERTA/EVENTOS/RECOMPRA_ACOES registry readers.

	A concrete reader sets :attr:`_MEMBER`, :attr:`_CONTRACT`, :attr:`_DATE_COLS` and
	:attr:`_LABEL`; everything else — the shared download/unzip/parse — lives here.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse this reader's registry member into a validated DataFrame.
	"""

	# Set by each concrete subclass. Declared here so the shared ``read`` can reference them.
	_MEMBER: ClassVar[str]
	_CONTRACT: ClassVar[FileContract]
	_DATE_COLS: ClassVar[tuple[str, ...]]
	_LABEL: ClassVar[str]

	# Per-reader default retry and backoff schedule. All readers share one archive, so they
	# inherit this default; a subclass may still assign its own, and a retry_policy passed to the
	# constructor overrides it for that instance.
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
			Directory in which to **persist** the raw ``cia_aberta_recompra_acoes.zip`` and every
			CSV extracted from it — not just the member read — for a bronze layer. Created if
			absent. When ``None`` (the default) the artifact is fetched into a temporary directory
			and discarded. CVM overwrites the file in place, so a persisted snapshot is the only
			record of what the registry said that day.
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
		"""Download, extract, and parse this reader's registry member into a typed DataFrame.

		The ZIP is fetched to a throwaway directory (or ``path_raw``) and every member extracted;
		this reader's member is read through the tabular seam, which enforces its
		:class:`FileContract` before applying the declared types. The ``DT_*`` columns become pure
		``date`` objects — the two satellites declare none, so all of their columns stay text —
		and every other column is exact source text, including ``CEP``, ``TEL`` and ``DDD``, which
		the CVM META declares ``numeric`` but which are identifiers, not quantities.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60.

		Returns
		-------
		pd.DataFrame
			The registry member — one row per registered platform (or administrator/partner).
			**No grain is asserted.**

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ContractError
			If the CSV violates this reader's contract.
		ValueError
			If the archive holds no member named :attr:`_MEMBER`.
		"""
		self._cls_logger.log_message(
			f"Downloading RECOMPRA_ACOES ({self._LABEL}) from {self._str_url}",
			"info",
		)
		dict_dtypes = {
			str_col: "str"
			for str_col in self._CONTRACT.tuple_required
			if str_col not in self._DATE_COLS
		}
		with raw_workspace(self._path_raw) as path_dir:
			path_zip = download_file(
				self._str_url,
				path_dir / _ZIP_FILENAME,
				int_timeout_s,
				retry_policy=self._retry_policy,
			)
			str_content_hash = hash_artifact(path_zip)
			path_csv = find_member(extract_all(path_zip, path_dir), self._MEMBER)
			df_ = read_table(
				path_csv,
				"",
				dict_dtypes,
				self._CONTRACT,
				list_date_cols=self._DATE_COLS,
				str_csv_sep=";",
				str_encoding="ISO-8859-1",
				int_csv_quoting=csv.QUOTE_NONE,
			)
		self._cls_logger.log_message(
			f"Loaded {len(df_)} {self._LABEL} rows from CIA_ABERTA/EVENTOS/RECOMPRA_ACOES", "info"
		)
		return stamp_provenance(df_, self._str_url, self._CONTRACT, str_content_hash)
