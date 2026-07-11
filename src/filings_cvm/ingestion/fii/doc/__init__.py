"""CVM open-data **document-dump** readers for FII (`FII/DOC/*`).

The FII portal root holds only document dumps (there is no `FII/CAD`). Today the Informe Mensal
(`INF_MENSAL`), nested in :mod:`filings_cvm.ingestion.fii.doc.inf_mensal` (3 members); the
`DFIN`, `INF_TRIMESTRAL` and `INF_ANUAL` datasets land as siblings. Re-exported from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fii.doc.inf_mensal import (
	InfMensalFiiAtivoPassivoReader,
	InfMensalFiiComplementoReader,
	InfMensalFiiGeralReader,
)


__all__ = [
	"InfMensalFiiAtivoPassivoReader",
	"InfMensalFiiComplementoReader",
	"InfMensalFiiGeralReader",
]
