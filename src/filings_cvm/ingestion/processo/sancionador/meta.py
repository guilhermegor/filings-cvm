"""CVM **META** for the Processo Sancionador dataset (`PROCESSO/SANCIONADOR`).

The spec CVM publishes for the sanctioning proceedings — the declared description, type and size
of each field. A ZIP of two members (`meta_processo_sancionador.txt`,
`meta_processo_sancionador_acusado.txt`), so the parsed frame comes back as one long frame with
each member's section in ``section``.

⚠️ **The two ``section`` labels are asymmetric — ``processo_sancionador`` and ``acusado``**, as in
the INTERMED / COORD_OFERTA siblings: one member is named with the bare `_MEMBER_STEM` and has no
`<stem>_` suffix to strip, so ``_section_of`` labels it by the whole stem. That is the base's
documented behaviour; both labels stay distinct, so it is honoured, not special-cased.

The META declares ``NUP`` as ``Alfanumérico`` and the ``Data_*`` fields as ``date``; the long free
text fields (``Ementa`` 4000, ``Objeto`` 2000) have no description. Its URL is a per-dataset
constant (`.zip`), never derived from a sibling.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_PROCESSO_SANCIONADOR
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaProcessoSancionadorReader(BaseMetaReader):
	"""Read the META of the CVM PROCESSO/SANCIONADOR dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/PROCESSO/SANCIONADOR/META/meta_processo_sancionador.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_PROCESSO_SANCIONADOR
	_MEMBER_STEM: ClassVar[str] = "processo_sancionador"
