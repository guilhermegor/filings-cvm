"""CVM **META** for the Companhias Abertas IPE dataset (`CIA_ABERTA/DOC/IPE`).

The spec CVM publishes for `ipe_cia_aberta_AAAA.csv` — the declared description, type and size of
each of its 13 fields. A flat `.txt`, so the whole document is one section.

⚠️ The URL is **constant per dataset and never derived**. Across the seven `CIA_ABERTA/DOC`
datasets CVM uses **four** different META spellings — `meta_<ds>_cia_aberta.zip`,
`meta_<ds>_cia_aberta_txt.zip` (with an `_txt` infix), `fca_cia_aberta.zip` (no `meta_` prefix at
all), and this loose `.txt`. A "derive the name" rule would 404 or fetch the wrong dataset's spec.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_IPE_CIA_ABERTA
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaIpeCiaAbertaReader(BaseMetaReader):
	"""Read the META of the CVM Companhias Abertas IPE dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/META/meta_ipe_cia_aberta.txt"
	)
	_CONTRACT: ClassVar[FileContract] = META_IPE_CIA_ABERTA
