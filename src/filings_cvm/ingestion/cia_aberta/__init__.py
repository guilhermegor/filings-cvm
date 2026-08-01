"""CVM open-data **Companhias Abertas** readers (`CIA_ABERTA/`).

Mirrors the `dados.cvm.gov.br/dados/CIA_ABERTA/` portal branch — the last and largest root of the
#41 sweep. The portal branch holds three sub-roots: `CAD` (the company registry, implemented here
via :mod:`filings_cvm.ingestion.cia_aberta.cad`), `DOC` (seven financial-statement datasets —
CGVN / DFP / FCA / FRE / IPE / ITR / VLMO) and `EVENTOS` (share buybacks). This slice ships the
`CAD` registry plus the `DOC/IPE` filing index; the remaining six `DOC` datasets and `EVENTOS` land
as their own readers. Every reader is re-exported flat from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.cia_aberta.cad import (
	CadastroCiaAbertaReader,
	MetaCadCiaAbertaReader,
)
from filings_cvm.ingestion.cia_aberta.doc import (
	CgvnCiaAbertaPraticasReader,
	CgvnCiaAbertaReader,
	FcaCiaAbertaAuditorReader,
	FcaCiaAbertaCanalDivulgacaoReader,
	FcaCiaAbertaDepartamentoAcionistasReader,
	FcaCiaAbertaDriReader,
	FcaCiaAbertaEnderecoReader,
	FcaCiaAbertaEscrituradorReader,
	FcaCiaAbertaGeralReader,
	FcaCiaAbertaPaisEstrangeiroNegociacaoReader,
	FcaCiaAbertaReader,
	FcaCiaAbertaValorMobiliarioReader,
	FreCiaAbertaAdministradorMembroConselhoFiscalReader,
	FreCiaAbertaAuditorReader,
	FreCiaAbertaCapitalSocialClasseAcaoReader,
	FreCiaAbertaCapitalSocialReader,
	FreCiaAbertaCapitalSocialTituloConversivelReader,
	FreCiaAbertaDistribuicaoCapitalClasseAcaoReader,
	FreCiaAbertaDistribuicaoCapitalReader,
	FreCiaAbertaMembroComiteReader,
	FreCiaAbertaMercadoEstrangeiroReader,
	FreCiaAbertaPosicaoAcionariaClasseAcaoReader,
	FreCiaAbertaPosicaoAcionariaReader,
	FreCiaAbertaReader,
	FreCiaAbertaRelacaoFamiliarReader,
	FreCiaAbertaRelacaoSubordinacaoReader,
	FreCiaAbertaResponsavelReader,
	IpeCiaAbertaReader,
	MetaCgvnCiaAbertaReader,
	MetaFcaCiaAbertaReader,
	MetaFreCiaAbertaReader,
	MetaIpeCiaAbertaReader,
	MetaVlmoCiaAbertaReader,
	VlmoCiaAbertaConReader,
	VlmoCiaAbertaReader,
)


__all__ = [
	"CadastroCiaAbertaReader",
	"CgvnCiaAbertaPraticasReader",
	"CgvnCiaAbertaReader",
	"FcaCiaAbertaAuditorReader",
	"FcaCiaAbertaCanalDivulgacaoReader",
	"FcaCiaAbertaDepartamentoAcionistasReader",
	"FcaCiaAbertaDriReader",
	"FcaCiaAbertaEnderecoReader",
	"FcaCiaAbertaEscrituradorReader",
	"FcaCiaAbertaGeralReader",
	"FcaCiaAbertaPaisEstrangeiroNegociacaoReader",
	"FcaCiaAbertaReader",
	"FcaCiaAbertaValorMobiliarioReader",
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
	"IpeCiaAbertaReader",
	"MetaCadCiaAbertaReader",
	"MetaCgvnCiaAbertaReader",
	"MetaFcaCiaAbertaReader",
	"MetaFreCiaAbertaReader",
	"MetaIpeCiaAbertaReader",
	"MetaVlmoCiaAbertaReader",
	"VlmoCiaAbertaConReader",
	"VlmoCiaAbertaReader",
]
