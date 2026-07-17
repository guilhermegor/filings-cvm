"""CVM **META** for the SECURIT DFIN_CRA dataset (`SECURIT/DOC/DFIN_CRA`).

The spec CVM publishes for `dfin_cra_AAAA.csv` — the declared description, type and size of each of
its 9 fields. A flat `.txt`, so the whole document is one section.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_DFIN_CRA
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaDfinCraReader(BaseMetaReader):
	"""Read the META of the CVM SECURIT DFIN_CRA dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/SECURIT/DOC/DFIN_CRA/META/meta_dfin_cra.txt"
	)
	_CONTRACT: ClassVar[FileContract] = META_DFIN_CRA
