"""CVM open-data **Cadastro de Fundos** reader (`FI/CAD`).

Snapshot registry of every fund CVM has ever registered, plus its META reader. Re-exported from
`opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.fi.cad.cadastro_fi.cadastro_fi import CadastroFiReader
from opendata_cvm.ingestion.fi.cad.cadastro_fi.meta import MetaCadastroFiReader


__all__ = ["CadastroFiReader", "MetaCadastroFiReader"]
