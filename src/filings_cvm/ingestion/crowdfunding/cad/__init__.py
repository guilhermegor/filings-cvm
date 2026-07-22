"""CVM open-data **registry** readers for crowdfunding platforms (`CROWDFUNDING/CAD`).

The three members of `cad_crowdfunding.zip` — the platform registry
(:mod:`filings_cvm.ingestion.crowdfunding.cad.crowdfunding`), its responsible administrators
(:mod:`filings_cvm.ingestion.crowdfunding.cad.crowdfunding_adm_resp`) and its partners
(:mod:`filings_cvm.ingestion.crowdfunding.cad.crowdfunding_socios`) — plus its META reader.
Re-exported from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.crowdfunding.cad.crowdfunding import CrowdfundingReader
from filings_cvm.ingestion.crowdfunding.cad.crowdfunding_adm_resp import CrowdfundingAdmRespReader
from filings_cvm.ingestion.crowdfunding.cad.crowdfunding_socios import CrowdfundingSociosReader
from filings_cvm.ingestion.crowdfunding.cad.meta import MetaCrowdfundingReader


__all__ = [
	"CrowdfundingAdmRespReader",
	"CrowdfundingReader",
	"CrowdfundingSociosReader",
	"MetaCrowdfundingReader",
]
