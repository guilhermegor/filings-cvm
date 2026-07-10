"""Shared XML-standard schemas (Pydantic models) for the CVM file standards.

Direction-neutral contracts consumed by both the ``submission`` section (models →
XML) and the future ``ingestion`` section (XML → models). One module per CVM
standard. Ships in the wheel under ``_internal``; the public API is curated by the
``submission``/``ingestion`` packages, which re-export the names consumers need.
"""

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
