"""CVM open-data **securities-offering register** readers (`OFERTA/DISTRIB`).

The two members of `oferta_distribuicao.zip` — the historical offering register
(:mod:`opendata_cvm.ingestion.oferta.distrib.oferta_distribuicao`) and the RCVM 160
offering-request register (:mod:`opendata_cvm.ingestion.oferta.distrib.oferta_resolucao_160`) —
plus its META reader. Re-exported from `opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.oferta.distrib.meta import MetaOfertaReader
from opendata_cvm.ingestion.oferta.distrib.oferta_distribuicao import OfertaDistribuicaoReader
from opendata_cvm.ingestion.oferta.distrib.oferta_resolucao_160 import OfertaResolucao160Reader


__all__ = [
	"MetaOfertaReader",
	"OfertaDistribuicaoReader",
	"OfertaResolucao160Reader",
]
