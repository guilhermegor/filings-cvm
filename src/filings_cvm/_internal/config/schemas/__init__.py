"""Shared XML-standard schemas (Pydantic models) for the CVM file standards.

Direction-neutral contracts consumed by both the ``submission`` section (models →
XML) and the future ``ingestion`` section (XML → models). One module per CVM
standard. Ships in the wheel under ``_internal``; the public API is curated by the
``submission``/``ingestion`` packages, which re-export the names consumers need.
"""

from filings_cvm._internal.config.schemas.far import (
	FarDocument,
	FarFund,
	FarHeader,
	FarMovement,
)
from filings_cvm._internal.config.schemas.lamina import (
	LaminaAntesInic2,
	LaminaCarencia,
	LaminaCompCarteira,
	LaminaConversao,
	LaminaDespesas,
	LaminaDocument,
	LaminaHeader,
	LaminaInform,
	LaminaInformExemploComp,
	LaminaInforTabRentAnual,
	LaminaListaCompCarteira,
	LaminaListaTabRentAnual,
	LaminaListaTabRentMensal,
	LaminaTabRentAnual,
	LaminaTabRentMensal,
	LaminaTabSimulDespesas,
	LaminaTabVarDesemp,
	LaminaTaxaAdministracao,
	LaminaTaxaEntrada,
	LaminaTaxaSaida,
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


__all__ = [
	"ClientCount",
	"DocumentHeader",
	"FarDocument",
	"FarFund",
	"FarHeader",
	"FarMovement",
	"LaminaAntesInic2",
	"LaminaCarencia",
	"LaminaCompCarteira",
	"LaminaConversao",
	"LaminaDespesas",
	"LaminaDocument",
	"LaminaHeader",
	"LaminaInforTabRentAnual",
	"LaminaInform",
	"LaminaInformExemploComp",
	"LaminaListaCompCarteira",
	"LaminaListaTabRentAnual",
	"LaminaListaTabRentMensal",
	"LaminaTabRentAnual",
	"LaminaTabRentMensal",
	"LaminaTabSimulDespesas",
	"LaminaTabVarDesemp",
	"LaminaTaxaAdministracao",
	"LaminaTaxaEntrada",
	"LaminaTaxaSaida",
	"NominalRiskBlock",
	"NominalRiskFactor",
	"OtcOperation",
	"PatrimonyDistribution",
	"PerfilMensalDocument",
	"PerfilMensalRow",
	"PerformanceFeeDetails",
	"PrimitiveRiskFactor",
	"PrivateCreditIssuer",
	"VarOutros",
	"VarPercValCota",
]
