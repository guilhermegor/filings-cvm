"""CVM open-data **Cadastro de Companhias Incentivadas** reader (`CIA_INCENT/CAD`).

Snapshot registry of the incentivised companies registered with the CVM, plus its META reader.
Re-exported from `opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.cia_incent.cad.cadastro.cadastro import CadastroCiaIncentReader
from opendata_cvm.ingestion.cia_incent.cad.cadastro.meta import MetaCadCiaIncentReader


__all__ = ["CadastroCiaIncentReader", "MetaCadCiaIncentReader"]
