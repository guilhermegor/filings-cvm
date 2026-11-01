"""CVM open-data **sanctioning proceedings** readers (`PROCESSO/SANCIONADOR`).

The two members of `processo_sancionador.zip` — the proceedings
(:mod:`filings_cvm.ingestion.processo.sancionador.processo_sancionador`) and their accused parties
(:mod:`filings_cvm.ingestion.processo.sancionador.processo_sancionador_acusado`) — plus the
dataset's META reader. Re-exported from `filings_cvm.ingestion.processo`.
"""

from filings_cvm.ingestion.processo.sancionador.meta import MetaProcessoSancionadorReader
from filings_cvm.ingestion.processo.sancionador.processo_sancionador import (
	ProcessoSancionadorReader,
)
from filings_cvm.ingestion.processo.sancionador.processo_sancionador_acusado import (
	ProcessoSancionadorAcusadoReader,
)


__all__ = [
	"MetaProcessoSancionadorReader",
	"ProcessoSancionadorAcusadoReader",
	"ProcessoSancionadorReader",
]
