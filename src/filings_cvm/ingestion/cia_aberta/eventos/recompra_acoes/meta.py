"""CVM **META** for the CIA_ABERTA RECOMPRA_ACOES dataset (`CIA_ABERTA/EVENTOS/RECOMPRA_ACOES`).

The spec CVM publishes for `cia_aberta_recompra_acoes.zip` — the declared description, type and
size of each field, one member per section.

⚠️ The file is `meta_cia_aberta_recompra_acoes.zip`, measured **two independent ways**: a `HEAD`
returning 200, and the `META/` directory listing, where it is the **only** file. Five other
candidate spellings 404 — including the `_txt` infix that is correct for DFP and ITR in this very
root.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_CIA_ABERTA_RECOMPRA_ACOES
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaRecompraAcoesReader(BaseMetaReader):
	"""Read the META of the CVM CIA_ABERTA RECOMPRA_ACOES dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/CIA_ABERTA/EVENTOS/RECOMPRA_ACOES/META/"
		"meta_cia_aberta_recompra_acoes.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_CIA_ABERTA_RECOMPRA_ACOES
