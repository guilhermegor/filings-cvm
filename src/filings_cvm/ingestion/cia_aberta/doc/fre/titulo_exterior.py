"""CVM FRE CIA_ABERTA (títulos emitidos no exterior) — ingestion (leitura) reader.

Securities the company issued abroad, with their terms.

⚠️ **Same width as `participacao_sociedade` (21 columns) and almost nothing in common with it** —
the two are grouped here by theme, not by shape, and each contract comes from its own header.

⚠️ Its terms columns are near-synonyms of `outro_valor_mobiliario`'s but **spelled differently**
(`Condicao_Conversibilidade` vs `Condicao_Conversibilidade_Efeito_Capital_Social`,
`Caracteristicas_Divida` vs `Caracteristicas_Valores_Mobiliarios_Divida`) — preserved verbatim.

`Quantidade`, `Valor_Nominal` and `Saldo_Devedor` stay **exact source text**.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import (
	FRE_CIA_ABERTA_TITULO_EXTERIOR,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaTituloExteriorReader(_BaseFreReader):
	"""Read this FRE CIA_ABERTA remuneração/valores-mobiliários member into a typed DataFrame.

	Covers `títulos emitidos no exterior`.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_titulo_exterior"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_TITULO_EXTERIOR
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Emissao",
		"Data_Vencimento",
	)
	_LABEL: ClassVar[str] = "títulos emitidos no exterior"
