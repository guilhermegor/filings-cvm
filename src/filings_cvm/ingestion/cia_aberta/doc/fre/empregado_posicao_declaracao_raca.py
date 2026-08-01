"""CVM FRE CIA_ABERTA (raça declarada (empregados por posição)) — ingestion (leitura) reader.

Race/colour counts declared for employees, grouped by job **position** (`Posicao`).

⚠️ **Aggregate counts, not personal data.** Despite the member name, every row is a **total per
company** and grouping — no individual is identified anywhere in it. The FRE members that do carry
personal data are the administração/pessoas ones.

The position-grouped twin of the `local` member: identical buckets, different grain.

`Quantidade_*` columns stay **exact source text** — counts, never a binary float; convert
downstream.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import (
	FRE_CIA_ABERTA_EMPREGADO_POSICAO_DECLARACAO_RACA,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaEmpregadoPosicaoDeclaracaoRacaReader(_BaseFreReader):
	"""Read this FRE CIA_ABERTA diversidade member into a typed DataFrame.

	Covers `raça declarada (empregados por posição)`.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_empregado_posicao_declaracao_raca"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_EMPREGADO_POSICAO_DECLARACAO_RACA
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "raça declarada (empregados por posição)"
