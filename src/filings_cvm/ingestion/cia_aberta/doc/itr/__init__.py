"""CVM open-data **ITR** readers for publicly held companies (`CIA_ABERTA/DOC/ITR`).

*Informações Trimestrais* — 19 members and 3.640.994 rows in 2025, the largest artifact this
library reads. Same shape as DFP, with one measured exception: `parecer` spells its fifth
column `TP_RELAT_ESP` (revisão especial) where DFP spells it `TP_RELAT_AUD`.

⚠️ `VL_CONTA` is exact text and its scale lives in `ESCALA_MOEDA` — see the base reader.
"""

from filings_cvm.ingestion.cia_aberta.doc.itr.bpa_con import (
	ItrCiaAbertaBpaConReader,
)
from filings_cvm.ingestion.cia_aberta.doc.itr.bpa_ind import (
	ItrCiaAbertaBpaIndReader,
)
from filings_cvm.ingestion.cia_aberta.doc.itr.bpp_con import (
	ItrCiaAbertaBppConReader,
)
from filings_cvm.ingestion.cia_aberta.doc.itr.bpp_ind import (
	ItrCiaAbertaBppIndReader,
)
from filings_cvm.ingestion.cia_aberta.doc.itr.composicao_capital import (
	ItrCiaAbertaComposicaoCapitalReader,
)
from filings_cvm.ingestion.cia_aberta.doc.itr.dfc_md_con import (
	ItrCiaAbertaDfcMdConReader,
)
from filings_cvm.ingestion.cia_aberta.doc.itr.dfc_md_ind import (
	ItrCiaAbertaDfcMdIndReader,
)
from filings_cvm.ingestion.cia_aberta.doc.itr.dfc_mi_con import (
	ItrCiaAbertaDfcMiConReader,
)
from filings_cvm.ingestion.cia_aberta.doc.itr.dfc_mi_ind import (
	ItrCiaAbertaDfcMiIndReader,
)
from filings_cvm.ingestion.cia_aberta.doc.itr.dmpl_con import (
	ItrCiaAbertaDmplConReader,
)
from filings_cvm.ingestion.cia_aberta.doc.itr.dmpl_ind import (
	ItrCiaAbertaDmplIndReader,
)
from filings_cvm.ingestion.cia_aberta.doc.itr.dra_con import (
	ItrCiaAbertaDraConReader,
)
from filings_cvm.ingestion.cia_aberta.doc.itr.dra_ind import (
	ItrCiaAbertaDraIndReader,
)
from filings_cvm.ingestion.cia_aberta.doc.itr.dre_con import (
	ItrCiaAbertaDreConReader,
)
from filings_cvm.ingestion.cia_aberta.doc.itr.dre_ind import (
	ItrCiaAbertaDreIndReader,
)
from filings_cvm.ingestion.cia_aberta.doc.itr.dva_con import (
	ItrCiaAbertaDvaConReader,
)
from filings_cvm.ingestion.cia_aberta.doc.itr.dva_ind import (
	ItrCiaAbertaDvaIndReader,
)
from filings_cvm.ingestion.cia_aberta.doc.itr.itr import (
	ItrCiaAbertaReader,
)
from filings_cvm.ingestion.cia_aberta.doc.itr.meta import MetaItrCiaAbertaReader
from filings_cvm.ingestion.cia_aberta.doc.itr.parecer import (
	ItrCiaAbertaParecerReader,
)


__all__ = [
	"ItrCiaAbertaBpaConReader",
	"ItrCiaAbertaBpaIndReader",
	"ItrCiaAbertaBppConReader",
	"ItrCiaAbertaBppIndReader",
	"ItrCiaAbertaComposicaoCapitalReader",
	"ItrCiaAbertaDfcMdConReader",
	"ItrCiaAbertaDfcMdIndReader",
	"ItrCiaAbertaDfcMiConReader",
	"ItrCiaAbertaDfcMiIndReader",
	"ItrCiaAbertaDmplConReader",
	"ItrCiaAbertaDmplIndReader",
	"ItrCiaAbertaDraConReader",
	"ItrCiaAbertaDraIndReader",
	"ItrCiaAbertaDreConReader",
	"ItrCiaAbertaDreIndReader",
	"ItrCiaAbertaDvaConReader",
	"ItrCiaAbertaDvaIndReader",
	"ItrCiaAbertaParecerReader",
	"ItrCiaAbertaReader",
	"MetaItrCiaAbertaReader",
]
