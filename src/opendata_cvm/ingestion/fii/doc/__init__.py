"""CVM open-data **document-dump** readers for FII (`FII/DOC/*`).

The FII portal root holds only document dumps (there is no `FII/CAD`), and **all four of its
datasets are implemented**: the Informe Mensal (`INF_MENSAL`, 3 members), the DFIN index (`DFIN`,
:mod:`opendata_cvm.ingestion.fii.doc.dfin`), the Informe Trimestral (`INF_TRIMESTRAL`, 16 members,
:mod:`opendata_cvm.ingestion.fii.doc.inf_trimestral`) and the Informe Anual (`INF_ANUAL`, 12
members, :mod:`opendata_cvm.ingestion.fii.doc.inf_anual`), plus their META readers. Re-exported
from `opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.fii.doc.dfin import DfinFiiReader, MetaDfinFiiReader
from opendata_cvm.ingestion.fii.doc.inf_anual import (
	InfAnualFiiAtivoAdquiridoReader,
	InfAnualFiiAtivoTransacaoReader,
	InfAnualFiiAtivoValorContabilReader,
	InfAnualFiiComplementoReader,
	InfAnualFiiDiretorResponsavelReader,
	InfAnualFiiDistribuicaoCotistasReader,
	InfAnualFiiExperienciaProfissionalReader,
	InfAnualFiiGeralReader,
	InfAnualFiiPrestadorServicoReader,
	InfAnualFiiProcessoReader,
	InfAnualFiiProcessoSemelhanteReader,
	InfAnualFiiRepresentanteCotistaReader,
	MetaInfAnualFiiReader,
)
from opendata_cvm.ingestion.fii.doc.inf_mensal import (
	InfMensalFiiAtivoPassivoReader,
	InfMensalFiiComplementoReader,
	InfMensalFiiGeralReader,
	MetaInfMensalFiiReader,
)
from opendata_cvm.ingestion.fii.doc.inf_trimestral import (
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
	MetaInfTrimestralFiiReader,
)


__all__ = [
	"DfinFiiReader",
	"InfAnualFiiAtivoAdquiridoReader",
	"InfAnualFiiAtivoTransacaoReader",
	"InfAnualFiiAtivoValorContabilReader",
	"InfAnualFiiComplementoReader",
	"InfAnualFiiDiretorResponsavelReader",
	"InfAnualFiiDistribuicaoCotistasReader",
	"InfAnualFiiExperienciaProfissionalReader",
	"InfAnualFiiGeralReader",
	"InfAnualFiiPrestadorServicoReader",
	"InfAnualFiiProcessoReader",
	"InfAnualFiiProcessoSemelhanteReader",
	"InfAnualFiiRepresentanteCotistaReader",
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
	"MetaDfinFiiReader",
	"MetaInfAnualFiiReader",
	"MetaInfMensalFiiReader",
	"MetaInfTrimestralFiiReader",
]
