"""CVM FRE CIA_ABERTA (posição acionária por classe de ação) — ingestion reader.

The preferred-share breakdown of the shareholder base: for each holder, how many shares of each
preferred class they hold. Joins back to `posicao_acionaria` on `ID_Acionista`.

⚠️ **The only member of this slice with no personal data** — it identifies the holder by
`ID_Acionista` alone, carrying neither a name nor a document. The single CNPJ column is the filing
company's.

`Quantidade_Acoes` and `Percentual_Acoes` stay exact text — never a binary float; convert
downstream.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import (
	FRE_CIA_ABERTA_POSICAO_ACIONARIA_CLASSE_ACAO,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaPosicaoAcionariaClasseAcaoReader(_BaseFreReader):
	"""Read the FRE CIA_ABERTA `posição acionária por classe` member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_posicao_acionaria_classe_acao"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_POSICAO_ACIONARIA_CLASSE_ACAO
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "posição acionária por classe"
