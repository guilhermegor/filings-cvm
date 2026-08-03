"""CVM RECOMPRA_ACOES (quantidades por tipo e classe de ação) — ingestion (leitura) reader.

One row per **share type and class** in a buy-back programme, joined by
`ID_Programa`.

⚠️ This member has **no date column and no CNPJ column at all** — it identifies nothing but the
programme it belongs to, so its `tuple_cnpj_cols` is empty. Declaring one would be inventing a
column the source does not have.

⚠️ `Classe_Acao` is empty in **2.322 of 2.381 rows** (97,5%) — ordinary shares have no class. Blank
stays blank. `Quantidade_Circulacao` and `Quantidade_Operacao` are counts and stay exact text.

Download/unzip/parse is inherited from the private `_BaseRecompraAcoesReader`; this module only
declares which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.cia_aberta_recompra_acoes import (
	CIA_ABERTA_RECOMPRA_ACOES_QUANTIDADES,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.eventos.recompra_acoes._base_recompra_acoes_reader import (
	_BaseRecompraAcoesReader,
)


class RecompraAcoesQuantidadesReader(_BaseRecompraAcoesReader):
	"""Read this RECOMPRA_ACOES member into a typed DataFrame.

	Covers `quantidades por tipo e classe de ação`.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the member (inherited).
	"""

	_MEMBER: ClassVar[str] = "cia_aberta_recompra_acoes_quantidades.csv"
	_CONTRACT: ClassVar[FileContract] = CIA_ABERTA_RECOMPRA_ACOES_QUANTIDADES
	_DATE_COLS: ClassVar[tuple[str, ...]] = ()
	_LABEL: ClassVar[str] = "quantidades por tipo e classe de ação"
