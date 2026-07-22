"""CVM open-data **Companhias Incentivadas** readers (`CIA_INCENT/`).

Mirrors the `dados.cvm.gov.br/dados/CIA_INCENT/` portal branch — one sibling among the portal's
other roots. It publishes only a registry (`CIA_INCENT/CAD`,
:mod:`filings_cvm.ingestion.cia_incent.cad`) of the incentivised companies registered with the CVM,
plus its META reader. Every reader is re-exported flat from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.cia_incent.cad import (
	CadastroCiaIncentReader,
	MetaCadCiaIncentReader,
)


__all__ = [
	"CadastroCiaIncentReader",
	"MetaCadCiaIncentReader",
]
