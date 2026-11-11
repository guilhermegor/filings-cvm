"""CVM open-data **document-dump** readers for FIAGRO (`FIAGRO/DOC/*`).

Today the monthly Informe Mensal FIAGRO (`INF_MENSAL`), nested in
:mod:`opendata_cvm.ingestion.fiagro.doc.inf_mensal` (2 members — informe + subclasse), plus its
META reader. Re-exported from `opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.fiagro.doc.inf_mensal import (
	InfMensalFiagroReader,
	InfMensalFiagroSubclasseReader,
	MetaInfMensalFiagroReader,
)


__all__ = [
	"InfMensalFiagroReader",
	"InfMensalFiagroSubclasseReader",
	"MetaInfMensalFiagroReader",
]
