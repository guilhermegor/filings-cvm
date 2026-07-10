"""Ingestion section — parse and interpret files *received* from CVM (leitura).

Every "leitura" solution lives here: it takes a file downloaded from CVM (an XML
standard document or an open-data dump) and returns typed models / DataFrames. The
building/serialising counterpart lives in the ``submission`` section.

    from filings_cvm.ingestion import InformeDiarioReader
"""

from filings_cvm.ingestion.cadastro_fi import CadastroFiReader
from filings_cvm.ingestion.cda import CdaReader
from filings_cvm.ingestion.informe_diario import InformeDiarioReader
from filings_cvm.ingestion.lamina import LaminaReader
from filings_cvm.ingestion.lamina_carteira import LaminaCarteiraReader
from filings_cvm.ingestion.registro_classe import RegistroClasseReader
from filings_cvm.ingestion.registro_fundo import RegistroFundoReader
from filings_cvm.ingestion.registro_subclasse import RegistroSubclasseReader


__all__ = [
	"CadastroFiReader",
	"CdaReader",
	"InformeDiarioReader",
	"LaminaCarteiraReader",
	"LaminaReader",
	"RegistroClasseReader",
	"RegistroFundoReader",
	"RegistroSubclasseReader",
]
