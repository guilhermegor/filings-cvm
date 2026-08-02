"""CVM open-data **EVENTUAL FI** reader (`FI/DOC/EVENTUAL`).

Index of the eventual documents funds and classes deliver to CVM, plus its META reader.
Re-exported from `filings_cvm.ingestion.fi`.
"""

from filings_cvm.ingestion.fi.doc.eventual.eventual import EventualFiReader
from filings_cvm.ingestion.fi.doc.eventual.meta import MetaEventualFiReader


__all__ = ["EventualFiReader", "MetaEventualFiReader"]
