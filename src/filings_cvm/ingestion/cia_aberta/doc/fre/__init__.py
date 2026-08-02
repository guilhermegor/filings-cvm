"""CVM open-data **FRE** readers for publicly held companies (`CIA_ABERTA/DOC/FRE`).

*Formulário de Referência* — the portal's largest dataset (36 members, ~131k rows), implemented
in four themed slices. This package currently ships the **index + capital-structure** and
**administração/pessoas** slices plus the META reader; the diversidade and remuneração slices
follow. Re-exported from `filings_cvm.ingestion`.

⚠️ The administração/pessoas slice holds **every CPF-bearing member of the dataset**. Personal
data is returned exactly as published and never validated as a company identifier; see each
module's docstring for what its columns actually contain.
"""

from filings_cvm.ingestion.cia_aberta.doc.fre.acao_entregue import (
	FreCiaAbertaAcaoEntregueReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.administrador_declaracao_genero import (
	FreCiaAbertaAdministradorDeclaracaoGeneroReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.administrador_declaracao_raca import (
	FreCiaAbertaAdministradorDeclaracaoRacaReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.administrador_membro_conselho_fiscal import (
	FreCiaAbertaAdministradorMembroConselhoFiscalReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.administrador_pcd import (
	FreCiaAbertaAdministradorPcdReader,
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
from filings_cvm.ingestion.cia_aberta.doc.fre.empregado_local_declaracao_genero import (
	FreCiaAbertaEmpregadoLocalDeclaracaoGeneroReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.empregado_local_declaracao_raca import (
	FreCiaAbertaEmpregadoLocalDeclaracaoRacaReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.empregado_local_faixa_etaria import (
	FreCiaAbertaEmpregadoLocalFaixaEtariaReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.empregado_pcd import (
	FreCiaAbertaEmpregadoPcdReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.empregado_posicao_declaracao_genero import (
	FreCiaAbertaEmpregadoPosicaoDeclaracaoGeneroReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.empregado_posicao_declaracao_raca import (
	FreCiaAbertaEmpregadoPosicaoDeclaracaoRacaReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.empregado_posicao_faixa_etaria import (
	FreCiaAbertaEmpregadoPosicaoFaixaEtariaReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.empregado_posicao_local import (
	FreCiaAbertaEmpregadoPosicaoLocalReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.fre import FreCiaAbertaReader
from filings_cvm.ingestion.cia_aberta.doc.fre.membro_comite import FreCiaAbertaMembroComiteReader
from filings_cvm.ingestion.cia_aberta.doc.fre.mercado_estrangeiro import (
	FreCiaAbertaMercadoEstrangeiroReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.meta import MetaFreCiaAbertaReader
from filings_cvm.ingestion.cia_aberta.doc.fre.outro_valor_mobiliario import (
	FreCiaAbertaOutroValorMobiliarioReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.participacao_sociedade import (
	FreCiaAbertaParticipacaoSociedadeReader,
)
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
from filings_cvm.ingestion.cia_aberta.doc.fre.remuneracao_acao import (
	FreCiaAbertaRemuneracaoAcaoReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.remuneracao_maxima_minima_media import (
	FreCiaAbertaRemuneracaoMaximaMinimaMediaReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.remuneracao_total_orgao import (
	FreCiaAbertaRemuneracaoTotalOrgaoReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.remuneracao_variavel import (
	FreCiaAbertaRemuneracaoVariavelReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.responsavel import FreCiaAbertaResponsavelReader
from filings_cvm.ingestion.cia_aberta.doc.fre.titular_valor_mobiliario import (
	FreCiaAbertaTitularValorMobiliarioReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.titulo_exterior import (
	FreCiaAbertaTituloExteriorReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.transacao_parte_relacionada import (
	FreCiaAbertaTransacaoParteRelacionadaReader,
)


__all__ = [
	"FreCiaAbertaAcaoEntregueReader",
	"FreCiaAbertaAdministradorDeclaracaoGeneroReader",
	"FreCiaAbertaAdministradorDeclaracaoRacaReader",
	"FreCiaAbertaAdministradorMembroConselhoFiscalReader",
	"FreCiaAbertaAdministradorPcdReader",
	"FreCiaAbertaAuditorReader",
	"FreCiaAbertaCapitalSocialClasseAcaoReader",
	"FreCiaAbertaCapitalSocialReader",
	"FreCiaAbertaCapitalSocialTituloConversivelReader",
	"FreCiaAbertaDistribuicaoCapitalClasseAcaoReader",
	"FreCiaAbertaDistribuicaoCapitalReader",
	"FreCiaAbertaEmpregadoLocalDeclaracaoGeneroReader",
	"FreCiaAbertaEmpregadoLocalDeclaracaoRacaReader",
	"FreCiaAbertaEmpregadoLocalFaixaEtariaReader",
	"FreCiaAbertaEmpregadoPcdReader",
	"FreCiaAbertaEmpregadoPosicaoDeclaracaoGeneroReader",
	"FreCiaAbertaEmpregadoPosicaoDeclaracaoRacaReader",
	"FreCiaAbertaEmpregadoPosicaoFaixaEtariaReader",
	"FreCiaAbertaEmpregadoPosicaoLocalReader",
	"FreCiaAbertaMembroComiteReader",
	"FreCiaAbertaMercadoEstrangeiroReader",
	"FreCiaAbertaOutroValorMobiliarioReader",
	"FreCiaAbertaParticipacaoSociedadeReader",
	"FreCiaAbertaPosicaoAcionariaClasseAcaoReader",
	"FreCiaAbertaPosicaoAcionariaReader",
	"FreCiaAbertaReader",
	"FreCiaAbertaRelacaoFamiliarReader",
	"FreCiaAbertaRelacaoSubordinacaoReader",
	"FreCiaAbertaRemuneracaoAcaoReader",
	"FreCiaAbertaRemuneracaoMaximaMinimaMediaReader",
	"FreCiaAbertaRemuneracaoTotalOrgaoReader",
	"FreCiaAbertaRemuneracaoVariavelReader",
	"FreCiaAbertaResponsavelReader",
	"FreCiaAbertaTitularValorMobiliarioReader",
	"FreCiaAbertaTituloExteriorReader",
	"FreCiaAbertaTransacaoParteRelacionadaReader",
	"MetaFreCiaAbertaReader",
]
