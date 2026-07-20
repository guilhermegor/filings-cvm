"""CVM open-data **registry** readers for fiduciary agents (`AGENTE_FIDUC/CAD`).

The two members of the `cad_agente_fiduc.zip` snapshot — natural-person agents
(:class:`~filings_cvm.ingestion.agente_fiduc.cad.agente_fiduc_pf.AgenteFiducPfReader`) and agent
firms (:class:`~filings_cvm.ingestion.agente_fiduc.cad.agente_fiduc_pj.AgenteFiducPjReader`) — over
a shared private base (`_base_agente_fiduc_reader`), plus the dataset's META reader. Re-exported
from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.agente_fiduc.cad.agente_fiduc_pf import AgenteFiducPfReader
from filings_cvm.ingestion.agente_fiduc.cad.agente_fiduc_pj import AgenteFiducPjReader
from filings_cvm.ingestion.agente_fiduc.cad.meta import MetaAgenteFiducReader


__all__ = [
	"AgenteFiducPfReader",
	"AgenteFiducPjReader",
	"MetaAgenteFiducReader",
]
