"""CVM open-data **document-dump** readers for FIE (`FIE/DOC/*`).

Two accounting document dumps, one reader each: the monthly trial balance (`BALANCETE`, post-RCVM
175, :mod:`filings_cvm.ingestion.fie.doc.balancete`) and the discontinued yearly balance sheet
(`BALANCO`, 2005–2020, pre-175, :mod:`filings_cvm.ingestion.fie.doc.balanco`), plus their META
readers. The FIE monthly measures (`FIE/MEDIDAS`) are a sibling of `FIE/DOC` on the portal, so
their reader lives one level up in :mod:`filings_cvm.ingestion.fie`. Re-exported from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fie.doc.balancete import BalanceteFieReader, MetaBalanceteFieReader
from filings_cvm.ingestion.fie.doc.balanco import BalancoFieReader, MetaBalancoFieReader


__all__ = [
	"BalanceteFieReader",
	"BalancoFieReader",
	"MetaBalanceteFieReader",
	"MetaBalancoFieReader",
]
