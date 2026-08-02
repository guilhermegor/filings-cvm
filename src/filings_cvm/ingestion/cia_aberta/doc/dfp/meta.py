"""CVM **META** for the CIA_ABERTA DFP dataset (`CIA_ABERTA/DOC/DFP`).

The spec CVM publishes for `dfp_cia_aberta_AAAA.zip` — the declared description, type and size of
each field, one member per section.

⚠️ The file is `meta_dfp_cia_aberta_txt.zip`, with the **`_txt` infix**; the three other spellings
this portal uses elsewhere (`meta_dfp_cia_aberta.txt`, `meta_dfp_cia_aberta.zip` and the
no-prefix `dfp_cia_aberta.zip`, which is the correct form for the sibling FCA) all **404**. The URL
is measured per dataset, never derived.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_DFP_CIA_ABERTA
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaDfpCiaAbertaReader(BaseMetaReader):
	"""Read the META of the CVM CIA_ABERTA DFP dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/META/meta_dfp_cia_aberta_txt.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_DFP_CIA_ABERTA
