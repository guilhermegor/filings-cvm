"""CVM open-data **Administrador de FII** readers (`ADM_FII/`).

Mirrors the `dados.cvm.gov.br/dados/ADM_FII/` portal branch — one sibling among the portal's
other roots. It publishes only a registry (`ADM_FII/CAD`,
:mod:`filings_cvm.ingestion.adm_fii.cad`) of the FII administrators (institutions), plus its META
reader. Every reader is re-exported flat from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.adm_fii.cad import (
	CadastroAdmFiiReader,
	MetaCadAdmFiiReader,
)


__all__ = [
	"CadastroAdmFiiReader",
	"MetaCadAdmFiiReader",
]
