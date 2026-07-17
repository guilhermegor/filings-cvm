"""CVM open-data **CDA** reader (`FI/DOC/CDA`).

Demonstrativo de Composição e Diversificação das Aplicações, plus its META reader. Re-exported
from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fi.doc.cda.cda import CdaReader
from filings_cvm.ingestion.fi.doc.cda.meta import MetaCdaReader


__all__ = ["CdaReader", "MetaCdaReader"]
