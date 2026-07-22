"""CVM open-data **Cadastro de Companhias Abertas** reader (`CIA_ABERTA/CAD`).

Snapshot registry of the publicly held companies registered with the CVM, plus its META reader.
Re-exported from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.cia_aberta.cad.cadastro.cadastro import CadastroCiaAbertaReader
from filings_cvm.ingestion.cia_aberta.cad.cadastro.meta import MetaCadCiaAbertaReader


__all__ = ["CadastroCiaAbertaReader", "MetaCadCiaAbertaReader"]
