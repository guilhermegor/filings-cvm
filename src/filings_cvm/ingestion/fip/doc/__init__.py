"""CVM open-data **document-dump** readers for FIP (`FIP/DOC/*`).

The FIP portal root holds two document dumps, both flat year-partitioned CSVs (one reader each):
the pre-RCVM 175 quarterly report (`INF_TRIMESTRAL`, 2010–2023,
:mod:`filings_cvm.ingestion.fip.doc.inf_trimestral`) and the post-175 four-monthly report that
replaced it (`INF_QUADRIMESTRAL`, from 2024,
:mod:`filings_cvm.ingestion.fip.doc.inf_quadrimestral`). Re-exported from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fip.doc.inf_quadrimestral import InfQuadrimestralFipReader
from filings_cvm.ingestion.fip.doc.inf_trimestral import InfTrimestralFipReader


__all__ = [
	"InfQuadrimestralFipReader",
	"InfTrimestralFipReader",
]
