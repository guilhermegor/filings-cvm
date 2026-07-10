"""CVM open-data **document-dump** readers (`FI/DOC/*`).

The monthly document dumps: Informe Diário (`INF_DIARIO`), CDA (`CDA`), and the Lâmina
family (`LAMINA`, nested in :mod:`filings_cvm.ingestion.fi.doc.lamina`). Re-exported from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fi.doc.cda import CdaReader
from filings_cvm.ingestion.fi.doc.informe_diario import InformeDiarioReader
from filings_cvm.ingestion.fi.doc.lamina import LaminaCarteiraReader, LaminaReader


__all__ = [
	"CdaReader",
	"InformeDiarioReader",
	"LaminaCarteiraReader",
	"LaminaReader",
]
