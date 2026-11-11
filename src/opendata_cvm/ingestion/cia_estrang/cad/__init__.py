"""CVM open-data **registry** readers for foreign companies (`CIA_ESTRANG/CAD`).

The single registry snapshot of foreign companies (`cad_cia_estrang.csv`,
:mod:`opendata_cvm.ingestion.cia_estrang.cad.cadastro`), plus its META reader. Re-exported from
`opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.cia_estrang.cad.cadastro import (
	CadastroCiaEstrangReader,
	MetaCadCiaEstrangReader,
)


__all__ = [
	"CadastroCiaEstrangReader",
	"MetaCadCiaEstrangReader",
]
