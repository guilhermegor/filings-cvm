"""CVM **META** for the FII DFIN dataset (`FII/DOC/DFIN`).

The spec CVM publishes for `dfin_fii_AAAA.csv` — the declared description, type and size of each
field. A flat `.txt`, so the whole document is one section.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_DFIN_FII
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaDfinFiiReader(BaseMetaReader):
	"""Read the META of the CVM FII DFIN dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = "https://dados.cvm.gov.br/dados/FII/DOC/DFIN/META/meta_dfin_fii.txt"
	_CONTRACT: ClassVar[FileContract] = META_DFIN_FII
