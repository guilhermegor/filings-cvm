"""CVM open-data **Informe Quadrimestral FIP** reader (`FIP/DOC/INF_QUADRIMESTRAL`).

Four-monthly report of Fundos de Investimento em Participações, post-RCVM 175, plus its META
reader. Re-exported from `opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.fip.doc.inf_quadrimestral.inf_quadrimestral import (
	InfQuadrimestralFipReader,
)
from opendata_cvm.ingestion.fip.doc.inf_quadrimestral.meta import MetaInfQuadrimestralFipReader


__all__ = ["InfQuadrimestralFipReader", "MetaInfQuadrimestralFipReader"]
