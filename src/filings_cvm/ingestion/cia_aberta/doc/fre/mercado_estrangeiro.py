"""CVM FRE CIA_ABERTA (mercado estrangeiro) — ingestion (leitura) reader.

Securities admitted to trading on foreign markets — depositary bank, custodian and the
certificate proportion. Only 11 rows in 2025, and the member with the most date columns in this
slice.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import (
	FRE_CIA_ABERTA_MERCADO_ESTRANGEIRO,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaMercadoEstrangeiroReader(_BaseFreReader):
	"""Read the FRE CIA_ABERTA `mercado estrangeiro` member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_mercado_estrangeiro"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_MERCADO_ESTRANGEIRO
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Emissao",
		"Data_Inicio_Listagem",
	)
	_LABEL: ClassVar[str] = "mercado estrangeiro"
