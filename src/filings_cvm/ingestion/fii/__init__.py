"""CVM open-data **Fundos de Investimento Imobiliário** readers (`FII/`).

Mirrors the `dados.cvm.gov.br/dados/FII/` portal branch — one sibling among the portal's other
roots (`FI/`, `FIDC/`, `AUDITOR/`, …), each of which gets its own sub-package here as it is
implemented. Under `FII/` live only the document dumps
(:mod:`filings_cvm.ingestion.fii.doc`) — the portal publishes no `FII/CAD`. Every reader is
re-exported flat from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fii.doc import (
	DfinFiiReader,
	InfMensalFiiAtivoPassivoReader,
	InfMensalFiiComplementoReader,
	InfMensalFiiGeralReader,
)


__all__ = [
	"DfinFiiReader",
	"InfMensalFiiAtivoPassivoReader",
	"InfMensalFiiComplementoReader",
	"InfMensalFiiGeralReader",
]
