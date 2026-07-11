"""CVM Informe Mensal FIDC readers — the 17 table members of ``inf_mensal_fidc_AAAAMM.zip``.

One reader per table of the FIDC monthly report (Tabelas I–X plus X's sub-tables), over a shared
private base (`_base_inf_mensal_fidc_reader`). Re-exported from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_i import InfMensalFidcTabIReader
from filings_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_ii import (
	InfMensalFidcTabIIReader,
)
from filings_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_iii import (
	InfMensalFidcTabIIIReader,
)
from filings_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_iv import (
	InfMensalFidcTabIVReader,
)
from filings_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_ix import (
	InfMensalFidcTabIXReader,
)
from filings_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_v import InfMensalFidcTabVReader
from filings_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_vi import (
	InfMensalFidcTabVIReader,
)
from filings_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_vii import (
	InfMensalFidcTabVIIReader,
)
from filings_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_x import InfMensalFidcTabXReader
from filings_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_x_1 import (
	InfMensalFidcTabX1Reader,
)
from filings_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_x_1_1 import (
	InfMensalFidcTabX11Reader,
)
from filings_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_x_2 import (
	InfMensalFidcTabX2Reader,
)
from filings_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_x_3 import (
	InfMensalFidcTabX3Reader,
)
from filings_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_x_4 import (
	InfMensalFidcTabX4Reader,
)
from filings_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_x_5 import (
	InfMensalFidcTabX5Reader,
)
from filings_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_x_6 import (
	InfMensalFidcTabX6Reader,
)
from filings_cvm.ingestion.fidc.doc.inf_mensal.inf_mensal_fidc_tab_x_7 import (
	InfMensalFidcTabX7Reader,
)


__all__ = [
	"InfMensalFidcTabIIIReader",
	"InfMensalFidcTabIIReader",
	"InfMensalFidcTabIReader",
	"InfMensalFidcTabIVReader",
	"InfMensalFidcTabIXReader",
	"InfMensalFidcTabVIIReader",
	"InfMensalFidcTabVIReader",
	"InfMensalFidcTabVReader",
	"InfMensalFidcTabX11Reader",
	"InfMensalFidcTabX1Reader",
	"InfMensalFidcTabX2Reader",
	"InfMensalFidcTabX3Reader",
	"InfMensalFidcTabX4Reader",
	"InfMensalFidcTabX5Reader",
	"InfMensalFidcTabX6Reader",
	"InfMensalFidcTabX7Reader",
	"InfMensalFidcTabXReader",
]
