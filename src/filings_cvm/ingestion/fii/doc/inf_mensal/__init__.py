"""CVM Informe Mensal FII readers — the 3 members of ``inf_mensal_fii_AAAA.zip``.

One reader per member (`geral`, `ativo_passivo`, `complemento`), over a shared private base
(`_base_inf_mensal_fii_reader`), plus its META reader. The dump is partitioned by **year**, not
month. Re-exported from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fii.doc.inf_mensal.inf_mensal_fii_ativo_passivo import (
	InfMensalFiiAtivoPassivoReader,
)
from filings_cvm.ingestion.fii.doc.inf_mensal.inf_mensal_fii_complemento import (
	InfMensalFiiComplementoReader,
)
from filings_cvm.ingestion.fii.doc.inf_mensal.inf_mensal_fii_geral import InfMensalFiiGeralReader
from filings_cvm.ingestion.fii.doc.inf_mensal.meta import MetaInfMensalFiiReader


__all__ = [
	"InfMensalFiiAtivoPassivoReader",
	"InfMensalFiiComplementoReader",
	"InfMensalFiiGeralReader",
	"MetaInfMensalFiiReader",
]
