"""CVM **META** for the COORD_OFERTA Cadastro dataset (`COORD_OFERTA/CAD`).

The spec CVM publishes for the offering-coordinator registry — the declared description, type and
size of each field. A ZIP of two members (`meta_cad_coord_oferta.txt`,
`meta_cad_coord_oferta_resp.txt`), so the parsed frame comes back as one long frame with each
member's section in ``section``.

⚠️ **The META is a `.zip`, not a `.txt`** — `meta_cad_coord_oferta.txt` 404s. The URL is a
per-dataset constant and is never derived from a sibling's shape (see ``docs/ingestion/meta.md``).

⚠️ **The two ``section`` labels are asymmetric — ``cad_coord_oferta`` and ``resp``**, exactly as in
the INTERMED sibling. One member (`meta_cad_coord_oferta.txt`) is named with the bare
`_MEMBER_STEM` and carries no `<stem>_` suffix to strip, so ``_section_of`` falls back to labelling
it by the whole stem; its sibling reduces to ``resp``. That fallback is the base's documented
behaviour and both labels stay distinct, so this is honoured, not "fixed" by special-casing the
shared base.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_CAD_COORD_OFERTA
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaCoordOfertaReader(BaseMetaReader):
	"""Read the META of the CVM COORD_OFERTA Cadastro dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/COORD_OFERTA/CAD/META/meta_cad_coord_oferta.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_CAD_COORD_OFERTA
	_MEMBER_STEM: ClassVar[str] = "cad_coord_oferta"
