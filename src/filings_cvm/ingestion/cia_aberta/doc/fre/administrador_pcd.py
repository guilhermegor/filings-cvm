"""CVM FRE CIA_ABERTA (administradores PCD) — ingestion (leitura) reader.

How many administrators of each governance organ declared themselves as a person with a disability.

⚠️ **Aggregate counts, not personal data.** Despite the member name, every row is a **total per
company** and grouping — no individual is identified anywhere in it. The FRE members that do carry
personal data are the administração/pessoas ones.

⚠️ The three `Quantidade_*` columns arrive **partly blank** (roughly a fifth of the rows in
2025), and `Nao_Aplicavel` flags a company that declared the breakdown does not apply. A
blank count is *not* a zero — it is an absent declaration, and it stays empty text.

`Quantidade_*` columns stay **exact source text** — counts, never a binary float; convert
downstream.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import (
	FRE_CIA_ABERTA_ADMINISTRADOR_PCD,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaAdministradorPcdReader(_BaseFreReader):
	"""Read this FRE CIA_ABERTA diversidade member into a typed DataFrame.

	Covers `administradores PCD`.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_administrador_PCD"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_ADMINISTRADOR_PCD
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "administradores PCD"
