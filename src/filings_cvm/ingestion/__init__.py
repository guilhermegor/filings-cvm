"""Ingestion section — parse and interpret files *received* from CVM (leitura).

Every "leitura" solution lives here: it takes a file downloaded from CVM (an XML
standard document or an open-data dump) and returns typed models / DataFrames. The
building/serialising counterpart lives in the ``submission`` section.

    from filings_cvm.ingestion import InformeDiarioReader
"""

from filings_cvm.ingestion.cad import CadastroFiReader
from filings_cvm.ingestion.cad.cad_fi_hist import (
	CadastroFiHistAdminReader,
	CadastroFiHistAuditorReader,
	CadastroFiHistClasseReader,
	CadastroFiHistCondomReader,
	CadastroFiHistControladorReader,
	CadastroFiHistCustodianteReader,
	CadastroFiHistDenomComercReader,
	CadastroFiHistDenomSocialReader,
	CadastroFiHistDiretorRespReader,
	CadastroFiHistExclusivoReader,
	CadastroFiHistExercSocialReader,
	CadastroFiHistFicReader,
	CadastroFiHistGestorReader,
	CadastroFiHistPublicoAlvoReader,
	CadastroFiHistRentabReader,
	CadastroFiHistSitReader,
	CadastroFiHistTaxaAdmReader,
	CadastroFiHistTaxaPerfmReader,
	CadastroFiHistTribLprazoReader,
)
from filings_cvm.ingestion.cad.registro import (
	RegistroClasseReader,
	RegistroFundoReader,
	RegistroSubclasseReader,
)
from filings_cvm.ingestion.doc import (
	CdaReader,
	InformeDiarioReader,
	LaminaCarteiraReader,
	LaminaReader,
)


__all__ = [
	"CadastroFiHistAdminReader",
	"CadastroFiHistAuditorReader",
	"CadastroFiHistClasseReader",
	"CadastroFiHistCondomReader",
	"CadastroFiHistControladorReader",
	"CadastroFiHistCustodianteReader",
	"CadastroFiHistDenomComercReader",
	"CadastroFiHistDenomSocialReader",
	"CadastroFiHistDiretorRespReader",
	"CadastroFiHistExclusivoReader",
	"CadastroFiHistExercSocialReader",
	"CadastroFiHistFicReader",
	"CadastroFiHistGestorReader",
	"CadastroFiHistPublicoAlvoReader",
	"CadastroFiHistRentabReader",
	"CadastroFiHistSitReader",
	"CadastroFiHistTaxaAdmReader",
	"CadastroFiHistTaxaPerfmReader",
	"CadastroFiHistTribLprazoReader",
	"CadastroFiReader",
	"CdaReader",
	"InformeDiarioReader",
	"LaminaCarteiraReader",
	"LaminaReader",
	"RegistroClasseReader",
	"RegistroFundoReader",
	"RegistroSubclasseReader",
]
