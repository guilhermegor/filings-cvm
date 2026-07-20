"""CVM open-data **Intermediários** readers (`INTERMED/`).

Mirrors the `dados.cvm.gov.br/dados/INTERMED/` portal branch — one sibling among the portal's other
roots. It publishes only a registry (`INTERMED/CAD`, :mod:`filings_cvm.ingestion.intermed.cad`) of
the market intermediaries CVM supervises, plus a table of their responsible officers.
"""

from filings_cvm.ingestion.intermed.cad import (
	IntermedReader,
	IntermedRespReader,
	MetaIntermedReader,
)


__all__ = [
	"IntermedReader",
	"IntermedRespReader",
	"MetaIntermedReader",
]
