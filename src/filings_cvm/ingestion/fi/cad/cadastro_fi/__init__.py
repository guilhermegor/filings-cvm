"""CVM open-data **Cadastro de Fundos** reader (`FI/CAD`).

Snapshot registry of every fund CVM has ever registered. Re-exported from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fi.cad.cadastro_fi.cadastro_fi import CadastroFiReader


__all__ = ["CadastroFiReader"]
