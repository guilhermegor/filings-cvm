"""CVM open-data **Emissor CEPAC** readers (`EMISSOR_CEPAC/`).

Mirrors the `dados.cvm.gov.br/dados/EMISSOR_CEPAC/` portal branch — one sibling among the portal's
other roots. It publishes only a registry (`EMISSOR_CEPAC/CAD`,
:mod:`filings_cvm.ingestion.emissor_cepac.cad`) of the CEPAC issuers (municipalities). The reader
is re-exported flat from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.emissor_cepac.cad import CadastroEmissorCepacReader


__all__ = [
	"CadastroEmissorCepacReader",
]
