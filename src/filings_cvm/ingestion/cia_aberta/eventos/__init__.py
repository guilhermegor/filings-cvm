"""CVM open-data **event** readers for publicly held companies (`CIA_ABERTA/EVENTOS`).

Mirrors the `CIA_ABERTA/EVENTOS/` portal branch, which holds a single dataset: `RECOMPRA_ACOES`,
the share buy-back programmes. Unlike the `DOC` branch beside it, this one is a **snapshot** — its
readers take no `date_ref`.
"""

from filings_cvm.ingestion.cia_aberta.eventos.recompra_acoes import (
	MetaRecompraAcoesReader,
	RecompraAcoesIntermediariosReader,
	RecompraAcoesQuantidadesReader,
	RecompraAcoesReader,
)


__all__ = [
	"MetaRecompraAcoesReader",
	"RecompraAcoesIntermediariosReader",
	"RecompraAcoesQuantidadesReader",
	"RecompraAcoesReader",
]
