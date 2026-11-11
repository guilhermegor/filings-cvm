"""CVM open-data **document-dump** readers for Securitização (`SECURIT/DOC/*`).

Two DFIN indexes — of CRA (`DFIN_CRA`, :mod:`opendata_cvm.ingestion.securit.doc.dfin_cra`) and CRI
(`DFIN_CRI`, :mod:`opendata_cvm.ingestion.securit.doc.dfin_cri`) financial statements, both flat
year-partitioned CSVs — plus the monthly report of the non-CRA/CRI operations (`INF_MENSAL_OTS`,
:mod:`opendata_cvm.ingestion.securit.doc.inf_mensal_ots`, 8 section members over a private base)
and of the CRI operations (`INF_MENSAL_CRI`,
:mod:`opendata_cvm.ingestion.securit.doc.inf_mensal_cri`, 11 section members over a private base).
With `INF_MENSAL_CRI` the `securit/` root is complete (4/4).
Every reader, plus its META reader, is re-exported from `opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.securit.doc.dfin_cra import DfinCraReader, MetaDfinCraReader
from opendata_cvm.ingestion.securit.doc.dfin_cri import DfinCriReader, MetaDfinCriReader
from opendata_cvm.ingestion.securit.doc.inf_mensal_cra import (
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
from opendata_cvm.ingestion.securit.doc.inf_mensal_cri import (
	InfMensalCriAtivoPassivoReader,
	InfMensalCriCarteiraModificacaoReader,
	InfMensalCriCarteiraReader,
	InfMensalCriCedenteDevedorReader,
	InfMensalCriClasseReader,
	InfMensalCriCreditosReader,
	InfMensalCriDerivativosReader,
	InfMensalCriDesembolsoReader,
	InfMensalCriFluxoCaixaReader,
	InfMensalCriGeralReader,
	InfMensalCriResponsavelReader,
	MetaInfMensalCriReader,
)
from opendata_cvm.ingestion.securit.doc.inf_mensal_ots import (
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
	"InfMensalCriAtivoPassivoReader",
	"InfMensalCriCarteiraModificacaoReader",
	"InfMensalCriCarteiraReader",
	"InfMensalCriCedenteDevedorReader",
	"InfMensalCriClasseReader",
	"InfMensalCriCreditosReader",
	"InfMensalCriDerivativosReader",
	"InfMensalCriDesembolsoReader",
	"InfMensalCriFluxoCaixaReader",
	"InfMensalCriGeralReader",
	"InfMensalCriResponsavelReader",
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
	"MetaInfMensalCriReader",
	"MetaInfMensalOtsReader",
]
