"""CVM **META** for the FIP Informe Trimestral dataset (`FIP/DOC/INF_TRIMESTRAL`).

The spec CVM publishes for `inf_trimestral_fip_AAAA.csv` (pre-RCVM 175) — the declared
description, type and size of each field. A flat `.txt`, so the whole document is one section.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_INF_TRIMESTRAL_FIP
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaInfTrimestralFipReader(BaseMetaReader):
	"""Read the META of the CVM FIP Informe Trimestral dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/FIP/DOC/INF_TRIMESTRAL/META/meta_inf_trimestral_fip.txt"
	)
	_CONTRACT: ClassVar[FileContract] = META_INF_TRIMESTRAL_FIP
