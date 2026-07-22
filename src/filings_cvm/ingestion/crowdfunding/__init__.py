"""CVM open-data **Crowdfunding** readers (`CROWDFUNDING/`).

Mirrors the `dados.cvm.gov.br/dados/CROWDFUNDING/` portal branch — one sibling among the portal's
other roots. It publishes only a registry (`CROWDFUNDING/CAD`,
:mod:`filings_cvm.ingestion.crowdfunding.cad`) of the electronic investment-crowdfunding platforms,
in a three-member archive, plus its META reader. Every reader is re-exported flat from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.crowdfunding.cad import (
	CrowdfundingAdmRespReader,
	CrowdfundingReader,
	CrowdfundingSociosReader,
	MetaCrowdfundingReader,
)


__all__ = [
	"CrowdfundingAdmRespReader",
	"CrowdfundingReader",
	"CrowdfundingSociosReader",
	"MetaCrowdfundingReader",
]
