"""CVM open-data **Balanço FIE** reader (`FIE/DOC/BALANCO`).

Yearly accounting balance sheet of the Fundos de Investimento Especialmente
constituídos, discontinued in 2020, plus its META reader. Re-exported from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fie.doc.balanco.balanco import BalancoFieReader
from filings_cvm.ingestion.fie.doc.balanco.meta import MetaBalancoFieReader


__all__ = ["BalancoFieReader", "MetaBalancoFieReader"]
