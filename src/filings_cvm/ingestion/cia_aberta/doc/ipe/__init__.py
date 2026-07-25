"""CVM open-data **IPE** reader for publicly held companies (`CIA_ABERTA/DOC/IPE`).

Index of the *Informações Periódicas e Eventuais* each listed company filed with CVM in a year —
one row per document, carrying a `Link_Download` the reader returns as text and never follows —
plus its META reader. Re-exported from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.cia_aberta.doc.ipe.ipe import IpeCiaAbertaReader
from filings_cvm.ingestion.cia_aberta.doc.ipe.meta import MetaIpeCiaAbertaReader


__all__ = ["IpeCiaAbertaReader", "MetaIpeCiaAbertaReader"]
