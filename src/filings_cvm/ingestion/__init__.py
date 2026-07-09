"""Ingestion section — parse and interpret files *received* from CVM (leitura).

Every "leitura" solution lives here: it takes a file downloaded from CVM (an XML
standard document or an open-data dump) and returns typed models / DataFrames. The
building/serialising counterpart lives in the ``submission`` section.

    from filings_cvm.ingestion import InformeDiarioReader
"""

from filings_cvm.ingestion.cda import CdaReader
from filings_cvm.ingestion.informe_diario import InformeDiarioReader


__all__ = ["CdaReader", "InformeDiarioReader"]
