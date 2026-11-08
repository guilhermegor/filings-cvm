"""CVM open-data **Processo** readers (`PROCESSO/`).

Mirrors the `dados.cvm.gov.br/dados/PROCESSO/` portal branch — one sibling among the portal's other
roots. It publishes only the sanctioning proceedings (`PROCESSO/SANCIONADOR`,
:mod:`filings_cvm.ingestion.processo.sancionador`), in a two-member archive, plus its META reader.
"""

from filings_cvm.ingestion.processo.sancionador import (
	MetaProcessoSancionadorReader,
	ProcessoSancionadorAcusadoReader,
	ProcessoSancionadorReader,
)


__all__ = [
	"MetaProcessoSancionadorReader",
	"ProcessoSancionadorAcusadoReader",
	"ProcessoSancionadorReader",
]
