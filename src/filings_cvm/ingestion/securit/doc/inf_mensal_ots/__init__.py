"""CVM Informe Mensal OTS readers — the 8 section members of ``inf_mensal_ots_AAAA.zip``.

One reader per section of the monthly report of the *Operações de Securitização* that are neither
CRA nor CRI (geral, ativo/passivo, classe, direitos creditórios, desembolso, fluxo de caixa,
derivativos, cedente/devedor), over a shared private base (`_base_inf_mensal_ots_reader`).
⚠️ The dump is **yearly-partitioned** despite the monthly report. Re-exported from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.securit.doc.inf_mensal_ots.inf_mensal_ots_ativo_passivo import (
	InfMensalOtsAtivoPassivoReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_ots.inf_mensal_ots_cedente_devedor import (
	InfMensalOtsCedenteDevedorReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_ots.inf_mensal_ots_classe import (
	InfMensalOtsClasseReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_ots.inf_mensal_ots_derivativos import (
	InfMensalOtsDerivativosReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_ots.inf_mensal_ots_desembolso import (
	InfMensalOtsDesembolsoReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_ots.inf_mensal_ots_direitos_creditorios import (
	InfMensalOtsDireitosCreditoriosReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_ots.inf_mensal_ots_fluxo_caixa import (
	InfMensalOtsFluxoCaixaReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_ots.inf_mensal_ots_geral import (
	InfMensalOtsGeralReader,
)


__all__ = [
	"InfMensalOtsAtivoPassivoReader",
	"InfMensalOtsCedenteDevedorReader",
	"InfMensalOtsClasseReader",
	"InfMensalOtsDerivativosReader",
	"InfMensalOtsDesembolsoReader",
	"InfMensalOtsDireitosCreditoriosReader",
	"InfMensalOtsFluxoCaixaReader",
	"InfMensalOtsGeralReader",
]
