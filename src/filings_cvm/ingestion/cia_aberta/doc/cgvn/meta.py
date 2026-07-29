"""CVM **META** for the Companhias Abertas CGVN dataset (`CIA_ABERTA/DOC/CGVN`).

The spec CVM publishes for the two `cgvn_cia_aberta*` members — 12 and 11 fields, matching the real
headers exactly, so the META independently confirms both shapes.

⚠️ The URL is **constant per dataset and never derived**. Here the standard prefixed form is the
one that works — `meta_cgvn_cia_aberta.zip` — while the loose `.txt`, the no-prefix
`cgvn_cia_aberta.zip` (which *is* the correct form for the sibling FCA) and the `_txt`-infixed
variant all return **404**. Five datasets into this sub-root, five different measurements: the only
reliable method is to check the portal per dataset.

⚠️ The first member is the bare stem (`meta_cgvn_cia_aberta.txt`), so the shared base's
`_section_of` falls back to labelling it by the whole stem and the sections come back
**asymmetric** — the same shape as VLMO, FCA, INTERMED and COORD_OFERTA.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_CGVN_CIA_ABERTA
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaCgvnCiaAbertaReader(BaseMetaReader):
	"""Read the META of the CVM Companhias Abertas CGVN dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/CGVN/META/meta_cgvn_cia_aberta.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_CGVN_CIA_ABERTA
