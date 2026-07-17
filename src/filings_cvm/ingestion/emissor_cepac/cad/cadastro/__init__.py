"""CVM open-data **Cadastro de Emissor CEPAC** reader (`EMISSOR_CEPAC/CAD`).

Snapshot registry of municipalities issuing CEPAC, plus its META reader. Re-exported from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.emissor_cepac.cad.cadastro.cadastro import CadastroEmissorCepacReader
from filings_cvm.ingestion.emissor_cepac.cad.cadastro.meta import MetaCadEmissorCepacReader


__all__ = ["CadastroEmissorCepacReader", "MetaCadEmissorCepacReader"]
