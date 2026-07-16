"""CVM open-data **Cadastro de Emissor CEPAC** reader (`EMISSOR_CEPAC/CAD`).

Snapshot registry of municipalities issuing CEPAC. Re-exported from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.emissor_cepac.cad.cadastro.cadastro import CadastroEmissorCepacReader


__all__ = ["CadastroEmissorCepacReader"]
