"""Submission section — build and serialise files to *send* to CVM (envio).

Every "envio" solution lives here: it takes validated schema models (or a filled
spreadsheet) and produces a CVM-compliant file ready to submit. The reading/parsing
counterpart lives in the ``ingestion`` section.

The shared XML-standard models are re-exported here so callers construct documents
and serialise them through a single import:

    from filings_cvm.submission import PerfilMensal, PerfilMensalDocument
"""

from filings_cvm._internal.config.schemas.informe_diario import (
	InformeDiarioDocument,
	InformeDiarioHeader,
	InformeDiarioInform,
	SignificantShareholder,
)
from filings_cvm._internal.config.schemas.inr_semestral import (
	InrAtivoExterior,
	InrClassifRisco,
	InrCotas,
	InrDemaisCodif,
	InrDemaisNCodif,
	InrDepPrazoTitIf,
	InrEmissorPfPj,
	InrEmissorPj,
	InrEntradaSaida,
	InrIndexador,
	InrInform,
	InrInvExt,
	InrParte1Document,
	InrParte1Header,
	InrParte2Document,
	InrParte2Header,
	InrParticipante,
	InrPosFim,
	InrPosFimNocional,
	InrRecursoEnviado,
	InrRecursoRecebido,
	InrRecursosEntreInvestidores,
	InrSwap,
	InrTitAgroCredPriv,
	InrTitPub,
	InrTransfRecursos,
)
from filings_cvm._internal.config.schemas.perfil_mensal import (
	ClientCount,
	DocumentHeader,
	NominalRiskBlock,
	NominalRiskFactor,
	OtcOperation,
	PatrimonyDistribution,
	PerfilMensalDocument,
	PerfilMensalRow,
	PerformanceFeeDetails,
	PrimitiveRiskFactor,
	PrivateCreditIssuer,
	VarOutros,
	VarPercValCota,
)
from filings_cvm.submission.informe_diario import InformeDiario
from filings_cvm.submission.inr_semestral_parte1 import InrSemestralParte1
from filings_cvm.submission.inr_semestral_parte2 import InrSemestralParte2
from filings_cvm.submission.perfil_mensal import PerfilMensal


__all__ = [
	"ClientCount",
	"DocumentHeader",
	"InformeDiario",
	"InformeDiarioDocument",
	"InformeDiarioHeader",
	"InformeDiarioInform",
	"InrAtivoExterior",
	"InrClassifRisco",
	"InrCotas",
	"InrDemaisCodif",
	"InrDemaisNCodif",
	"InrDepPrazoTitIf",
	"InrEmissorPfPj",
	"InrEmissorPj",
	"InrEntradaSaida",
	"InrIndexador",
	"InrInform",
	"InrInvExt",
	"InrParte1Document",
	"InrParte1Header",
	"InrParte2Document",
	"InrParte2Header",
	"InrParticipante",
	"InrPosFim",
	"InrPosFimNocional",
	"InrRecursoEnviado",
	"InrRecursoRecebido",
	"InrRecursosEntreInvestidores",
	"InrSemestralParte1",
	"InrSemestralParte2",
	"InrSwap",
	"InrTitAgroCredPriv",
	"InrTitPub",
	"InrTransfRecursos",
	"NominalRiskBlock",
	"NominalRiskFactor",
	"OtcOperation",
	"PatrimonyDistribution",
	"PerfilMensal",
	"PerfilMensalDocument",
	"PerfilMensalRow",
	"PerformanceFeeDetails",
	"PrimitiveRiskFactor",
	"PrivateCreditIssuer",
	"SignificantShareholder",
	"VarOutros",
	"VarPercValCota",
]
