"""CVM FRE CIA_ABERTA (ações entregues) — ingestion (leitura) reader.

Shares actually delivered under share-based compensation plans, per company and organ.

⚠️ **Fourteen columns, and two siblings have fourteen too.** `remuneracao_acao` and
`remuneracao_maxima_minima_media` share this member's first ten columns and differ only in the
last four; the contract is generated from *this* member's own header.

`Quantidade_*`, `Preco_*` and `Valor_*` stay **exact source text** — money and counts, never a
binary float; convert to `Decimal` downstream.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import (
	FRE_CIA_ABERTA_ACAO_ENTREGUE,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaAcaoEntregueReader(_BaseFreReader):
	"""Read this FRE CIA_ABERTA remuneração/valores-mobiliários member into a typed DataFrame.

	Covers `ações entregues`.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_acao_entregue"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_ACAO_ENTREGUE
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Inicio_Exercicio_Social",
		"Data_Fim_Exercicio_Social",
	)
	_LABEL: ClassVar[str] = "ações entregues"
