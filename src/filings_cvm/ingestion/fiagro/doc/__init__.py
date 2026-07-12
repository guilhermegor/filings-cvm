"""CVM open-data **document-dump** readers for FIAGRO (`FIAGRO/DOC/*`).

Today the monthly Informe Mensal FIAGRO (`INF_MENSAL`), nested in
:mod:`filings_cvm.ingestion.fiagro.doc.inf_mensal` (2 members — informe + subclasse). Re-exported
from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fiagro.doc.inf_mensal import (
	InfMensalFiagroReader,
	InfMensalFiagroSubclasseReader,
)


__all__ = [
	"InfMensalFiagroReader",
	"InfMensalFiagroSubclasseReader",
]
