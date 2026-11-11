"""CVM **META** for the FIE Balanço dataset (`FIE/DOC/BALANCO`).

The spec CVM publishes for `balanco_fie_AAAA.zip` (discontinued in 2020) — the declared
description, type and size of each field. A flat `.txt`, so the whole document is one section.
"""

from __future__ import annotations

from typing import ClassVar

from opendata_cvm._internal.config.contracts.meta import META_BALANCO_FIE
from opendata_cvm._internal.utils.tabular_reader import FileContract
from opendata_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaBalancoFieReader(BaseMetaReader):
	"""Read the META of the CVM FIE Balanço dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/FIE/DOC/BALANCO/META/meta_balanco_fie.txt"
	)
	_CONTRACT: ClassVar[FileContract] = META_BALANCO_FIE
