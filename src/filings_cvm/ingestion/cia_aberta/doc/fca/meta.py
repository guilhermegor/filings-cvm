"""CVM **META** for the Companhias Abertas FCA dataset (`CIA_ABERTA/DOC/FCA`).

The spec CVM publishes for the ten `fca_cia_aberta_*` members — the declared description, type and
size of each field. Its ten field counts (9 / 15 / 7 / 23 / 26 / 21 / 24 / 26 / 7 / 18) match the
real headers exactly, so it independently confirms every member's shape.

⚠️ **This is the strongest case in the portal for "the META URL is constant per dataset and never
derived."** The archive is `fca_cia_aberta.zip` — the one META file in the portal published
**without the `meta_` prefix** — while its ten members *are* prefixed `meta_fca_cia_aberta*`. Both
obvious derivations 404: `meta_fca_cia_aberta.zip` and `meta_fca_cia_aberta.txt`. Measured, not
assumed.

Note that the sibling `CIA_ABERTA/CAD` dataset *does* publish `meta_cad_cia_aberta.txt` and it
works fine — the prefix is not portal-wide policy, it varies per dataset, which is exactly why each
`Meta*Reader` pins its own literal URL.

⚠️ The first member is the bare stem (`meta_fca_cia_aberta.txt`), so the shared base's
`_section_of` falls back to labelling it by the whole stem and the sections come back
**asymmetric** — the same shape as VLMO, INTERMED and COORD_OFERTA. Honoured as-is.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_FCA_CIA_ABERTA
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaFcaCiaAbertaReader(BaseMetaReader):
	"""Read the META of the CVM Companhias Abertas FCA dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	# NOT `meta_fca_cia_aberta.zip` — that 404s. See the module docstring.
	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/META/fca_cia_aberta.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_FCA_CIA_ABERTA
