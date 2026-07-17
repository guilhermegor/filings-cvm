"""CVM open-data **Fundos de Investimento nas Cadeias Produtivas Agroindustriais** readers.

Mirrors the `dados.cvm.gov.br/dados/FIAGRO/` portal branch — one sibling among the portal's other
roots (`FI/`, `FIDC/`, `FII/`, `FIP/`, …), each of which gets its own sub-package here as it is
implemented. Under `FIAGRO/` live the document dumps
(:mod:`filings_cvm.ingestion.fiagro.doc`), today the Informe Mensal FIAGRO, plus its META reader.
Every reader is re-exported flat from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fiagro.doc import (
	InfMensalFiagroReader,
	InfMensalFiagroSubclasseReader,
	MetaInfMensalFiagroReader,
)


__all__ = [
	"InfMensalFiagroReader",
	"InfMensalFiagroSubclasseReader",
	"MetaInfMensalFiagroReader",
]
