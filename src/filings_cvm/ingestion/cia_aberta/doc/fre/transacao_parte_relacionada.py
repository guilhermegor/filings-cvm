"""CVM FRE CIA_ABERTA (transações com partes relacionadas) — ingestion (leitura) reader.

Related-party transactions: counterparty, amounts, terms and the issuer's position.

⚠️⚠️ **`Documento_Parte_Relacionada` is NOT declared a CNPJ column**, even though it is 100% empty
in 2025 and would therefore pass. Its sibling `Tipo_Pessoa` has domain **`PF/PJ`** in the META, so
the column holds a **CPF or a CNPJ** depending on the row — the same shape as
`relacao_subordinacao.Documento_Pessoa_Relacionada` in the administração slice, which holds both.
Declaring it would pass every empty year and fail the first year with data.

⚠️ **`Duracao_Transacao` is free text, not a date**, although 879 of its 11.238 values look like
`DD/MM/YYYY`. The META types it `varchar`; it stays exact text and is never coerced.

`Montante_*` and `Saldo_Existente` stay **exact source text** — money, never a binary float.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import (
	FRE_CIA_ABERTA_TRANSACAO_PARTE_RELACIONADA,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaTransacaoParteRelacionadaReader(_BaseFreReader):
	"""Read this FRE CIA_ABERTA remuneração/valores-mobiliários member into a typed DataFrame.

	Covers `transações com partes relacionadas`.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_transacao_parte_relacionada"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_TRANSACAO_PARTE_RELACIONADA
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Transacao",
	)
	_LABEL: ClassVar[str] = "transações com partes relacionadas"
