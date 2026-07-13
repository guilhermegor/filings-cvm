"""CVM open-data **registry** readers for CEPAC issuers (`EMISSOR_CEPAC/CAD`).

The single registry snapshot of CEPAC issuers (`cad_emissor_cepac.csv`,
:mod:`filings_cvm.ingestion.emissor_cepac.cad.cadastro`). Re-exported from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.emissor_cepac.cad.cadastro import CadastroEmissorCepacReader


__all__ = [
	"CadastroEmissorCepacReader",
]
