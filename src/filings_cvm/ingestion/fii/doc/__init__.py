"""CVM open-data **document-dump** readers for FII (`FII/DOC/*`).

The FII portal root holds only document dumps (there is no `FII/CAD`). Today the Informe Mensal
(`INF_MENSAL`, 3 members), the DFIN index (`DFIN`,
:mod:`filings_cvm.ingestion.fii.doc.dfin`) and the Informe Trimestral (`INF_TRIMESTRAL`, 16
members, :mod:`filings_cvm.ingestion.fii.doc.inf_trimestral`); the `INF_ANUAL` dataset lands as a
sibling. Re-exported from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fii.doc.dfin import DfinFiiReader
from filings_cvm.ingestion.fii.doc.inf_mensal import (
	InfMensalFiiAtivoPassivoReader,
	InfMensalFiiComplementoReader,
	InfMensalFiiGeralReader,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral import (
	InfTrimestralFiiAlienacaoImovelReader,
	InfTrimestralFiiAlienacaoTerrenoReader,
	InfTrimestralFiiAquisicaoImovelReader,
	InfTrimestralFiiAquisicaoTerrenoReader,
	InfTrimestralFiiAtivoGarantiaRentabilidadeReader,
	InfTrimestralFiiAtivoReader,
	InfTrimestralFiiComplementoReader,
	InfTrimestralFiiDireitoReader,
	InfTrimestralFiiGeralReader,
	InfTrimestralFiiImovelDesempenhoReader,
	InfTrimestralFiiImovelReader,
	InfTrimestralFiiImovelRendaAcabadoContratoReader,
	InfTrimestralFiiImovelRendaAcabadoInquilinoReader,
	InfTrimestralFiiRentabilidadeEfetivaReader,
	InfTrimestralFiiResultadoContabilFinanceiroReader,
	InfTrimestralFiiTerrenoReader,
)


__all__ = [
	"DfinFiiReader",
	"InfMensalFiiAtivoPassivoReader",
	"InfMensalFiiComplementoReader",
	"InfMensalFiiGeralReader",
	"InfTrimestralFiiAlienacaoImovelReader",
	"InfTrimestralFiiAlienacaoTerrenoReader",
	"InfTrimestralFiiAquisicaoImovelReader",
	"InfTrimestralFiiAquisicaoTerrenoReader",
	"InfTrimestralFiiAtivoGarantiaRentabilidadeReader",
	"InfTrimestralFiiAtivoReader",
	"InfTrimestralFiiComplementoReader",
	"InfTrimestralFiiDireitoReader",
	"InfTrimestralFiiGeralReader",
	"InfTrimestralFiiImovelDesempenhoReader",
	"InfTrimestralFiiImovelReader",
	"InfTrimestralFiiImovelRendaAcabadoContratoReader",
	"InfTrimestralFiiImovelRendaAcabadoInquilinoReader",
	"InfTrimestralFiiRentabilidadeEfetivaReader",
	"InfTrimestralFiiResultadoContabilFinanceiroReader",
	"InfTrimestralFiiTerrenoReader",
]
