"""CVM DFP CIA_ABERTA (composição do capital) — ingestion (leitura) reader.

Share counts per filing: ordinary, preferred and total shares, both issued and
held in treasury.

⚠️ The `QT_ACAO_*` columns are counts and stay **exact source text**, never binary floats.

Download/unzip/parse is inherited from the private `_BaseDfpReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.dfp_cia_aberta import (
	DFP_CIA_ABERTA_COMPOSICAO_CAPITAL,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.dfp._base_dfp_reader import _BaseDfpReader


class DfpCiaAbertaComposicaoCapitalReader(_BaseDfpReader):
	"""Read this DFP CIA_ABERTA member into a typed DataFrame.

	Covers `composição do capital`.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "dfp_cia_aberta_composicao_capital"
	_CONTRACT: ClassVar[FileContract] = DFP_CIA_ABERTA_COMPOSICAO_CAPITAL
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REFER",)
	_LABEL: ClassVar[str] = "composição do capital"
