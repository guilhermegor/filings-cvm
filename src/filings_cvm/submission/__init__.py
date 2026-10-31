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
from filings_cvm._internal.config.schemas.inr_mensal import (
	Aplicacoes,
	EntradaSaida,
	InrMensalDocument,
	InrMensalHeader,
	MovRecursos,
	Participante,
	RecursosEnvMesmoInvest,
	RecursosEnvOutroInvest,
	RecursosMesmoInvest,
	RecursosOutroInvest,
	RecursosRecebMesmoInvest,
	RecursosRecebOutroInvest,
	TransfRecursos,
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
from filings_cvm.submission.inr_mensal import InrMensal
from filings_cvm.submission.perfil_mensal import PerfilMensal


__all__ = [
	"Aplicacoes",
	"ClientCount",
	"DocumentHeader",
	"EntradaSaida",
	"InformeDiario",
	"InformeDiarioDocument",
	"InformeDiarioHeader",
	"InformeDiarioInform",
	"InrMensal",
	"InrMensalDocument",
	"InrMensalHeader",
	"MovRecursos",
	"NominalRiskBlock",
	"NominalRiskFactor",
	"OtcOperation",
	"Participante",
	"PatrimonyDistribution",
	"PerfilMensal",
	"PerfilMensalDocument",
	"PerfilMensalRow",
	"PerformanceFeeDetails",
	"PrimitiveRiskFactor",
	"PrivateCreditIssuer",
	"RecursosEnvMesmoInvest",
	"RecursosEnvOutroInvest",
	"RecursosMesmoInvest",
	"RecursosOutroInvest",
	"RecursosRecebMesmoInvest",
	"RecursosRecebOutroInvest",
	"SignificantShareholder",
	"TransfRecursos",
	"VarOutros",
	"VarPercValCota",
]
