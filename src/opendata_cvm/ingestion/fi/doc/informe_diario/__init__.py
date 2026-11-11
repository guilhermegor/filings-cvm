"""CVM open-data **Informe Diário** reader (`FI/DOC/INF_DIARIO`).

Daily net-worth and quota reports of *fundos de investimento*, plus its META reader. Re-exported
from `opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.fi.doc.informe_diario.informe_diario import InformeDiarioReader
from opendata_cvm.ingestion.fi.doc.informe_diario.meta import MetaInformeDiarioReader


__all__ = ["InformeDiarioReader", "MetaInformeDiarioReader"]
