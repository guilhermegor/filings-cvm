"""CVM FRE CIA_ABERTA (títulos conversíveis) — ingestion (leitura) reader.

Securities convertible into shares and the conditions of conversion — the smallest member of
this slice (26 rows in 2025).

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import (
	FRE_CIA_ABERTA_CAPITAL_SOCIAL_TITULO_CONVERSIVEL,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaCapitalSocialTituloConversivelReader(_BaseFreReader):
	"""Read the FRE CIA_ABERTA `títulos conversíveis` member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_capital_social_titulo_conversivel"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_CAPITAL_SOCIAL_TITULO_CONVERSIVEL
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "títulos conversíveis"
