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
from filings_cvm._internal.config.schemas.informe_sintetico import (
	FcceAplicacoes,
	FcceAplicacoesPosFinal,
	FcceHeader,
	FcceInform,
	FcceOutras,
	FicAplicacoes,
	FicAplicacoesPosFinal,
	FicHeader,
	FicInform,
	FicOutras,
	FitvmAplicacoes,
	FitvmAplicacoesPosFinal,
	FitvmHeader,
	FitvmInform,
	FitvmOutras,
	InformeSinteticoFcceDocument,
	InformeSinteticoFicDocument,
	InformeSinteticoFitvmDocument,
	InformeSinteticoOutrosDocument,
	OutrosAplicacoes,
	OutrosAplicacoesPosFinal,
	OutrosHeader,
	OutrosInform,
	OutrosOutras,
	SinteticoContrFuturo,
	SinteticoDebt,
	SinteticoMercATermo,
	SinteticoMercOpcao,
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
from filings_cvm.submission.informe_sintetico_fcce import InformeSinteticoFcce
from filings_cvm.submission.informe_sintetico_fic import InformeSinteticoFic
from filings_cvm.submission.informe_sintetico_fitvm import InformeSinteticoFitvm
from filings_cvm.submission.informe_sintetico_outros import InformeSinteticoOutros
from filings_cvm.submission.perfil_mensal import PerfilMensal


__all__ = [
	"ClientCount",
	"DocumentHeader",
	"FcceAplicacoes",
	"FcceAplicacoesPosFinal",
	"FcceHeader",
	"FcceInform",
	"FcceOutras",
	"FicAplicacoes",
	"FicAplicacoesPosFinal",
	"FicHeader",
	"FicInform",
	"FicOutras",
	"FitvmAplicacoes",
	"FitvmAplicacoesPosFinal",
	"FitvmHeader",
	"FitvmInform",
	"FitvmOutras",
	"InformeDiario",
	"InformeDiarioDocument",
	"InformeDiarioHeader",
	"InformeDiarioInform",
	"InformeSinteticoFcce",
	"InformeSinteticoFcceDocument",
	"InformeSinteticoFic",
	"InformeSinteticoFicDocument",
	"InformeSinteticoFitvm",
	"InformeSinteticoFitvmDocument",
	"InformeSinteticoOutros",
	"InformeSinteticoOutrosDocument",
	"NominalRiskBlock",
	"NominalRiskFactor",
	"OtcOperation",
	"OutrosAplicacoes",
	"OutrosAplicacoesPosFinal",
	"OutrosHeader",
	"OutrosInform",
	"OutrosOutras",
	"PatrimonyDistribution",
	"PerfilMensal",
	"PerfilMensalDocument",
	"PerfilMensalRow",
	"PerformanceFeeDetails",
	"PrimitiveRiskFactor",
	"PrivateCreditIssuer",
	"SignificantShareholder",
	"SinteticoContrFuturo",
	"SinteticoDebt",
	"SinteticoMercATermo",
	"SinteticoMercOpcao",
	"VarOutros",
	"VarPercValCota",
]
