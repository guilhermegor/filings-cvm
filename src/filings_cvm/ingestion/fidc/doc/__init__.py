"""CVM open-data **document-dump** readers for FIDC (`FIDC/DOC/*`).

Today the monthly Informe Mensal FIDC (`INF_MENSAL`), nested in
:mod:`filings_cvm.ingestion.fidc.doc.inf_mensal` (17 table members), plus its META reader.
Re-exported from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fidc.doc.inf_mensal import (
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
