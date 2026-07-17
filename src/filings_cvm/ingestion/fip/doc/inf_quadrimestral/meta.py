"""CVM **META** for the FIP Informe Quadrimestral dataset (`FIP/DOC/INF_QUADRIMESTRAL`).

The spec CVM publishes for `inf_quadrimestral_fip_AAAA.csv` (post-RCVM 175) — the declared
description, type and size of each field. A flat `.txt`, so the whole document is one section.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_INF_QUADRIMESTRAL_FIP
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaInfQuadrimestralFipReader(BaseMetaReader):
	"""Read the META of the CVM FIP Informe Quadrimestral dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/FIP/DOC/INF_QUADRIMESTRAL/META/meta_inf_quadrimestral_fip.txt"
	)
	_CONTRACT: ClassVar[FileContract] = META_INF_QUADRIMESTRAL_FIP
