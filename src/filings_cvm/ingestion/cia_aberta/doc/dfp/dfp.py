"""CVM DFP CIA_ABERTA (índice dos formulários) — ingestion (leitura) reader.

One row per DFP filing delivered in the year: who filed, when, and a `LINK_DOC`
pointing at the document on CVM's RAD portal (host `http://www.rad.cvm.gov.br`). The link is
returned as **text and never followed** — this is the index, not the statements.

⚠️ `CD_CVM` arrives with a **leading zero** (`001023`) and is therefore text; a numeric type would
drop it silently.

Download/unzip/parse is inherited from the private `_BaseDfpReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.dfp_cia_aberta import (
	DFP_CIA_ABERTA,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.dfp._base_dfp_reader import _BaseDfpReader


class DfpCiaAbertaReader(_BaseDfpReader):
	"""Read this DFP CIA_ABERTA member into a typed DataFrame.

	Covers `índice dos formulários`.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "dfp_cia_aberta"
	_CONTRACT: ClassVar[FileContract] = DFP_CIA_ABERTA
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"DT_REFER",
		"DT_RECEB",
	)
	_LABEL: ClassVar[str] = "índice dos formulários"
