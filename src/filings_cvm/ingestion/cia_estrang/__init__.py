"""CVM open-data **Companhias Estrangeiras** readers (`CIA_ESTRANG/`).

Mirrors the `dados.cvm.gov.br/dados/CIA_ESTRANG/` portal branch — one sibling among the portal's
other roots. It publishes only a registry (`CIA_ESTRANG/CAD`,
:mod:`filings_cvm.ingestion.cia_estrang.cad`) of the foreign companies registered with the CVM,
plus its META reader. Every reader is re-exported flat from `filings_cvm.ingestion`. Opens Wave 4
of the portal sweep (issue #41).
"""

from filings_cvm.ingestion.cia_estrang.cad import (
	CadastroCiaEstrangReader,
	MetaCadCiaEstrangReader,
)


__all__ = [
	"CadastroCiaEstrangReader",
	"MetaCadCiaEstrangReader",
]
