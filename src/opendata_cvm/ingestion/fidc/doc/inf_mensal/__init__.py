"""CVM Informe Mensal FIDC readers — the 18 table members of ``inf_mensal_fidc_AAAAMM.zip``.

One reader per table of the FIDC monthly report (Tabelas I–X plus X's sub-tables), over a shared
private base (`_base_inf_mensal_fidc_reader`), plus its META reader. Re-exported from
`opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_i import (
	InfMensalFidcTabIReader,
)
from opendata_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_ii import (
	InfMensalFidcTabIIReader,
)
from opendata_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_iii import (
	InfMensalFidcTabIIIReader,
)
from opendata_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_iv import (
	InfMensalFidcTabIVReader,
)
from opendata_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_ix import (
	InfMensalFidcTabIXReader,
)
from opendata_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_v import (
	InfMensalFidcTabVReader,
)
from opendata_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_vi import (
	InfMensalFidcTabVIReader,
)
from opendata_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_vii import (
	InfMensalFidcTabVIIReader,
)
from opendata_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_viii import (
	InfMensalFidcTabVIIIReader,
)
from opendata_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_x import (
	InfMensalFidcTabXReader,
)
from opendata_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_x_1 import (
	InfMensalFidcTabX1Reader,
)
from opendata_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_x_1_1 import (
	InfMensalFidcTabX11Reader,
)
from opendata_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_x_2 import (
	InfMensalFidcTabX2Reader,
)
from opendata_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_x_3 import (
	InfMensalFidcTabX3Reader,
)
from opendata_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_x_4 import (
	InfMensalFidcTabX4Reader,
)
from opendata_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_x_5 import (
	InfMensalFidcTabX5Reader,
)
from opendata_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_x_6 import (
	InfMensalFidcTabX6Reader,
)
from opendata_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_x_7 import (
	InfMensalFidcTabX7Reader,
)
from opendata_cvm.ingestion.fidc.doc.inf_mensal.meta import MetaInfMensalFidcReader


__all__ = [
	"InfMensalFidcTabIIIReader",
	"InfMensalFidcTabIIReader",
	"InfMensalFidcTabIReader",
	"InfMensalFidcTabIVReader",
	"InfMensalFidcTabIXReader",
	"InfMensalFidcTabVIIIReader",
	"InfMensalFidcTabVIIReader",
	"InfMensalFidcTabVIReader",
	"InfMensalFidcTabVReader",
	"InfMensalFidcTabX1Reader",
	"InfMensalFidcTabX2Reader",
	"InfMensalFidcTabX3Reader",
	"InfMensalFidcTabX4Reader",
	"InfMensalFidcTabX5Reader",
	"InfMensalFidcTabX6Reader",
	"InfMensalFidcTabX7Reader",
	"InfMensalFidcTabX11Reader",
	"InfMensalFidcTabXReader",
	"MetaInfMensalFidcReader",
]
