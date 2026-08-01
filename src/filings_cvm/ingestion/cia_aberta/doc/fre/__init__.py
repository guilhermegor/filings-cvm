"""CVM open-data **FRE** readers for publicly held companies (`CIA_ABERTA/DOC/FRE`).

*Formulário de Referência* — the portal's largest dataset (36 members, ~131k rows), implemented
in four themed slices. This package currently ships the **index + capital-structure** and
**administração/pessoas** slices plus the META reader; the diversidade and remuneração slices
follow. Re-exported from `filings_cvm.ingestion`.

⚠️ The administração/pessoas slice holds **every CPF-bearing member of the dataset**. Personal
data is returned exactly as published and never validated as a company identifier; see each
module's docstring for what its columns actually contain.
"""

from filings_cvm.ingestion.cia_aberta.doc.fre.administrador_membro_conselho_fiscal import (
	FreCiaAbertaAdministradorMembroConselhoFiscalReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.auditor import FreCiaAbertaAuditorReader
from filings_cvm.ingestion.cia_aberta.doc.fre.capital_social import FreCiaAbertaCapitalSocialReader
from filings_cvm.ingestion.cia_aberta.doc.fre.capital_social_classe_acao import (
	FreCiaAbertaCapitalSocialClasseAcaoReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.capital_social_titulo_conversivel import (
	FreCiaAbertaCapitalSocialTituloConversivelReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.distribuicao_capital import (
	FreCiaAbertaDistribuicaoCapitalReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.distribuicao_capital_classe_acao import (
	FreCiaAbertaDistribuicaoCapitalClasseAcaoReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.fre import FreCiaAbertaReader
from filings_cvm.ingestion.cia_aberta.doc.fre.membro_comite import FreCiaAbertaMembroComiteReader
from filings_cvm.ingestion.cia_aberta.doc.fre.mercado_estrangeiro import (
	FreCiaAbertaMercadoEstrangeiroReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.meta import MetaFreCiaAbertaReader
from filings_cvm.ingestion.cia_aberta.doc.fre.posicao_acionaria import (
	FreCiaAbertaPosicaoAcionariaReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.posicao_acionaria_classe_acao import (
	FreCiaAbertaPosicaoAcionariaClasseAcaoReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.relacao_familiar import (
	FreCiaAbertaRelacaoFamiliarReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.relacao_subordinacao import (
	FreCiaAbertaRelacaoSubordinacaoReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.responsavel import FreCiaAbertaResponsavelReader


__all__ = [
	"FreCiaAbertaAdministradorMembroConselhoFiscalReader",
	"FreCiaAbertaAuditorReader",
	"FreCiaAbertaCapitalSocialClasseAcaoReader",
	"FreCiaAbertaCapitalSocialReader",
	"FreCiaAbertaCapitalSocialTituloConversivelReader",
	"FreCiaAbertaDistribuicaoCapitalClasseAcaoReader",
	"FreCiaAbertaDistribuicaoCapitalReader",
	"FreCiaAbertaMembroComiteReader",
	"FreCiaAbertaMercadoEstrangeiroReader",
	"FreCiaAbertaPosicaoAcionariaClasseAcaoReader",
	"FreCiaAbertaPosicaoAcionariaReader",
	"FreCiaAbertaReader",
	"FreCiaAbertaRelacaoFamiliarReader",
	"FreCiaAbertaRelacaoSubordinacaoReader",
	"FreCiaAbertaResponsavelReader",
	"MetaFreCiaAbertaReader",
]
