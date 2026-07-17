"""CVM CAD/FI **histórico** readers — the 19 per-attribute change-logs of `cad_fi_hist.zip`.

One reader per mutable attribute of the legacy CAD/FI registry, over a shared private base
(`_base_cad_fi_hist_reader`), plus its META reader. Re-exported from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fi.cad.cad_fi_hist.cad_fi_hist_admin import CadastroFiHistAdminReader
from filings_cvm.ingestion.fi.cad.cad_fi_hist.cad_fi_hist_auditor import (
	CadastroFiHistAuditorReader,
)
from filings_cvm.ingestion.fi.cad.cad_fi_hist.cad_fi_hist_classe import CadastroFiHistClasseReader
from filings_cvm.ingestion.fi.cad.cad_fi_hist.cad_fi_hist_condom import CadastroFiHistCondomReader
from filings_cvm.ingestion.fi.cad.cad_fi_hist.cad_fi_hist_controlador import (
	CadastroFiHistControladorReader,
)
from filings_cvm.ingestion.fi.cad.cad_fi_hist.cad_fi_hist_custodiante import (
	CadastroFiHistCustodianteReader,
)
from filings_cvm.ingestion.fi.cad.cad_fi_hist.cad_fi_hist_denom_comerc import (
	CadastroFiHistDenomComercReader,
)
from filings_cvm.ingestion.fi.cad.cad_fi_hist.cad_fi_hist_denom_social import (
	CadastroFiHistDenomSocialReader,
)
from filings_cvm.ingestion.fi.cad.cad_fi_hist.cad_fi_hist_diretor_resp import (
	CadastroFiHistDiretorRespReader,
)
from filings_cvm.ingestion.fi.cad.cad_fi_hist.cad_fi_hist_exclusivo import (
	CadastroFiHistExclusivoReader,
)
from filings_cvm.ingestion.fi.cad.cad_fi_hist.cad_fi_hist_exerc_social import (
	CadastroFiHistExercSocialReader,
)
from filings_cvm.ingestion.fi.cad.cad_fi_hist.cad_fi_hist_fic import CadastroFiHistFicReader
from filings_cvm.ingestion.fi.cad.cad_fi_hist.cad_fi_hist_gestor import CadastroFiHistGestorReader
from filings_cvm.ingestion.fi.cad.cad_fi_hist.cad_fi_hist_publico_alvo import (
	CadastroFiHistPublicoAlvoReader,
)
from filings_cvm.ingestion.fi.cad.cad_fi_hist.cad_fi_hist_rentab import CadastroFiHistRentabReader
from filings_cvm.ingestion.fi.cad.cad_fi_hist.cad_fi_hist_sit import CadastroFiHistSitReader
from filings_cvm.ingestion.fi.cad.cad_fi_hist.cad_fi_hist_taxa_adm import (
	CadastroFiHistTaxaAdmReader,
)
from filings_cvm.ingestion.fi.cad.cad_fi_hist.cad_fi_hist_taxa_perfm import (
	CadastroFiHistTaxaPerfmReader,
)
from filings_cvm.ingestion.fi.cad.cad_fi_hist.cad_fi_hist_trib_lprazo import (
	CadastroFiHistTribLprazoReader,
)
from filings_cvm.ingestion.fi.cad.cad_fi_hist.meta import MetaCadFiHistReader


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
	"MetaCadFiHistReader",
]
