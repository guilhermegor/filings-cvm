"""CVM FRE CIA_ABERTA (outros valores mobiliários) — ingestion (leitura) reader.

Securities other than shares issued by the company, with their terms.

⚠️ **Three columns arrive 100% empty in 2025** — `Quantidade_Pessoa_Fisica`,
`Quantidade_Pessoa_Juridica` and `Quantidade_Investidor_Institucional`. They are declared
`numeric` by the dataset's META and are returned as exact text like every other count, so an
empty column is empty, never zero.

`Quantidade`, `Valor` and `Saldo_Devedor` stay **exact source text**; convert to `Decimal`
downstream.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import (
	FRE_CIA_ABERTA_OUTRO_VALOR_MOBILIARIO,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaOutroValorMobiliarioReader(_BaseFreReader):
	"""Read this FRE CIA_ABERTA remuneração/valores-mobiliários member into a typed DataFrame.

	Covers `outros valores mobiliários`.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_outro_valor_mobiliario"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_OUTRO_VALOR_MOBILIARIO
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Emissao",
		"Data_Vencimento",
	)
	_LABEL: ClassVar[str] = "outros valores mobiliários"
