"""CVM open-data **Balanço FIE** reader (`FIE/DOC/BALANCO`).

Yearly accounting balance sheet of the Fundos de Investimento Especialmente
constituídos, discontinued in 2020. Re-exported from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fie.doc.balanco.balanco import BalancoFieReader


__all__ = ["BalancoFieReader"]
