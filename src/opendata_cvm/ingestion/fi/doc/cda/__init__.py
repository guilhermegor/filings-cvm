"""CVM open-data **CDA** reader (`FI/DOC/CDA`).

`Demonstrativo de Composição e Diversificação das Aplicações`, plus its META reader. Re-exported
from `opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.fi.doc.cda.cda import CdaReader
from opendata_cvm.ingestion.fi.doc.cda.meta import MetaCdaReader


__all__ = ["CdaReader", "MetaCdaReader"]
