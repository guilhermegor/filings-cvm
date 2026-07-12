"""CVM open-data **Fundos de Investimento Especialmente constituídos** readers (`FIE/`).

Mirrors the `dados.cvm.gov.br/dados/FIE/` portal branch — one sibling among the portal's other
roots (`FI/`, `FIDC/`, `FII/`, `FIP/`, `FIAGRO/`, …). Under `FIE/` live the accounting document
dumps (:mod:`filings_cvm.ingestion.fie.doc` — balancete, balanço) and, as a sibling of `DOC/`, the
monthly measures (:mod:`filings_cvm.ingestion.fie.medidas`). The portal publishes **no** `FIE/CAD`
(both its `DADOS/` and `META/` are empty). Every reader is re-exported flat from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fie.doc import (
	BalanceteFieReader,
	BalancoFieReader,
)
from filings_cvm.ingestion.fie.medidas import MedidasMesFieReader


__all__ = [
	"BalanceteFieReader",
	"BalancoFieReader",
	"MedidasMesFieReader",
]
