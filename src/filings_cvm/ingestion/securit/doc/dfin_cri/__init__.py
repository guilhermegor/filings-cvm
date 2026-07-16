"""CVM open-data **DFIN CRI** reader (`SECURIT/DOC/DFIN_CRI`).

Index of CRI financial statements delivered to CVM. Re-exported from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.securit.doc.dfin_cri.dfin_cri import DfinCriReader


__all__ = ["DfinCriReader"]
