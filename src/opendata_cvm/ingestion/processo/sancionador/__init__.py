"""CVM open-data **sanctioning proceedings** readers (`PROCESSO/SANCIONADOR`).

The two members of `processo_sancionador.zip` — the proceedings
(:mod:`opendata_cvm.ingestion.processo.sancionador.processo_sancionador`) and their accused parties
(:mod:`opendata_cvm.ingestion.processo.sancionador.processo_sancionador_acusado`) — plus the
dataset's META reader. Re-exported from `opendata_cvm.ingestion.processo`.
"""

from opendata_cvm.ingestion.processo.sancionador.meta import MetaProcessoSancionadorReader
from opendata_cvm.ingestion.processo.sancionador.processo_sancionador import (
	ProcessoSancionadorReader,
)
from opendata_cvm.ingestion.processo.sancionador.processo_sancionador_acusado import (
	ProcessoSancionadorAcusadoReader,
)


__all__ = [
	"MetaProcessoSancionadorReader",
	"ProcessoSancionadorAcusadoReader",
	"ProcessoSancionadorReader",
]
