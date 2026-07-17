"""CVM open-data **document-dump** readers for Securitização (`SECURIT/DOC/*`).

Two DFIN indexes — of CRA (`DFIN_CRA`, :mod:`filings_cvm.ingestion.securit.doc.dfin_cra`) and CRI
(`DFIN_CRI`, :mod:`filings_cvm.ingestion.securit.doc.dfin_cri`) financial statements, both flat
year-partitioned CSVs — plus the monthly report of the non-CRA/CRI operations (`INF_MENSAL_OTS`,
:mod:`filings_cvm.ingestion.securit.doc.inf_mensal_ots`, 8 section members over a private base).
The `INF_MENSAL_CRI` dump lands as a later PR. Every reader, plus its META reader, is re-exported
from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.securit.doc.dfin_cra import DfinCraReader, MetaDfinCraReader
from filings_cvm.ingestion.securit.doc.dfin_cri import DfinCriReader, MetaDfinCriReader
from filings_cvm.ingestion.securit.doc.inf_mensal_cra import (
	InfMensalCraAtivoPassivoReader,
	InfMensalCraCedenteDevedorReader,
	InfMensalCraClasseReader,
	InfMensalCraDerivativosReader,
	InfMensalCraDesembolsoReader,
	InfMensalCraDireitosCreditoriosReader,
	InfMensalCraFluxoCaixaReader,
	InfMensalCraGeralReader,
	MetaInfMensalCraReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_ots import (
	InfMensalOtsAtivoPassivoReader,
	InfMensalOtsCedenteDevedorReader,
	InfMensalOtsClasseReader,
	InfMensalOtsDerivativosReader,
	InfMensalOtsDesembolsoReader,
	InfMensalOtsDireitosCreditoriosReader,
	InfMensalOtsFluxoCaixaReader,
	InfMensalOtsGeralReader,
	MetaInfMensalOtsReader,
)


__all__ = [
	"DfinCraReader",
	"DfinCriReader",
	"InfMensalCraAtivoPassivoReader",
	"InfMensalCraCedenteDevedorReader",
	"InfMensalCraClasseReader",
	"InfMensalCraDerivativosReader",
	"InfMensalCraDesembolsoReader",
	"InfMensalCraDireitosCreditoriosReader",
	"InfMensalCraFluxoCaixaReader",
	"InfMensalCraGeralReader",
	"InfMensalOtsAtivoPassivoReader",
	"InfMensalOtsCedenteDevedorReader",
	"InfMensalOtsClasseReader",
	"InfMensalOtsDerivativosReader",
	"InfMensalOtsDesembolsoReader",
	"InfMensalOtsDireitosCreditoriosReader",
	"InfMensalOtsFluxoCaixaReader",
	"InfMensalOtsGeralReader",
	"MetaDfinCraReader",
	"MetaDfinCriReader",
	"MetaInfMensalCraReader",
	"MetaInfMensalOtsReader",
]
