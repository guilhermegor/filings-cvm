"""CVM **META** for the CIA_ABERTA ITR dataset (`CIA_ABERTA/DOC/ITR`).

The spec CVM publishes for `itr_cia_aberta_AAAA.zip` — the declared description, type and size of
each field, one member per section.

⚠️ The file is `meta_itr_cia_aberta_txt.zip`, with the **`_txt` infix** — the same spelling DFP
uses, and still **measured rather than derived**: the other three forms this portal uses elsewhere
all **404**, and elsewhere in this very sub-root FCA answers only to a no-prefix name and IPE to a
loose `.txt`.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_ITR_CIA_ABERTA
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaItrCiaAbertaReader(BaseMetaReader):
	"""Read the META of the CVM CIA_ABERTA ITR dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/META/meta_itr_cia_aberta_txt.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_ITR_CIA_ABERTA
