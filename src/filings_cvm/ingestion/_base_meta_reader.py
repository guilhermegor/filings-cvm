"""Private base for the CVM **META** readers — one per dataset.

Every dataset's META is fetched the same way and differs only in its URL, so the machinery lives
here once and each dataset's ``meta.py`` declares two constants. This mirrors the reader bases
(``_base_inf_mensal_cra_reader.py`` + thin subclasses), but sits at the ``ingestion/`` root because
it is shared across every portal root rather than scoped to one dataset package.

**Why the URL is a per-dataset constant and never derived.** The META filename is not a function of
the dataset path: ``meta_inf_mensal_cri.zip`` but ``meta_cda_fi_txt.zip`` (a ``_txt`` infix), and
``FIE/MEDIDAS`` publishes both ``.csv`` and ``.txt``. Worse, **``meta_cad_fi.txt`` and
``meta_cad_fi.zip`` are different datasets** — the ``.txt`` is ``cad_fi`` (41 fields), the ``.zip``
is ``cad_fi_hist`` (19 members). Any "derive the name" or "prefer the zip" rule would hand a caller
the wrong dataset's metadata **with every test still green**, which is precisely the failure #96
caught in the contracts themselves.

There is **no `date_ref`**: a META sits at a fixed URL that CVM overwrites in place, so a persisted
``path_raw`` snapshot is the only record of what the spec said that day (the ``CadastroFiReader``
precedent).
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar
import zipfile

import pandas as pd

from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.http_downloader import download_file
from filings_cvm._internal.utils.meta_parser import parse_meta_blocks
from filings_cvm._internal.utils.provenance import hash_artifact, stamp_provenance
from filings_cvm._internal.utils.raw_workspace import raw_workspace
from filings_cvm._internal.utils.retry import LogEmitter, RetryPolicy
from filings_cvm._internal.utils.tabular_reader import FileContract


# CVM encodes every META in ISO-8859-1 (Latin-1), like the data dumps.
_ENCODING = "ISO-8859-1"

# Shared default: the open-data portal throttles under load. 5 attempts on a capped exponential
# schedule (~2, 4, 8, 10 s). A subclass may override `_RETRY_POLICY`; a per-instance
# `retry_policy=` still wins.
_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class BaseMetaReader(IngestionReader):
	"""Download one dataset's META and return it as a typed, provenance-stamped DataFrame.

	Subclasses declare :attr:`_META_URL` and :attr:`_CONTRACT` and nothing else.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame.
	"""

	# Declared by every subclass.
	_META_URL: ClassVar[str]
	_CONTRACT: ClassVar[FileContract]
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY

	# The stem CVM repeats on every member of this dataset's META zip, stripped to leave the bare
	# section — a worked example lives on the parsing method below. Declared, never derived — the
	# stems are irregular from one dataset to the next, so a member's own name does not predict
	# them. Empty for a flat text file, which has no members.
	_MEMBER_STEM: ClassVar[str] = ""

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
			Directory in which to **persist** the raw META artifact for a datalake's bronze layer.
			Created if absent. When ``None`` (the default) it is fetched into a temporary directory
			and discarded. CVM overwrites the META in place, so a persisted copy is the **only**
			record of what the spec said on a given day.
		retry_policy : RetryPolicy, optional
			Retry/backoff schedule forwarded to the download seam. When ``None`` (the default) this
			class's :attr:`_RETRY_POLICY` is used.
		cls_logger : LogEmitter, optional
			Injected log sink (``log_message(message, level)``). Defaults to a stdlib-backed
			:class:`LogEmitter`, so no logging import is forced on consumers.
		"""
		self._path_raw = path_raw
		self._retry_policy = retry_policy if retry_policy is not None else self._RETRY_POLICY
		self._cls_logger = cls_logger if cls_logger is not None else LogEmitter()
		self._str_url = self._META_URL

	def read(self, int_timeout_s: int = 60) -> pd.DataFrame:
		"""Download and parse this dataset's META.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60.

		Returns
		-------
		pd.DataFrame
			One row per declared field, columns :attr:`FileContract.output_columns`. A multi-member
			META ZIP is returned as **one long frame**, each member's name in ``section``; a flat
			``.txt`` uses the dataset's source key (minus the ``meta_`` prefix) as its section.
			**Field names are verbatim CVM**, including the 50-char truncation.

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		ValueError
			If the download seam rejects :attr:`_META_URL` (bad scheme, internal host). Not
			reachable in practice — the URL is a per-subclass constant, not caller input.
		UnicodeDecodeError
			If the artifact is not decodable as ISO-8859-1, i.e. CVM changed the encoding.
		"""
		str_filename = self._str_url.rsplit("/", 1)[-1]
		self._cls_logger.log_message(f"Downloading META from {self._str_url}", "info")
		with raw_workspace(self._path_raw) as path_dir:
			path_meta = download_file(
				self._str_url,
				path_dir / str_filename,
				int_timeout_s,
				retry_policy=self._retry_policy,
			)
			str_content_hash = hash_artifact(path_meta)
			list_records = self._parse_artifact(path_meta)
		df_ = pd.DataFrame(list_records, columns=list(self._CONTRACT.tuple_required)).astype(
			"string"
		)
		self._cls_logger.log_message(
			f"Loaded {len(df_)} META field rows from {str_filename}", "info"
		)
		return stamp_provenance(df_, self._str_url, self._CONTRACT, str_content_hash)

	def _parse_artifact(self, path_meta: Path) -> list[dict[str, str]]:
		"""Parse the downloaded artifact — a member-per-section ZIP or a single flat text.

		Parameters
		----------
		path_meta : pathlib.Path
			The downloaded META file.

		Returns
		-------
		list of dict of (str, str)
			The parsed records of every member, concatenated in member order.
		"""
		if path_meta.suffix.lower() != ".zip":
			str_section = self._CONTRACT.str_source_key.removeprefix("meta_")
			return parse_meta_blocks(path_meta.read_bytes().decode(_ENCODING), str_section)
		list_records: list[dict[str, str]] = []
		with zipfile.ZipFile(path_meta) as cls_zip:
			for str_member in sorted(cls_zip.namelist()):
				list_records += parse_meta_blocks(
					cls_zip.read(str_member).decode(_ENCODING),
					self._section_of(str_member),
				)
		return list_records

	def _section_of(self, str_member: str) -> str:
		"""Turn a META ZIP member's filename into its section label.

		``meta_inf_mensal_cra_fluxo_caixa.txt`` → ``fluxo_caixa``. The dataset stem CVM repeats on
		every member is declared by the subclass (:attr:`_MEMBER_STEM`) rather than derived from
		the filename: the stems are irregular — ``meta_cad_fi.zip``'s members are
		``meta_cad_fi_hist_*`` (a different dataset from ``meta_cad_fi.txt``), so the archive's
		name does not predict them.

		Parameters
		----------
		str_member : str
			The ZIP member's name.

		Returns
		-------
		str
			The section label, or the whole stem when it does not carry the expected prefix (a
			member CVM names unexpectedly is labelled by its stem rather than dropped).
		"""
		str_stem = Path(str_member).stem.removeprefix("meta_")
		if self._MEMBER_STEM and str_stem.startswith(f"{self._MEMBER_STEM}_"):
			return str_stem.removeprefix(f"{self._MEMBER_STEM}_")
		return str_stem
