"""CVM DFP CIA_ABERTA (valor adicionado (individual)) — ingestion (leitura) reader.

One row per account line of the statement, for the current period and the
comparative one — `ORDEM_EXERC` (`ÚLTIMO` / `PENÚLTIMO`) distinguishes them, so **no unique key is
asserted**.

⚠️ `VL_CONTA` is money with ten decimal places and stays **exact source text**; ⚠️⚠️ its scale is
in `ESCALA_MOEDA` (`MIL` / `UNIDADE`), a *different column* — summing values without reading it is
wrong by a factor of a thousand. The reader does not rescale.

⚠️ This member's column list is **shared verbatim with its siblings of the same shape** — measured,
not assumed, and pinned to this member's own published header.

Download/unzip/parse is inherited from the private `_BaseDfpReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.dfp_cia_aberta import (
	DFP_CIA_ABERTA_DVA_IND,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.dfp._base_dfp_reader import _BaseDfpReader


class DfpCiaAbertaDvaIndReader(_BaseDfpReader):
	"""Read this DFP CIA_ABERTA member into a typed DataFrame.

	Covers `valor adicionado (individual)`.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "dfp_cia_aberta_DVA_ind"
	_CONTRACT: ClassVar[FileContract] = DFP_CIA_ABERTA_DVA_IND
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"DT_REFER",
		"DT_INI_EXERC",
		"DT_FIM_EXERC",
	)
	_LABEL: ClassVar[str] = "valor adicionado (individual)"
