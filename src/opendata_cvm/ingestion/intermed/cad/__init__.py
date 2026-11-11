"""CVM open-data **registry** readers for market intermediaries (`INTERMED/CAD`).

The two members of the `cad_intermed.zip` snapshot — the intermediary registry
(:class:`~opendata_cvm.ingestion.intermed.cad.intermed.IntermedReader`) and its responsible-officer
table (:class:`~opendata_cvm.ingestion.intermed.cad.intermed_resp.IntermedRespReader`) — over a
shared private base (`_base_intermed_reader`), plus the dataset's META reader. Re-exported flat at
the package root.
"""

from opendata_cvm.ingestion.intermed.cad.intermed import IntermedReader
from opendata_cvm.ingestion.intermed.cad.intermed_resp import IntermedRespReader
from opendata_cvm.ingestion.intermed.cad.meta import MetaIntermedReader


__all__ = [
	"IntermedReader",
	"IntermedRespReader",
	"MetaIntermedReader",
]
