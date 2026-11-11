"""CVM open-data **document-dump** readers for FIDC (`FIDC/DOC/*`).

Today the monthly Informe Mensal FIDC (`INF_MENSAL`), nested in
:mod:`opendata_cvm.ingestion.fidc.doc.inf_mensal` (18 table members), plus its META reader.
Re-exported from `opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.fidc.doc.inf_mensal import (
	InfMensalFidcTabIIIReader,
	InfMensalFidcTabIIReader,
	InfMensalFidcTabIReader,
	InfMensalFidcTabIVReader,
	InfMensalFidcTabIXReader,
	InfMensalFidcTabVIIIReader,
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
	"InfMensalFidcTabVIIIReader",
	"InfMensalFidcTabVIIReader",
	"InfMensalFidcTabVIReader",
	"InfMensalFidcTabVReader",
	"InfMensalFidcTabX1Reader",
	"InfMensalFidcTabX2Reader",
	"InfMensalFidcTabX3Reader",
	"InfMensalFidcTabX4Reader",
	"InfMensalFidcTabX5Reader",
	"InfMensalFidcTabX6Reader",
	"InfMensalFidcTabX7Reader",
	"InfMensalFidcTabX11Reader",
	"InfMensalFidcTabXReader",
	"MetaInfMensalFidcReader",
]
