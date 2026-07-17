"""CVM open-data **DFIN CRA** reader (`SECURIT/DOC/DFIN_CRA`).

Index of CRA financial statements delivered to CVM, plus its META reader. Re-exported from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.securit.doc.dfin_cra.dfin_cra import DfinCraReader
from filings_cvm.ingestion.securit.doc.dfin_cra.meta import MetaDfinCraReader


__all__ = ["DfinCraReader", "MetaDfinCraReader"]
