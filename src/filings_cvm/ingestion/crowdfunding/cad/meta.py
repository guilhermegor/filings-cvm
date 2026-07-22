"""CVM **META** for the CROWDFUNDING Cadastro dataset (`CROWDFUNDING/CAD`).

The spec CVM publishes for the crowdfunding-platform registry — the declared description, type and
size of each field. A ZIP of three members (`meta_cad_crowdfunding.txt`,
`meta_cad_crowdfunding_adm_resp.txt`, `meta_cad_crowdfunding_socios.txt`), so the parsed frame
comes back as one long frame with each member's section in ``section``.

⚠️ **The META is a `.zip`, not a `.txt`** — `meta_cad_crowdfunding.txt` 404s. The URL is a
per-dataset constant and is never derived from a sibling's shape (see ``docs/ingestion/meta.md``).

⚠️ **The three ``section`` labels are asymmetric — ``cad_crowdfunding``, ``adm_resp`` and
``socios``**, as in the INTERMED / COORD_OFERTA siblings. One member (`meta_cad_crowdfunding.txt`)
is named with the bare `_MEMBER_STEM` and carries no `<stem>_` suffix to strip, so ``_section_of``
falls back to labelling it by the whole stem; the other two reduce to their suffixes. That fallback
is the base's documented behaviour and all three labels stay distinct, so this is honoured, not
"fixed" by special-casing the shared base.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_CAD_CROWDFUNDING
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaCrowdfundingReader(BaseMetaReader):
	"""Read the META of the CVM CROWDFUNDING Cadastro dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/CROWDFUNDING/CAD/META/meta_cad_crowdfunding.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_CAD_CROWDFUNDING
	_MEMBER_STEM: ClassVar[str] = "cad_crowdfunding"
