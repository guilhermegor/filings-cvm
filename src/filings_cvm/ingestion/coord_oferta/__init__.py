"""CVM open-data **Coordenadores de Oferta** readers (`COORD_OFERTA/`).

Mirrors the `dados.cvm.gov.br/dados/COORD_OFERTA/` portal branch — one sibling among the portal's
other roots. It publishes only a registry (`COORD_OFERTA/CAD`,
:mod:`filings_cvm.ingestion.coord_oferta.cad`) of the institutions registered to coordinate
securities offerings, in a two-member archive, plus its META reader. Every reader is re-exported
flat from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.coord_oferta.cad import (
	CoordOfertaReader,
	CoordOfertaRespReader,
	MetaCoordOfertaReader,
)


__all__ = [
	"CoordOfertaReader",
	"CoordOfertaRespReader",
	"MetaCoordOfertaReader",
]
