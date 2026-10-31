"""Submission section — build and serialise files to *send* to CVM (envio).

Every "envio" solution lives here: it takes validated schema models (or a filled
spreadsheet) and produces a CVM-compliant file ready to submit. The reading/parsing
counterpart lives in the ``ingestion`` section.

The shared XML-standard models are re-exported here so callers construct documents
and serialise them through a single import:

    from filings_cvm.submission import PerfilMensal, PerfilMensalDocument
"""

from filings_cvm._internal.config.schemas.inf_fundo_157 import (
	InfFundo157Cotista,
	InfFundo157Document,
	InfFundo157Header,
)
from filings_cvm._internal.config.schemas.informe_diario import (
	InformeDiarioDocument,
	InformeDiarioHeader,
	InformeDiarioInform,
	SignificantShareholder,
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
from filings_cvm.submission.inf_fundo_157 import InfFundo157
from filings_cvm.submission.informe_diario import InformeDiario
from filings_cvm.submission.perfil_mensal import PerfilMensal


__all__ = [
	"ClientCount",
	"DocumentHeader",
	"InfFundo157",
	"InfFundo157Cotista",
	"InfFundo157Document",
	"InfFundo157Header",
	"InformeDiario",
	"InformeDiarioDocument",
	"InformeDiarioHeader",
	"InformeDiarioInform",
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
