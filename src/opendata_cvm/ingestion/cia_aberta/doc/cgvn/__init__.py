"""CVM open-data **CGVN** readers for publicly held companies (`CIA_ABERTA/DOC/CGVN`).

`Informe sobre o Código Brasileiro de Governança Corporativa` — the **index** of filed informes
(`CgvnCiaAbertaReader`) and their **content**, the practice-by-practice adoption report
(`CgvnCiaAbertaPraticasReader`) — plus the META reader. Re-exported from `opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.cia_aberta.doc.cgvn.cgvn import CgvnCiaAbertaReader
from opendata_cvm.ingestion.cia_aberta.doc.cgvn.meta import MetaCgvnCiaAbertaReader
from opendata_cvm.ingestion.cia_aberta.doc.cgvn.praticas import CgvnCiaAbertaPraticasReader


__all__ = [
	"CgvnCiaAbertaPraticasReader",
	"CgvnCiaAbertaReader",
	"MetaCgvnCiaAbertaReader",
]
