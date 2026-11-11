"""CVM Informe Mensal OTS readers — the 8 section members of ``inf_mensal_ots_AAAA.zip``.

One reader per section of the monthly report of the *Operações de Securitização* that are neither
CRA nor CRI (geral, ativo/passivo, classe, direitos creditórios, desembolso, fluxo de caixa,
derivativos, cedente/devedor), over a shared private base (`_base_inf_mensal_ots_reader`).
⚠️ The dump is **yearly-partitioned** despite the monthly report. Plus its META reader.
Re-exported from `opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.securit.doc.inf_mensal_ots.inf_mensal_ots_ativo_passivo import (
	InfMensalOtsAtivoPassivoReader,
)
from opendata_cvm.ingestion.securit.doc.inf_mensal_ots.inf_mensal_ots_cedente_devedor import (
	InfMensalOtsCedenteDevedorReader,
)
from opendata_cvm.ingestion.securit.doc.inf_mensal_ots.inf_mensal_ots_classe import (
	InfMensalOtsClasseReader,
)
from opendata_cvm.ingestion.securit.doc.inf_mensal_ots.inf_mensal_ots_derivativos import (
	InfMensalOtsDerivativosReader,
)
from opendata_cvm.ingestion.securit.doc.inf_mensal_ots.inf_mensal_ots_desembolso import (
	InfMensalOtsDesembolsoReader,
)
from opendata_cvm.ingestion.securit.doc.inf_mensal_ots.inf_mensal_ots_direitos_creditorios import (
	InfMensalOtsDireitosCreditoriosReader,
)
from opendata_cvm.ingestion.securit.doc.inf_mensal_ots.inf_mensal_ots_fluxo_caixa import (
	InfMensalOtsFluxoCaixaReader,
)
from opendata_cvm.ingestion.securit.doc.inf_mensal_ots.inf_mensal_ots_geral import (
	InfMensalOtsGeralReader,
)
from opendata_cvm.ingestion.securit.doc.inf_mensal_ots.meta import MetaInfMensalOtsReader


__all__ = [
	"InfMensalOtsAtivoPassivoReader",
	"InfMensalOtsCedenteDevedorReader",
	"InfMensalOtsClasseReader",
	"InfMensalOtsDerivativosReader",
	"InfMensalOtsDesembolsoReader",
	"InfMensalOtsDireitosCreditoriosReader",
	"InfMensalOtsFluxoCaixaReader",
	"InfMensalOtsGeralReader",
	"MetaInfMensalOtsReader",
]
