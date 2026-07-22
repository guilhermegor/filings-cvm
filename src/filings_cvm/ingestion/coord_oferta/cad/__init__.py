"""CVM open-data **registry** readers for offering coordinators (`COORD_OFERTA/CAD`).

The two members of `cad_coord_oferta.zip` — the coordinator registry
(:mod:`filings_cvm.ingestion.coord_oferta.cad.coord_oferta`) and its responsible-officer table
(:mod:`filings_cvm.ingestion.coord_oferta.cad.coord_oferta_resp`) — plus its META reader.
Re-exported from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.coord_oferta.cad.coord_oferta import CoordOfertaReader
from filings_cvm.ingestion.coord_oferta.cad.coord_oferta_resp import CoordOfertaRespReader
from filings_cvm.ingestion.coord_oferta.cad.meta import MetaCoordOfertaReader


__all__ = [
	"CoordOfertaReader",
	"CoordOfertaRespReader",
	"MetaCoordOfertaReader",
]
