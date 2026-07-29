"""CVM open-data **FRE** readers for publicly held companies (`CIA_ABERTA/DOC/FRE`).

*Formulário de Referência* — the portal's largest dataset (36 members, ~131k rows), implemented
in four themed slices. This package currently ships the **index + capital-structure** slice plus
the META reader; the administração/pessoas, diversidade and remuneração slices follow.
Re-exported from `filings_cvm.ingestion`.
"""

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
from filings_cvm.ingestion.cia_aberta.doc.fre.mercado_estrangeiro import (
	FreCiaAbertaMercadoEstrangeiroReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre.meta import MetaFreCiaAbertaReader
from filings_cvm.ingestion.cia_aberta.doc.fre.responsavel import FreCiaAbertaResponsavelReader


__all__ = [
	"FreCiaAbertaCapitalSocialClasseAcaoReader",
	"FreCiaAbertaCapitalSocialReader",
	"FreCiaAbertaCapitalSocialTituloConversivelReader",
	"FreCiaAbertaDistribuicaoCapitalClasseAcaoReader",
	"FreCiaAbertaDistribuicaoCapitalReader",
	"FreCiaAbertaMercadoEstrangeiroReader",
	"FreCiaAbertaReader",
	"FreCiaAbertaResponsavelReader",
	"MetaFreCiaAbertaReader",
]
