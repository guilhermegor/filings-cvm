"""CVM open-data **Securitização** readers (`SECURIT/`).

Mirrors the `dados.cvm.gov.br/dados/SECURIT/` portal branch — one sibling among the portal's other
roots (`FI/`, `FIDC/`, `FII/`, `FIP/`, `FIAGRO/`, `FIE/`, …). Under `SECURIT/` live the document
dumps (:mod:`filings_cvm.ingestion.securit.doc`): the DFIN CRA/CRI indexes and the 8-member monthly
reports of the CRA and non-CRA/CRI (`INF_MENSAL_OTS`) operations. Every reader, plus its META
reader, is re-exported flat from `filings_cvm.ingestion`.
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
