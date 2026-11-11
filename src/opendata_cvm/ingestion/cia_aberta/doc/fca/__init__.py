"""CVM open-data **FCA** readers for publicly held companies (`CIA_ABERTA/DOC/FCA`).

*Formulário Cadastral* — the index plus its nine detail tables (auditor, canal_divulgacao,
departamento_acionistas, dri, endereco, escriturador, geral, pais_estrangeiro_negociacao,
valor_mobiliario) — plus the META reader. Re-exported from `opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.cia_aberta.doc.fca.auditor import FcaCiaAbertaAuditorReader
from opendata_cvm.ingestion.cia_aberta.doc.fca.canal_divulgacao import (
	FcaCiaAbertaCanalDivulgacaoReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.fca.departamento_acionistas import (
	FcaCiaAbertaDepartamentoAcionistasReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.fca.dri import FcaCiaAbertaDriReader
from opendata_cvm.ingestion.cia_aberta.doc.fca.endereco import FcaCiaAbertaEnderecoReader
from opendata_cvm.ingestion.cia_aberta.doc.fca.escriturador import FcaCiaAbertaEscrituradorReader
from opendata_cvm.ingestion.cia_aberta.doc.fca.fca import FcaCiaAbertaReader
from opendata_cvm.ingestion.cia_aberta.doc.fca.geral import FcaCiaAbertaGeralReader
from opendata_cvm.ingestion.cia_aberta.doc.fca.meta import MetaFcaCiaAbertaReader
from opendata_cvm.ingestion.cia_aberta.doc.fca.pais_estrangeiro_negociacao import (
	FcaCiaAbertaPaisEstrangeiroNegociacaoReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.fca.valor_mobiliario import (
	FcaCiaAbertaValorMobiliarioReader,
)


__all__ = [
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
	"MetaFcaCiaAbertaReader",
]
