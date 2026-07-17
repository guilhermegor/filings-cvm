"""CVM **META** for the FI CDA dataset (`FI/DOC/CDA`).

The spec CVM publishes for the block-type members of `cda_fi_AAAAMM.zip` (the Demonstrativo de
Composição e Diversificação das Aplicações) — the declared description, type and size of every
field. Note the `_txt` infix in the archive name (`meta_cda_fi_txt.zip`), irregular against most
other datasets' META filenames.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_CDA_FI
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaCdaReader(BaseMetaReader):
	"""Read the META of the CVM FI CDA dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = "https://dados.cvm.gov.br/dados/FI/DOC/CDA/META/meta_cda_fi_txt.zip"
	_CONTRACT: ClassVar[FileContract] = META_CDA_FI
	_MEMBER_STEM: ClassVar[str] = "cda_fi"
