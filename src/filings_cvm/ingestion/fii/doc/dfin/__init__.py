"""CVM open-data **DFIN FII** reader (`FII/DOC/DFIN`).

Index of FII financial statements delivered to CVM. Re-exported from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fii.doc.dfin.dfin import DfinFiiReader


__all__ = ["DfinFiiReader"]
