"""CVM open-data **Lâmina** readers (`FI/DOC/LAMINA`).

Both members of the monthly `lamina_fi_AAAAMM.zip`: the fact sheet proper and its
allocation-by-asset-type carteira member, plus its META reader. Re-exported from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fi.doc.lamina.lamina import LaminaReader
from filings_cvm.ingestion.fi.doc.lamina.lamina_carteira import LaminaCarteiraReader
from filings_cvm.ingestion.fi.doc.lamina.meta import MetaLaminaReader


__all__ = ["LaminaCarteiraReader", "LaminaReader", "MetaLaminaReader"]
