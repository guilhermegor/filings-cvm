"""CVM open-data **Informe Trimestral FIP** reader (`FIP/DOC/INF_TRIMESTRAL`).

Quarterly report of Fundos de Investimento em Participações, pre-RCVM 175. Re-exported
from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fip.doc.inf_trimestral.inf_trimestral import InfTrimestralFipReader


__all__ = ["InfTrimestralFipReader"]
