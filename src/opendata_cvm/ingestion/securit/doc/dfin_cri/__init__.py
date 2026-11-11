"""CVM open-data **DFIN CRI** reader (`SECURIT/DOC/DFIN_CRI`).

Index of CRI financial statements delivered to CVM, plus its META reader. Re-exported from
`opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.securit.doc.dfin_cri.dfin_cri import DfinCriReader
from opendata_cvm.ingestion.securit.doc.dfin_cri.meta import MetaDfinCriReader


__all__ = ["DfinCriReader", "MetaDfinCriReader"]
