"""CVM FRE CIA_ABERTA (distribuição do capital) — ingestion (leitura) reader.

How the capital is distributed: counts of individual, corporate and institutional shareholders,
and the free-float share counts and percentages.

``Data_Ultima_Assembleia`` is blank in a couple of rows, so it becomes ``NaT`` rather than
raising.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import (
	FRE_CIA_ABERTA_DISTRIBUICAO_CAPITAL,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaDistribuicaoCapitalReader(_BaseFreReader):
	"""Read the FRE CIA_ABERTA `distribuição do capital` member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_distribuicao_capital"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_DISTRIBUICAO_CAPITAL
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Ultima_Assembleia",
	)
	_LABEL: ClassVar[str] = "distribuição do capital"
