"""CVM Informe Mensal CRI readers — the 11 section members of ``inf_mensal_cri_AAAA.zip``.

One reader per section of the monthly report of the **CRI** (*Certificado de Recebíveis
Imobiliários*) operations (geral, ativo/passivo, classe, créditos, carteira, modificação de
carteira, desembolso, fluxo de caixa, derivativos, cedente/devedor, responsável), over a shared
private base (`_base_inf_mensal_cri_reader`). ⚠️ The dump is **yearly-partitioned** despite the
monthly report, and — despite sharing seven section names with CRA/OTS — CRI is real-estate: it has
**no ``direitos_creditorios``** (``creditos`` instead) and **adds four members** (``carteira``,
``carteira_modificacao``, ``creditos``, ``responsavel``). Plus its META reader. With this the
`securit/` root is complete (4/4). Re-exported from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.securit.doc.inf_mensal_cri.inf_mensal_cri_ativo_passivo import (
	InfMensalCriAtivoPassivoReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_cri.inf_mensal_cri_carteira import (
	InfMensalCriCarteiraReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_cri.inf_mensal_cri_carteira_modificacao import (
	InfMensalCriCarteiraModificacaoReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_cri.inf_mensal_cri_cedente_devedor import (
	InfMensalCriCedenteDevedorReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_cri.inf_mensal_cri_classe import (
	InfMensalCriClasseReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_cri.inf_mensal_cri_creditos import (
	InfMensalCriCreditosReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_cri.inf_mensal_cri_derivativos import (
	InfMensalCriDerivativosReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_cri.inf_mensal_cri_desembolso import (
	InfMensalCriDesembolsoReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_cri.inf_mensal_cri_fluxo_caixa import (
	InfMensalCriFluxoCaixaReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_cri.inf_mensal_cri_geral import (
	InfMensalCriGeralReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_cri.inf_mensal_cri_responsavel import (
	InfMensalCriResponsavelReader,
)
from filings_cvm.ingestion.securit.doc.inf_mensal_cri.meta import MetaInfMensalCriReader


__all__ = [
	"InfMensalCriAtivoPassivoReader",
	"InfMensalCriCarteiraModificacaoReader",
	"InfMensalCriCarteiraReader",
	"InfMensalCriCedenteDevedorReader",
	"InfMensalCriClasseReader",
	"InfMensalCriCreditosReader",
	"InfMensalCriDerivativosReader",
	"InfMensalCriDesembolsoReader",
	"InfMensalCriFluxoCaixaReader",
	"InfMensalCriGeralReader",
	"InfMensalCriResponsavelReader",
	"MetaInfMensalCriReader",
]
