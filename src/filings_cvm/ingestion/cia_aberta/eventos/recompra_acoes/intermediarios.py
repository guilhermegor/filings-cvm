"""CVM CIA_ABERTA/EVENTOS/RECOMPRA_ACOES (intermediários do programa) — ingestion (leitura) reader.

One row per **broker** engaged in a buy-back programme, joined to it by
`ID_Programa` — 4.269 rows against 1.916 programmes, so a programme may list several.

⚠️ This member has **no date column at all**, the ADM_CART shape: every column comes back as exact
source text.

Download/unzip/parse is inherited from the private `_BaseRecompraAcoesReader`; this module only
declares which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.cia_aberta_recompra_acoes import (
	CIA_ABERTA_RECOMPRA_ACOES_INTERMEDIARIOS,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.eventos.recompra_acoes._base_recompra_acoes_reader import (
	_BaseRecompraAcoesReader,
)


class RecompraAcoesIntermediariosReader(_BaseRecompraAcoesReader):
	"""Read this RECOMPRA_ACOES member into a typed DataFrame.

	Covers `intermediários do programa`.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the member (inherited).
	"""

	_MEMBER: ClassVar[str] = "cia_aberta_recompra_acoes_intermediarios.csv"
	_CONTRACT: ClassVar[FileContract] = CIA_ABERTA_RECOMPRA_ACOES_INTERMEDIARIOS
	_DATE_COLS: ClassVar[tuple[str, ...]] = ()
	_LABEL: ClassVar[str] = "intermediários do programa"
