"""CVM open-data **Auditor** readers (`AUDITOR/`).

Mirrors the `dados.cvm.gov.br/dados/AUDITOR/` portal branch — one sibling among the portal's other
roots. It publishes only a registry (`AUDITOR/CAD`, :mod:`filings_cvm.ingestion.auditor.cad`) of
the independent auditors CVM supervises, split into natural persons and audit firms, plus its META
reader. Every reader is re-exported flat from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.auditor.cad import (
	AuditorPfReader,
	AuditorPjReader,
	MetaAuditorReader,
)


__all__ = [
	"AuditorPfReader",
	"AuditorPjReader",
	"MetaAuditorReader",
]
