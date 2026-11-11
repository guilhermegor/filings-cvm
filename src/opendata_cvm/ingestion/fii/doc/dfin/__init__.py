"""CVM open-data **DFIN FII** reader (`FII/DOC/DFIN`).

Index of FII financial statements delivered to CVM, plus its META reader. Re-exported from
`opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.fii.doc.dfin.dfin import DfinFiiReader
from opendata_cvm.ingestion.fii.doc.dfin.meta import MetaDfinFiiReader


__all__ = ["DfinFiiReader", "MetaDfinFiiReader"]
