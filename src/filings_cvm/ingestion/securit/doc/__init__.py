"""CVM open-data **document-dump** readers for Securitização (`SECURIT/DOC/*`).

Today the two DFIN indexes — of CRA (`DFIN_CRA`,
:mod:`filings_cvm.ingestion.securit.doc.dfin_cra`) and CRI (`DFIN_CRI`,
:mod:`filings_cvm.ingestion.securit.doc.dfin_cri`) financial statements, both flat year-partitioned
CSVs. The three monthly `INF_MENSAL_*` multi-member dumps land as later PRs. Re-exported from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.securit.doc.dfin_cra import DfinCraReader
from filings_cvm.ingestion.securit.doc.dfin_cri import DfinCriReader


__all__ = [
	"DfinCraReader",
	"DfinCriReader",
]
