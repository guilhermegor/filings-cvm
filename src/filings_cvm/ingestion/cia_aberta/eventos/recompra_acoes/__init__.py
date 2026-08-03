"""CVM open-data **RECOMPRA_ACOES** readers (`CIA_ABERTA/EVENTOS/RECOMPRA_ACOES`).

Share buy-back programmes: the programme, its brokers and its share counts, all joined by
`ID_Programa`. A **snapshot** — no `date_ref`. Re-exported from `filings_cvm.ingestion.cia_aberta`.
"""

from filings_cvm.ingestion.cia_aberta.eventos.recompra_acoes.intermediarios import (
	RecompraAcoesIntermediariosReader,
)
from filings_cvm.ingestion.cia_aberta.eventos.recompra_acoes.meta import MetaRecompraAcoesReader
from filings_cvm.ingestion.cia_aberta.eventos.recompra_acoes.quantidades import (
	RecompraAcoesQuantidadesReader,
)
from filings_cvm.ingestion.cia_aberta.eventos.recompra_acoes.recompra_acoes import (
	RecompraAcoesReader,
)


__all__ = [
	"MetaRecompraAcoesReader",
	"RecompraAcoesIntermediariosReader",
	"RecompraAcoesQuantidadesReader",
	"RecompraAcoesReader",
]
