"""CVM open-data **document-dump** readers (`FI/DOC/*`).

The monthly document dumps: Informe Diário (`INF_DIARIO`), CDA (`CDA`), Extrato (`EXTRATO`),
Perfil Mensal
(`PERFIL_MENSAL`, nested in :mod:`filings_cvm.ingestion.fi.doc.perfil_mensal`), and the Lâmina
family (`LAMINA`, nested in :mod:`filings_cvm.ingestion.fi.doc.lamina`). Re-exported from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fi.doc.balancete import (
	BalanceteFiPre202311Reader,
	BalanceteFiReader,
	MetaBalanceteFiReader,
)
from filings_cvm.ingestion.fi.doc.cda import CdaReader, MetaCdaReader
from filings_cvm.ingestion.fi.doc.eventual import (
	EventualFiReader,
	MetaEventualFiReader,
)
from filings_cvm.ingestion.fi.doc.extrato import (
	ExtratoFiPre2020Reader,
	ExtratoFiReader,
	ExtratoFiSnapshotReader,
	MetaExtratoFiReader,
)
from filings_cvm.ingestion.fi.doc.informe_diario import (
	InformeDiarioReader,
	MetaInformeDiarioReader,
)
from filings_cvm.ingestion.fi.doc.lamina import (
	LaminaCarteiraReader,
	LaminaReader,
	MetaLaminaReader,
)
from filings_cvm.ingestion.fi.doc.perfil_mensal import (
	MetaPerfilMensalFiReader,
	PerfilMensalPre175Reader,
	PerfilMensalReader,
)


__all__ = [
	"BalanceteFiPre202311Reader",
	"BalanceteFiReader",
	"CdaReader",
	"EventualFiReader",
	"ExtratoFiPre2020Reader",
	"ExtratoFiReader",
	"ExtratoFiSnapshotReader",
	"InformeDiarioReader",
	"LaminaCarteiraReader",
	"LaminaReader",
	"MetaBalanceteFiReader",
	"MetaCdaReader",
	"MetaEventualFiReader",
	"MetaExtratoFiReader",
	"MetaInformeDiarioReader",
	"MetaLaminaReader",
	"MetaPerfilMensalFiReader",
	"PerfilMensalPre175Reader",
	"PerfilMensalReader",
]
