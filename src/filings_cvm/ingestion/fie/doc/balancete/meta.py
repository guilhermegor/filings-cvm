"""CVM **META** for the FIE Balancete dataset (`FIE/DOC/BALANCETE`).

The spec CVM publishes for `balancete_fie_AAAAMM.zip` — the declared description, type and size
of each field. A flat `.txt`, so the whole document is one section.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_BALANCETE_FIE
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaBalanceteFieReader(BaseMetaReader):
	"""Read the META of the CVM FIE Balancete dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/FIE/DOC/BALANCETE/META/meta_balancete_fie.txt"
	)
	_CONTRACT: ClassVar[FileContract] = META_BALANCETE_FIE
