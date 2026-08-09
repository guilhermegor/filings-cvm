"""CVM open-data **EXTRATO FI** readers (`FI/DOC/EXTRATO`).

The Extrato das Informações sobre o Fundo, plus its META reader. **Three readers**, because the
dataset publishes **two artifacts** and the yearly one changed schema mid-series: yearly filings
from 2020 (117 columns), the yearly filings through 2019 (116), and the fixed-URL snapshot holding
each fund's latest extrato. Re-exported from `filings_cvm.ingestion.fi`.
"""

from filings_cvm.ingestion.fi.doc.extrato.extrato import ExtratoFiReader
from filings_cvm.ingestion.fi.doc.extrato.extrato_pre2020 import ExtratoFiPre2020Reader
from filings_cvm.ingestion.fi.doc.extrato.extrato_snapshot import ExtratoFiSnapshotReader
from filings_cvm.ingestion.fi.doc.extrato.meta import MetaExtratoFiReader


__all__ = [
	"ExtratoFiPre2020Reader",
	"ExtratoFiReader",
	"ExtratoFiSnapshotReader",
	"MetaExtratoFiReader",
]
