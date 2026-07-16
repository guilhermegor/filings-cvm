"""CVM open-data **Balancete FIE** reader (`FIE/DOC/BALANCETE`).

Monthly accounting trial balance of the Fundos de Investimento Especialmente
constituídos. Re-exported from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fie.doc.balancete.balancete import BalanceteFieReader


__all__ = ["BalanceteFieReader"]
