"""CVM open-data **registry** readers for offering coordinators (`COORD_OFERTA/CAD`).

The two members of `cad_coord_oferta.zip` — the coordinator registry
(:mod:`opendata_cvm.ingestion.coord_oferta.cad.coord_oferta`) and its responsible-officer table
(:mod:`opendata_cvm.ingestion.coord_oferta.cad.coord_oferta_resp`) — plus its META reader.
Re-exported from `opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.coord_oferta.cad.coord_oferta import CoordOfertaReader
from opendata_cvm.ingestion.coord_oferta.cad.coord_oferta_resp import CoordOfertaRespReader
from opendata_cvm.ingestion.coord_oferta.cad.meta import MetaCoordOfertaReader


__all__ = [
	"CoordOfertaReader",
	"CoordOfertaRespReader",
	"MetaCoordOfertaReader",
]
