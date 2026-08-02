"""CVM FRE CIA_ABERTA (titulares de valores mobiliários) — ingestion (leitura) reader.

Holder counts per security class: natural persons, legal persons and institutional
investors.

⚠️ **Aggregate counts, not holders.** The member names *titulares* but every row is a **total**;
no holder is identified, so it carries no personal data.

The narrowest member of the slice (9 columns) and the only one with a single date column.
`Quantidade_*` stays **exact source text**.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import (
	FRE_CIA_ABERTA_TITULAR_VALOR_MOBILIARIO,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaTitularValorMobiliarioReader(_BaseFreReader):
	"""Read this FRE CIA_ABERTA remuneração/valores-mobiliários member into a typed DataFrame.

	Covers `titulares de valores mobiliários`.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_titular_valor_mobiliario"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_TITULAR_VALOR_MOBILIARIO
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "titulares de valores mobiliários"
