"""Ingestion section — parse and interpret files *received* from CVM (leitura).

Every "leitura" solution lives here: it takes a file downloaded from CVM (an XML standard document
or an open-data dump) and returns typed models / DataFrames. The building/serialising counterpart
lives in the ``submission`` section.

Readers are grouped by **CVM open-data portal root** (`dados.cvm.gov.br/dados/<ROOT>/…`), and each
root package **is** the public surface for its own readers::

    from filings_cvm.ingestion.cia_aberta import FreCiaAbertaAuditorReader
    from filings_cvm.ingestion.fidc import InfMensalFidcTabIReader

The 22 roots are re-exported here as packages, so ``from filings_cvm.ingestion import cia_aberta``
works too. **Individual readers are not re-exported** — neither here nor at the top level. The
portal's own division is the grouping the data already has, and a single flat namespace would put
200+ names in one undivided wall that every new reader widens. See the changelog's migration note.
"""

from filings_cvm.ingestion import (
	adm_cart,
	adm_fii,
	agente_auton,
	agente_fiduc,
	auditor,
	cia_aberta,
	cia_estrang,
	cia_incent,
	consultor_vlmob,
	coord_oferta,
	crowdfunding,
	emissor_cepac,
	fi,
	fiagro,
	fidc,
	fie,
	fii,
	fip,
	intermed,
	invnr,
	oferta,
	securit,
)


__all__ = [
	"adm_cart",
	"adm_fii",
	"agente_auton",
	"agente_fiduc",
	"auditor",
	"cia_aberta",
	"cia_estrang",
	"cia_incent",
	"consultor_vlmob",
	"coord_oferta",
	"crowdfunding",
	"emissor_cepac",
	"fi",
	"fiagro",
	"fidc",
	"fie",
	"fii",
	"fip",
	"intermed",
	"invnr",
	"oferta",
	"securit",
]
