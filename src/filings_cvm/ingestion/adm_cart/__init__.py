"""CVM open-data **Administradores de Carteira** readers (`ADM_CART/`).

Mirrors the `dados.cvm.gov.br/dados/ADM_CART/` portal branch — one sibling among the portal's other
roots. It publishes only a registry (`ADM_CART/CAD`, :mod:`filings_cvm.ingestion.adm_cart.cad`) of
the portfolio managers CVM supervises, split across five members: the natural- and legal-person
managers plus their directors, responsible officers and partners.
"""

from filings_cvm.ingestion.adm_cart.cad import (
	AdmCartDiretorReader,
	AdmCartPfReader,
	AdmCartPjReader,
	AdmCartRespReader,
	AdmCartSociosReader,
	MetaAdmCartReader,
)


__all__ = [
	"AdmCartDiretorReader",
	"AdmCartPfReader",
	"AdmCartPjReader",
	"AdmCartRespReader",
	"AdmCartSociosReader",
	"MetaAdmCartReader",
]
