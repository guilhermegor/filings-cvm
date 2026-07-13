"""CVM open-data **document-dump** readers for Securitização (`SECURIT/DOC/*`).

Two DFIN indexes — of CRA (`DFIN_CRA`, :mod:`filings_cvm.ingestion.securit.doc.dfin_cra`) and CRI
(`DFIN_CRI`, :mod:`filings_cvm.ingestion.securit.doc.dfin_cri`) financial statements, both flat
year-partitioned CSVs — plus the monthly report of the non-CRA/CRI operations (`INF_MENSAL_OTS`,
:mod:`filings_cvm.ingestion.securit.doc.inf_mensal_ots`, 8 section members over a private base).
The `INF_MENSAL_CRA` / `INF_MENSAL_CRI` dumps land as later PRs. Re-exported from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.securit.doc.dfin_cra import DfinCraReader
from filings_cvm.ingestion.securit.doc.dfin_cri import DfinCriReader
from filings_cvm.ingestion.securit.doc.inf_mensal_ots import (
	InfMensalOtsAtivoPassivoReader,
	InfMensalOtsCedenteDevedorReader,
	InfMensalOtsClasseReader,
	InfMensalOtsDerivativosReader,
	InfMensalOtsDesembolsoReader,
	InfMensalOtsDireitosCreditoriosReader,
	InfMensalOtsFluxoCaixaReader,
	InfMensalOtsGeralReader,
)


__all__ = [
	"DfinCraReader",
	"DfinCriReader",
	"InfMensalOtsAtivoPassivoReader",
	"InfMensalOtsCedenteDevedorReader",
	"InfMensalOtsClasseReader",
	"InfMensalOtsDerivativosReader",
	"InfMensalOtsDesembolsoReader",
	"InfMensalOtsDireitosCreditoriosReader",
	"InfMensalOtsFluxoCaixaReader",
	"InfMensalOtsGeralReader",
]
