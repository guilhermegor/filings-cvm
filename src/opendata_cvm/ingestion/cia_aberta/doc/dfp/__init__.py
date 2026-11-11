"""CVM open-data **DFP** readers for publicly held companies (`CIA_ABERTA/DOC/DFP`).

*Demonstrações Financeiras Padronizadas* — 19 members and ~1,17 million rows: the filing
index, eight statement types in a *consolidado* and an *individual* variant each, the share
composition and the auditor's opinion. Re-exported from `opendata_cvm.ingestion.cia_aberta`.

⚠️ `VL_CONTA` is exact text and its scale lives in `ESCALA_MOEDA` — see the base reader.
"""

from opendata_cvm.ingestion.cia_aberta.doc.dfp.bpa_con import (
	DfpCiaAbertaBpaConReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.dfp.bpa_ind import (
	DfpCiaAbertaBpaIndReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.dfp.bpp_con import (
	DfpCiaAbertaBppConReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.dfp.bpp_ind import (
	DfpCiaAbertaBppIndReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.dfp.composicao_capital import (
	DfpCiaAbertaComposicaoCapitalReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.dfp.dfc_md_con import (
	DfpCiaAbertaDfcMdConReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.dfp.dfc_md_ind import (
	DfpCiaAbertaDfcMdIndReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.dfp.dfc_mi_con import (
	DfpCiaAbertaDfcMiConReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.dfp.dfc_mi_ind import (
	DfpCiaAbertaDfcMiIndReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.dfp.dfp import (
	DfpCiaAbertaReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.dfp.dmpl_con import (
	DfpCiaAbertaDmplConReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.dfp.dmpl_ind import (
	DfpCiaAbertaDmplIndReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.dfp.dra_con import (
	DfpCiaAbertaDraConReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.dfp.dra_ind import (
	DfpCiaAbertaDraIndReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.dfp.dre_con import (
	DfpCiaAbertaDreConReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.dfp.dre_ind import (
	DfpCiaAbertaDreIndReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.dfp.dva_con import (
	DfpCiaAbertaDvaConReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.dfp.dva_ind import (
	DfpCiaAbertaDvaIndReader,
)
from opendata_cvm.ingestion.cia_aberta.doc.dfp.meta import MetaDfpCiaAbertaReader
from opendata_cvm.ingestion.cia_aberta.doc.dfp.parecer import (
	DfpCiaAbertaParecerReader,
)


__all__ = [
	"DfpCiaAbertaBpaConReader",
	"DfpCiaAbertaBpaIndReader",
	"DfpCiaAbertaBppConReader",
	"DfpCiaAbertaBppIndReader",
	"DfpCiaAbertaComposicaoCapitalReader",
	"DfpCiaAbertaDfcMdConReader",
	"DfpCiaAbertaDfcMdIndReader",
	"DfpCiaAbertaDfcMiConReader",
	"DfpCiaAbertaDfcMiIndReader",
	"DfpCiaAbertaDmplConReader",
	"DfpCiaAbertaDmplIndReader",
	"DfpCiaAbertaDraConReader",
	"DfpCiaAbertaDraIndReader",
	"DfpCiaAbertaDreConReader",
	"DfpCiaAbertaDreIndReader",
	"DfpCiaAbertaDvaConReader",
	"DfpCiaAbertaDvaIndReader",
	"DfpCiaAbertaParecerReader",
	"DfpCiaAbertaReader",
	"MetaDfpCiaAbertaReader",
]
