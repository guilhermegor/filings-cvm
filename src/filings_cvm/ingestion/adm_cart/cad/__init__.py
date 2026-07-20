"""CVM open-data **registry** readers for portfolio managers (`ADM_CART/CAD`).

The five members of the `cad_adm_cart.zip` snapshot — the natural- and legal-person managers
(:class:`~filings_cvm.ingestion.adm_cart.cad.adm_cart_pf.AdmCartPfReader`,
:class:`~filings_cvm.ingestion.adm_cart.cad.adm_cart_pj.AdmCartPjReader`) plus their directors,
responsible officers and partners
(:class:`~filings_cvm.ingestion.adm_cart.cad.adm_cart_diretor.AdmCartDiretorReader`,
:class:`~filings_cvm.ingestion.adm_cart.cad.adm_cart_resp.AdmCartRespReader`,
:class:`~filings_cvm.ingestion.adm_cart.cad.adm_cart_socios.AdmCartSociosReader`) — over a shared
private base (`_base_adm_cart_reader`), plus the dataset's META reader. Re-exported flat at the
package root.
"""

from filings_cvm.ingestion.adm_cart.cad.adm_cart_diretor import AdmCartDiretorReader
from filings_cvm.ingestion.adm_cart.cad.adm_cart_pf import AdmCartPfReader
from filings_cvm.ingestion.adm_cart.cad.adm_cart_pj import AdmCartPjReader
from filings_cvm.ingestion.adm_cart.cad.adm_cart_resp import AdmCartRespReader
from filings_cvm.ingestion.adm_cart.cad.adm_cart_socios import AdmCartSociosReader
from filings_cvm.ingestion.adm_cart.cad.meta import MetaAdmCartReader


__all__ = [
	"AdmCartDiretorReader",
	"AdmCartPfReader",
	"AdmCartPjReader",
	"AdmCartRespReader",
	"AdmCartSociosReader",
	"MetaAdmCartReader",
]
