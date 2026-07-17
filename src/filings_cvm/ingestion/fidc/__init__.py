"""CVM open-data **Fundos de Investimento em Direitos Creditórios** readers (`FIDC/`).

Mirrors the `dados.cvm.gov.br/dados/FIDC/` portal branch — one sibling among the portal's other
roots (`FI/`, `FII/`, `AUDITOR/`, …), each of which gets its own sub-package here as it is
implemented. Under `FIDC/` live the document dumps
(:mod:`filings_cvm.ingestion.fidc.doc`), today the Informe Mensal FIDC, plus its META reader.
Every reader is re-exported flat from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fidc.doc import (
	InfMensalFidcTabIIIReader,
	InfMensalFidcTabIIReader,
	InfMensalFidcTabIReader,
	InfMensalFidcTabIVReader,
	InfMensalFidcTabIXReader,
	InfMensalFidcTabVIIReader,
	InfMensalFidcTabVIReader,
	InfMensalFidcTabVReader,
	InfMensalFidcTabX1Reader,
	InfMensalFidcTabX2Reader,
	InfMensalFidcTabX3Reader,
	InfMensalFidcTabX4Reader,
	InfMensalFidcTabX5Reader,
	InfMensalFidcTabX6Reader,
	InfMensalFidcTabX7Reader,
	InfMensalFidcTabX11Reader,
	InfMensalFidcTabXReader,
	MetaInfMensalFidcReader,
)


__all__ = [
	"InfMensalFidcTabIIIReader",
	"InfMensalFidcTabIIReader",
	"InfMensalFidcTabIReader",
	"InfMensalFidcTabIVReader",
	"InfMensalFidcTabIXReader",
	"InfMensalFidcTabVIIReader",
	"InfMensalFidcTabVIReader",
	"InfMensalFidcTabVReader",
	"InfMensalFidcTabX11Reader",
	"InfMensalFidcTabX1Reader",
	"InfMensalFidcTabX2Reader",
	"InfMensalFidcTabX3Reader",
	"InfMensalFidcTabX4Reader",
	"InfMensalFidcTabX5Reader",
	"InfMensalFidcTabX6Reader",
	"InfMensalFidcTabX7Reader",
	"InfMensalFidcTabXReader",
	"MetaInfMensalFidcReader",
]
