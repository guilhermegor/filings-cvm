"""CVM open-data **Medidas Mensais FIE** reader (`FIE/MEDIDAS`).

Monthly headline measures (net worth, shareholder count) of the Fundos de Investimento
Especialmente constituídos. Re-exported from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fie.medidas.medidas import MedidasMesFieReader


__all__ = ["MedidasMesFieReader"]
