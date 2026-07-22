"""CVM open-data **Cadastro de Administrador de FII** reader (`ADM_FII/CAD`).

Snapshot registry of the entities registered to administer FIIs, plus its META reader.
Re-exported from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.adm_fii.cad.cadastro.cadastro import CadastroAdmFiiReader
from filings_cvm.ingestion.adm_fii.cad.cadastro.meta import MetaCadAdmFiiReader


__all__ = ["CadastroAdmFiiReader", "MetaCadAdmFiiReader"]
