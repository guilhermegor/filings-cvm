"""CVM open-data **Fundos de Investimento em Participações** readers (`FIP/`).

Mirrors the `dados.cvm.gov.br/dados/FIP/` portal branch — one sibling among the portal's other
roots (`FI/`, `FIDC/`, `FII/`, …), each of which gets its own sub-package here as it is
implemented. Under `FIP/` live only the document dumps
(:mod:`filings_cvm.ingestion.fip.doc`) — the portal publishes no `FIP/CAD`. Every reader is
re-exported flat from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fip.doc import (
	InfQuadrimestralFipReader,
	InfTrimestralFipReader,
)


__all__ = [
	"InfQuadrimestralFipReader",
	"InfTrimestralFipReader",
]
