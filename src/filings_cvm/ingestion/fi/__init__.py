"""CVM open-data **Fundos de Investimento** readers (`FI/`).

Mirrors the `dados.cvm.gov.br/dados/FI/` portal branch — one sibling among the
portal's other roots (`FIDC/`, `FII/`, `AUDITOR/`, `INVNR/`, …), each of which
gets its own sub-package here as it is implemented. Under `FI/` live the document
dumps (:mod:`filings_cvm.ingestion.fi.doc`) and the cadastro
(:mod:`filings_cvm.ingestion.fi.cad`). Every reader is re-exported flat from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fi.cad import CadastroFiReader
from filings_cvm.ingestion.fi.cad.cad_fi_hist import (
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
from filings_cvm.ingestion.fi.cad.registro import (
	RegistroClasseReader,
	RegistroFundoReader,
	RegistroSubclasseReader,
)
from filings_cvm.ingestion.fi.doc import (
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
