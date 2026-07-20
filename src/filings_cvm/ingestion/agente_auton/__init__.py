"""CVM open-data **Agente Autônomo** readers (`AGENTE_AUTON/`).

Mirrors the `dados.cvm.gov.br/dados/AGENTE_AUTON/` portal branch — one sibling among the portal's
other roots. It publishes only a registry (`AGENTE_AUTON/CAD`,
:mod:`filings_cvm.ingestion.agente_auton.cad`) of the autonomous investment agents CVM supervises,
split into natural persons and agent firms, plus its META reader. Every reader is re-exported flat
from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.agente_auton.cad import (
	AgenteAutonPfReader,
	AgenteAutonPjReader,
	MetaAgenteAutonReader,
)


__all__ = [
	"AgenteAutonPfReader",
	"AgenteAutonPjReader",
	"MetaAgenteAutonReader",
]
