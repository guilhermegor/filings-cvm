"""CVM open-data **registry** readers for CEPAC issuers (`EMISSOR_CEPAC/CAD`).

The single registry snapshot of CEPAC issuers (`cad_emissor_cepac.csv`,
:mod:`opendata_cvm.ingestion.emissor_cepac.cad.cadastro`), plus its META reader. Re-exported from
`opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.emissor_cepac.cad.cadastro import (
	CadastroEmissorCepacReader,
	MetaCadEmissorCepacReader,
)


__all__ = [
	"CadastroEmissorCepacReader",
	"MetaCadEmissorCepacReader",
]
