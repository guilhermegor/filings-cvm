"""CVM **META** for the Atos Declaratórios dataset (`ATO_DECLR/INTERMED`).

The spec CVM publishes for `ato_declr.csv` — the declared description, type and size of each
field. A flat `.txt`, so the whole document is one section.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_ATO_DECLR
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaAtoDeclrReader(BaseMetaReader):
	"""Read the META of the CVM Atos Declaratórios dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/ATO_DECLR/INTERMED/META/meta_ato_declr.txt"
	)
	_CONTRACT: ClassVar[FileContract] = META_ATO_DECLR
