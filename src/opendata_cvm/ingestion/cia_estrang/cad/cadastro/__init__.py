"""CVM open-data **Cadastro de Companhias Estrangeiras** reader (`CIA_ESTRANG/CAD`).

Snapshot registry of the foreign companies registered with the CVM, plus its META reader.
Re-exported from `opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.cia_estrang.cad.cadastro.cadastro import CadastroCiaEstrangReader
from opendata_cvm.ingestion.cia_estrang.cad.cadastro.meta import MetaCadCiaEstrangReader


__all__ = ["CadastroCiaEstrangReader", "MetaCadCiaEstrangReader"]
