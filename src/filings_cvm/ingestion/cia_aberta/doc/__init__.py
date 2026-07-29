"""CVM open-data **document** readers for publicly held companies (`CIA_ABERTA/DOC`).

Mirrors the `CIA_ABERTA/DOC/` portal branch, which holds seven datasets — CGVN, DFP, FCA, FRE,
IPE, ITR and VLMO. Each is a **yearly ZIP** (`<ds>_cia_aberta_AAAA.zip`) and each gets its own
grounding: the member count differs sharply between them (IPE ships 1 member, VLMO 2, FCA 10), so
none may be written by presuming a sibling's shape.

This slice ships **IPE** (:mod:`filings_cvm.ingestion.cia_aberta.doc.ipe`); the remaining six land
as their own readers. Every reader is re-exported flat from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.cia_aberta.doc.cgvn import (
	CgvnCiaAbertaPraticasReader,
	CgvnCiaAbertaReader,
	MetaCgvnCiaAbertaReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fca import (
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
	MetaFcaCiaAbertaReader,
)
from filings_cvm.ingestion.cia_aberta.doc.fre import (
	FreCiaAbertaCapitalSocialClasseAcaoReader,
	FreCiaAbertaCapitalSocialReader,
	FreCiaAbertaCapitalSocialTituloConversivelReader,
	FreCiaAbertaDistribuicaoCapitalClasseAcaoReader,
	FreCiaAbertaDistribuicaoCapitalReader,
	FreCiaAbertaMercadoEstrangeiroReader,
	FreCiaAbertaReader,
	FreCiaAbertaResponsavelReader,
	MetaFreCiaAbertaReader,
)
from filings_cvm.ingestion.cia_aberta.doc.ipe import (
	IpeCiaAbertaReader,
	MetaIpeCiaAbertaReader,
)
from filings_cvm.ingestion.cia_aberta.doc.vlmo import (
	MetaVlmoCiaAbertaReader,
	VlmoCiaAbertaConReader,
	VlmoCiaAbertaReader,
)


__all__ = [
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
	"FreCiaAbertaCapitalSocialClasseAcaoReader",
	"FreCiaAbertaCapitalSocialReader",
	"FreCiaAbertaCapitalSocialTituloConversivelReader",
	"FreCiaAbertaDistribuicaoCapitalClasseAcaoReader",
	"FreCiaAbertaDistribuicaoCapitalReader",
	"FreCiaAbertaMercadoEstrangeiroReader",
	"FreCiaAbertaReader",
	"FreCiaAbertaResponsavelReader",
	"IpeCiaAbertaReader",
	"MetaCgvnCiaAbertaReader",
	"MetaFcaCiaAbertaReader",
	"MetaFreCiaAbertaReader",
	"MetaIpeCiaAbertaReader",
	"MetaVlmoCiaAbertaReader",
	"VlmoCiaAbertaConReader",
	"VlmoCiaAbertaReader",
]
