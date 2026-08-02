"""CVM **META** for the FI EVENTUAL dataset (`FI/DOC/EVENTUAL`).

The spec CVM publishes for `eventual_fi_AAAA.csv` — the declared description, type and size of each
field. A flat `.txt`, so the whole document is one section; the three other spellings this portal
uses elsewhere (`meta_eventual_fi.zip`, `eventual_fi.zip`, `meta_eventual_fi_txt.zip`) all 404, so
the URL is pinned rather than derived.

⚠️ Its eleven fields are listed **alphabetically**, which is not the order of the real file — the
header stays the source of column order, and the META the source of declared types.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_EVENTUAL_FI
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaEventualFiReader(BaseMetaReader):
	"""Read the META of the CVM FI EVENTUAL dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/FI/DOC/EVENTUAL/META/meta_eventual_fi.txt"
	)
	_CONTRACT: ClassVar[FileContract] = META_EVENTUAL_FI
