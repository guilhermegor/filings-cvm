"""CVM open-data **registry** readers for independent auditors (`AUDITOR/CAD`).

The two members of the `cad_auditor.zip` snapshot — natural-person auditors
(:class:`~filings_cvm.ingestion.auditor.cad.auditor_pf.AuditorPfReader`) and audit firms
(:class:`~filings_cvm.ingestion.auditor.cad.auditor_pj.AuditorPjReader`) — over a shared private
base (`_base_auditor_reader`), plus the dataset's META reader. Re-exported from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.auditor.cad.auditor_pf import AuditorPfReader
from filings_cvm.ingestion.auditor.cad.auditor_pj import AuditorPjReader
from filings_cvm.ingestion.auditor.cad.meta import MetaAuditorReader


__all__ = [
	"AuditorPfReader",
	"AuditorPjReader",
	"MetaAuditorReader",
]
