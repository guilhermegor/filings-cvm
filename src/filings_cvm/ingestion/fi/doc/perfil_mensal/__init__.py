"""CVM open-data **PERFIL MENSAL FI** readers (`FI/DOC/PERFIL_MENSAL`).

The monthly fund/class profile — shareholder mix, VaR and stress figures, derivative notionals and
the counterparty/issuer concentration blocks — plus its META reader. **Two readers**, one per
regulatory regime: RCVM 175's fund/class split changed the header mid-series (106 → 107 columns) at
`202312`. Re-exported from `filings_cvm.ingestion.fi`.
"""

from filings_cvm.ingestion.fi.doc.perfil_mensal.meta import MetaPerfilMensalFiReader
from filings_cvm.ingestion.fi.doc.perfil_mensal.perfil_mensal import PerfilMensalReader
from filings_cvm.ingestion.fi.doc.perfil_mensal.perfil_mensal_pre175 import (
	PerfilMensalPre175Reader,
)


__all__ = ["MetaPerfilMensalFiReader", "PerfilMensalPre175Reader", "PerfilMensalReader"]
