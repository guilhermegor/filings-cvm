"""CVM open-data **registry** readers for autonomous investment agents (`AGENTE_AUTON/CAD`).

The two members of the `cad_agente_auton.zip` snapshot — natural-person agents
(:class:`~filings_cvm.ingestion.agente_auton.cad.agente_auton_pf.AgenteAutonPfReader`) and agent
firms (:class:`~filings_cvm.ingestion.agente_auton.cad.agente_auton_pj.AgenteAutonPjReader`) — over
a shared private base (`_base_agente_auton_reader`), plus the dataset's META reader. Re-exported
from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.agente_auton.cad.agente_auton_pf import AgenteAutonPfReader
from filings_cvm.ingestion.agente_auton.cad.agente_auton_pj import AgenteAutonPjReader
from filings_cvm.ingestion.agente_auton.cad.meta import MetaAgenteAutonReader


__all__ = [
	"AgenteAutonPfReader",
	"AgenteAutonPjReader",
	"MetaAgenteAutonReader",
]
