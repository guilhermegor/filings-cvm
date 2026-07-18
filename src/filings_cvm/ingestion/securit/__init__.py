"""CVM open-data **Securitização** readers (`SECURIT/`).

Mirrors the `dados.cvm.gov.br/dados/SECURIT/` portal branch — one sibling among the portal's other
roots (`FI/`, `FIDC/`, `FII/`, `FIP/`, `FIAGRO/`, `FIE/`, …). Under `SECURIT/` live the document
dumps (:mod:`filings_cvm.ingestion.securit.doc`): the DFIN CRA/CRI indexes and the monthly reports
of the CRA (8 members), the non-CRA/CRI (`INF_MENSAL_OTS`, 8 members) and the CRI
(`INF_MENSAL_CRI`, 11 members) operations. Every reader, plus its META reader, is re-exported flat
from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.securit.doc import (
	DfinCraReader,
	DfinCriReader,
	InfMensalCraAtivoPassivoReader,
	InfMensalCraCedenteDevedorReader,
	InfMensalCraClasseReader,
	InfMensalCraDerivativosReader,
	InfMensalCraDesembolsoReader,
	InfMensalCraDireitosCreditoriosReader,
	InfMensalCraFluxoCaixaReader,
	InfMensalCraGeralReader,
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
	InfMensalOtsAtivoPassivoReader,
	InfMensalOtsCedenteDevedorReader,
	InfMensalOtsClasseReader,
	InfMensalOtsDerivativosReader,
	InfMensalOtsDesembolsoReader,
	InfMensalOtsDireitosCreditoriosReader,
	InfMensalOtsFluxoCaixaReader,
	InfMensalOtsGeralReader,
	MetaDfinCraReader,
	MetaDfinCriReader,
	MetaInfMensalCraReader,
	MetaInfMensalCriReader,
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
