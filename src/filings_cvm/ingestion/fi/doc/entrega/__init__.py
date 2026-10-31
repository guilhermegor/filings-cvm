"""CVM open-data **ENTREGA FI** readers (`FI/DOC/ENTREGA`).

Index of the documents funds delivered, plus its META reader. **Two readers**, one per CSV member
of the monthly ZIP (all documents / daily funds), which share one header. Re-exported from
`filings_cvm.ingestion.fi`.
"""

from filings_cvm.ingestion.fi.doc.entrega.entrega import EntregaFiReader
from filings_cvm.ingestion.fi.doc.entrega.entrega_diario import EntregaFiDiarioReader
from filings_cvm.ingestion.fi.doc.entrega.meta import MetaEntregaFiReader


__all__ = ["EntregaFiDiarioReader", "EntregaFiReader", "MetaEntregaFiReader"]
