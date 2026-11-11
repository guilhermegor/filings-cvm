"""CVM open-data **ITR** readers for publicly held companies (`CIA_ABERTA/DOC/ITR`).

*Informações Trimestrais* — 19 members and 3.640.994 rows in 2025, the largest artifact this
library reads. Same shape as DFP, with one measured exception: `parecer` spells its fifth
column `TP_RELAT_ESP` (revisão especial) where DFP spells it `TP_RELAT_AUD`.

⚠️ `VL_CONTA` is exact text and its scale lives in `ESCALA_MOEDA` — see the base reader.
"""

from opendata_cvm.ingestion.cia_aberta.doc.itr.bpa_con import (
	ItrCiaAbertaBpaConReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.itr.bpa_ind import (
	ItrCiaAbertaBpaIndReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.itr.bpp_con import (
	ItrCiaAbertaBppConReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.itr.bpp_ind import (
	ItrCiaAbertaBppIndReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.itr.composicao_capital import (
	ItrCiaAbertaComposicaoCapitalReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.itr.dfc_md_con import (
	ItrCiaAbertaDfcMdConReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.itr.dfc_md_ind import (
	ItrCiaAbertaDfcMdIndReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.itr.dfc_mi_con import (
	ItrCiaAbertaDfcMiConReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.itr.dfc_mi_ind import (
	ItrCiaAbertaDfcMiIndReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.itr.dmpl_con import (
	ItrCiaAbertaDmplConReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.itr.dmpl_ind import (
	ItrCiaAbertaDmplIndReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.itr.dra_con import (
	ItrCiaAbertaDraConReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.itr.dra_ind import (
	ItrCiaAbertaDraIndReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.itr.dre_con import (
	ItrCiaAbertaDreConReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.itr.dre_ind import (
	ItrCiaAbertaDreIndReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.itr.dva_con import (
	ItrCiaAbertaDvaConReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.itr.dva_ind import (
	ItrCiaAbertaDvaIndReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.itr.itr import (
	ItrCiaAbertaReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.itr.meta import MetaItrCiaAbertaReader
from opendata_cvm.ingestion.cia_aberta.doc.itr.parecer import (
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
