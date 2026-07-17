"""CVM Informe Mensal FIAGRO readers — the 2 members of ``inf_mensal_fiagro_AAAAMM.zip``.

One reader per member — the informe proper (``InfMensalFiagroReader``) and its per-subclasse
breakdown (``InfMensalFiagroSubclasseReader``) — over a shared private base
(`_base_inf_mensal_fiagro_reader`), plus its META reader. Re-exported from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fiagro.doc.inf_mensal.inf_mensal_fiagro import InfMensalFiagroReader
from filings_cvm.ingestion.fiagro.doc.inf_mensal.inf_mensal_fiagro_subclasse import (
	InfMensalFiagroSubclasseReader,
)
from filings_cvm.ingestion.fiagro.doc.inf_mensal.meta import MetaInfMensalFiagroReader


__all__ = [
	"InfMensalFiagroReader",
	"InfMensalFiagroSubclasseReader",
	"MetaInfMensalFiagroReader",
]
