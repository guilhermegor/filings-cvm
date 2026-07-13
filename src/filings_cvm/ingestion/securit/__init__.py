"""CVM open-data **Securitização** readers (`SECURIT/`).

Mirrors the `dados.cvm.gov.br/dados/SECURIT/` portal branch — one sibling among the portal's other
roots (`FI/`, `FIDC/`, `FII/`, `FIP/`, `FIAGRO/`, `FIE/`, …). Under `SECURIT/` live the document
dumps (:mod:`filings_cvm.ingestion.securit.doc`) — the DFIN CRA/CRI indexes today, the monthly
`INF_MENSAL_*` dumps as they land. Every reader is re-exported flat from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.securit.doc import (
	DfinCraReader,
	DfinCriReader,
)


__all__ = [
	"DfinCraReader",
	"DfinCriReader",
]
