"""CVM open-data **Complemento FI** readers (`FI/DOC/COMPL`).

Complementary information funds declare about themselves, one reader per member of
`compl_fi_AAAAMM.zip` (4 members), plus the META reader. A closed monthly series
(`201801`-`201904`). Re-exported from `filings_cvm.ingestion.fi`.
"""

from filings_cvm.ingestion.fi.doc.compl.compl import ComplFiReader
from filings_cvm.ingestion.fi.doc.compl.compl_inf import ComplFiInfReader
from filings_cvm.ingestion.fi.doc.compl.compl_inf_cotst import ComplFiInfCotstReader
from filings_cvm.ingestion.fi.doc.compl.compl_prest import ComplFiPrestReader
from filings_cvm.ingestion.fi.doc.compl.meta import MetaComplFiReader


__all__ = [
	"ComplFiInfCotstReader",
	"ComplFiInfReader",
	"ComplFiPrestReader",
	"ComplFiReader",
	"MetaComplFiReader",
]
