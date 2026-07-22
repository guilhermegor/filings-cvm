"""CVM open-data **registry** readers for incentivised companies (`CIA_INCENT/CAD`).

The single registry snapshot of incentivised companies (`cad_cia_incent.csv`,
:mod:`filings_cvm.ingestion.cia_incent.cad.cadastro`), plus its META reader. Re-exported from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.cia_incent.cad.cadastro import (
	CadastroCiaIncentReader,
	MetaCadCiaIncentReader,
)


__all__ = [
	"CadastroCiaIncentReader",
	"MetaCadCiaIncentReader",
]
