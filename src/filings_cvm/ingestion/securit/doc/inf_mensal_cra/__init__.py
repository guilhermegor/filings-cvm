"""CVM Informe Mensal CRA readers — the 8 section members of ``inf_mensal_cra_AAAA.zip``.

One reader per section of the monthly report of the **CRA** (*Certificado de Recebíveis do
Agronegócio*) operations (geral, ativo/passivo, classe, direitos creditórios, desembolso, fluxo de
caixa, derivativos, cedente/devedor), over a shared private base (`_base_inf_mensal_cra_reader`).
⚠️ The dump is **yearly-partitioned** despite the monthly report, and — despite sharing the OTS
section names — **none of the 8 column lists matches OTS's**. Re-exported from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.securit.doc.inf_mensal_cra.inf_mensal_cra_ativo_passivo import (
	InfMensalCraAtivoPassivoReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_cra.inf_mensal_cra_cedente_devedor import (
	InfMensalCraCedenteDevedorReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_cra.inf_mensal_cra_classe import (
	InfMensalCraClasseReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_cra.inf_mensal_cra_derivativos import (
	InfMensalCraDerivativosReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_cra.inf_mensal_cra_desembolso import (
	InfMensalCraDesembolsoReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_cra.inf_mensal_cra_direitos_creditorios import (
	InfMensalCraDireitosCreditoriosReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_cra.inf_mensal_cra_fluxo_caixa import (
	InfMensalCraFluxoCaixaReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_cra.inf_mensal_cra_geral import (
	InfMensalCraGeralReader,
)


__all__ = [
	"InfMensalCraAtivoPassivoReader",
	"InfMensalCraCedenteDevedorReader",
	"InfMensalCraClasseReader",
	"InfMensalCraDerivativosReader",
	"InfMensalCraDesembolsoReader",
	"InfMensalCraDireitosCreditoriosReader",
	"InfMensalCraFluxoCaixaReader",
	"InfMensalCraGeralReader",
]
