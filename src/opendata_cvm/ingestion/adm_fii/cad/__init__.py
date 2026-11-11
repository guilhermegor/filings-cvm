"""CVM open-data **registry** readers for FII administrators (`ADM_FII/CAD`).

The single registry snapshot of FII administrators (`cad_adm_fii.csv`,
:mod:`opendata_cvm.ingestion.adm_fii.cad.cadastro`), plus its META reader. Re-exported from
`opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.adm_fii.cad.cadastro import (
	CadastroAdmFiiReader,
	MetaCadAdmFiiReader,
)


__all__ = [
	"CadastroAdmFiiReader",
	"MetaCadAdmFiiReader",
]
