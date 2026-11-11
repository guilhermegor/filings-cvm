"""CVM open-data **Ofertas de Distribuição** readers (`OFERTA/`).

Mirrors the `dados.cvm.gov.br/dados/OFERTA/` portal branch — one sibling among the portal's other
roots. It publishes only the distribution register (`OFERTA/DISTRIB`,
:mod:`opendata_cvm.ingestion.oferta.distrib`) of securities offerings, in a two-member archive (one
per regulatory regime), plus its META reader. Every reader is re-exported flat from
`opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.oferta.distrib import (
	MetaOfertaReader,
	OfertaDistribuicaoReader,
	OfertaResolucao160Reader,
)


__all__ = [
	"MetaOfertaReader",
	"OfertaDistribuicaoReader",
	"OfertaResolucao160Reader",
]
