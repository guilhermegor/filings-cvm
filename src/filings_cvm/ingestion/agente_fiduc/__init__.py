"""CVM open-data **Agente Fiduciário** readers (`AGENTE_FIDUC/`).

Mirrors the `dados.cvm.gov.br/dados/AGENTE_FIDUC/` portal branch — one sibling among the portal's
other roots. It publishes only a registry (`AGENTE_FIDUC/CAD`,
:mod:`filings_cvm.ingestion.agente_fiduc.cad`) of the fiduciary agents CVM supervises, split into
natural persons and agent firms, plus its META reader. Every reader is re-exported flat from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.agente_fiduc.cad import (
	AgenteFiducPfReader,
	AgenteFiducPjReader,
	MetaAgenteFiducReader,
)


__all__ = [
	"AgenteFiducPfReader",
	"AgenteFiducPjReader",
	"MetaAgenteFiducReader",
]
