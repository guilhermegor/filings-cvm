"""CVM open-data **Informe Trimestral FIP** reader (`FIP/DOC/INF_TRIMESTRAL`).

Quarterly report of Fundos de Investimento em Participações, pre-RCVM 175, plus its META reader.
Re-exported from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fip.doc.inf_trimestral.inf_trimestral import InfTrimestralFipReader
from filings_cvm.ingestion.fip.doc.inf_trimestral.meta import MetaInfTrimestralFipReader


__all__ = ["InfTrimestralFipReader", "MetaInfTrimestralFipReader"]
