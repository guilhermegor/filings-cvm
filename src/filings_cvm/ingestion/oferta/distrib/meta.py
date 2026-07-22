"""CVM **META** for the OFERTA/DISTRIB dataset (`OFERTA/DISTRIB`).

The spec CVM publishes for the securities-offering register — the declared description, type and
size of each field. A ZIP of two members (`meta_oferta_distribuicao.txt`,
`meta_oferta_resolucao_160.txt`), so the parsed frame comes back as one long frame with each
member's section in ``section``.

⚠️ **The META is a `.zip`, not a `.txt`** — `meta_oferta_distribuicao.txt` 404s. The URL is a
per-dataset constant and is never derived from a sibling's shape (see ``docs/ingestion/meta.md``).

The two members share the ``oferta_`` prefix, so with ``_MEMBER_STEM = "oferta"`` the base's
``_section_of`` strips it to leave the clean, symmetric section labels ``distribuicao`` and
``resolucao_160`` — unlike the INTERMED / COORD_OFERTA metas, whose bare-stem member forces an
asymmetric fallback.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_OFERTA_DISTRIBUICAO
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaOfertaReader(BaseMetaReader):
	"""Read the META of the CVM OFERTA/DISTRIB dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/OFERTA/DISTRIB/META/meta_oferta_distribuicao.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_OFERTA_DISTRIBUICAO
	_MEMBER_STEM: ClassVar[str] = "oferta"
