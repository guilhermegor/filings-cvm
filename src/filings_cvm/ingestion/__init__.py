"""Ingestion section — parse and interpret files *received* from CVM (leitura).

Every "leitura" solution lives here: it takes a file downloaded from CVM (an XML
standard document or an open-data dump) and returns typed models / DataFrames. The
building/serialising counterpart lives in the ``submission`` section.

    from filings_cvm.ingestion import InformeDiarioReader
"""

from filings_cvm.ingestion.cad_fi_hist_admin import CadastroFiHistAdminReader
from filings_cvm.ingestion.cad_fi_hist_auditor import CadastroFiHistAuditorReader
from filings_cvm.ingestion.cad_fi_hist_classe import CadastroFiHistClasseReader
from filings_cvm.ingestion.cad_fi_hist_condom import CadastroFiHistCondomReader
from filings_cvm.ingestion.cad_fi_hist_controlador import CadastroFiHistControladorReader
from filings_cvm.ingestion.cad_fi_hist_custodiante import CadastroFiHistCustodianteReader
from filings_cvm.ingestion.cad_fi_hist_denom_comerc import CadastroFiHistDenomComercReader
from filings_cvm.ingestion.cad_fi_hist_denom_social import CadastroFiHistDenomSocialReader
from filings_cvm.ingestion.cad_fi_hist_diretor_resp import CadastroFiHistDiretorRespReader
from filings_cvm.ingestion.cad_fi_hist_exclusivo import CadastroFiHistExclusivoReader
from filings_cvm.ingestion.cad_fi_hist_exerc_social import CadastroFiHistExercSocialReader
from filings_cvm.ingestion.cad_fi_hist_fic import CadastroFiHistFicReader
from filings_cvm.ingestion.cad_fi_hist_gestor import CadastroFiHistGestorReader
from filings_cvm.ingestion.cad_fi_hist_publico_alvo import CadastroFiHistPublicoAlvoReader
from filings_cvm.ingestion.cad_fi_hist_rentab import CadastroFiHistRentabReader
from filings_cvm.ingestion.cad_fi_hist_sit import CadastroFiHistSitReader
from filings_cvm.ingestion.cad_fi_hist_taxa_adm import CadastroFiHistTaxaAdmReader
from filings_cvm.ingestion.cad_fi_hist_taxa_perfm import CadastroFiHistTaxaPerfmReader
from filings_cvm.ingestion.cad_fi_hist_trib_lprazo import CadastroFiHistTribLprazoReader
from filings_cvm.ingestion.cadastro_fi import CadastroFiReader
from filings_cvm.ingestion.cda import CdaReader
from filings_cvm.ingestion.informe_diario import InformeDiarioReader
from filings_cvm.ingestion.lamina import LaminaReader
from filings_cvm.ingestion.lamina_carteira import LaminaCarteiraReader
from filings_cvm.ingestion.registro_classe import RegistroClasseReader
from filings_cvm.ingestion.registro_fundo import RegistroFundoReader
from filings_cvm.ingestion.registro_subclasse import RegistroSubclasseReader


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
