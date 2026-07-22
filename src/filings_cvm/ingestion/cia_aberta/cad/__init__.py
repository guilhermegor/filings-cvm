"""CVM open-data **registry** readers for publicly held companies (`CIA_ABERTA/CAD`).

The single registry snapshot of publicly held companies (`cad_cia_aberta.csv`,
:mod:`filings_cvm.ingestion.cia_aberta.cad.cadastro`), plus its META reader. Re-exported from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.cia_aberta.cad.cadastro import (
	CadastroCiaAbertaReader,
	MetaCadCiaAbertaReader,
)


__all__ = [
	"CadastroCiaAbertaReader",
	"MetaCadCiaAbertaReader",
]
