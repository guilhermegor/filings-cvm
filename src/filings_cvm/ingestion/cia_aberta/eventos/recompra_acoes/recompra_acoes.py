"""CVM CIA_ABERTA/EVENTOS/RECOMPRA_ACOES (programas de recompra) — ingestion (leitura) reader.

One row per buy-back **programme**: the company, when it was resolved and
when the window closes, the operation type and purpose, and the share counts.

`ID_Programa` is unique here (1.916 distinct values in 1.916 rows) and is the key the two satellite
members join on. It is an identifier, so it stays text.

⚠️ The series runs from **1997** in a single snapshot — CVM overwrites the file in place, so a
persisted `path_raw` is the only record of what it said on a given day.

⚠️ `Tipo_Operacao`, `Motivo`, `Finalidade_Compra` and both `Quantidade_*` columns arrive
**partially empty**; blank stays blank, never a placeholder or a zero.

Download/unzip/parse is inherited from the private `_BaseRecompraAcoesReader`; this module only
declares which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.cia_aberta_recompra_acoes import (
	CIA_ABERTA_RECOMPRA_ACOES,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.eventos.recompra_acoes._base_recompra_acoes_reader import (
	_BaseRecompraAcoesReader,
)


class RecompraAcoesReader(_BaseRecompraAcoesReader):
	"""Read this RECOMPRA_ACOES member into a typed DataFrame.

	Covers `programas de recompra`.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the member (inherited).
	"""

	_MEMBER: ClassVar[str] = "cia_aberta_recompra_acoes.csv"
	_CONTRACT: ClassVar[FileContract] = CIA_ABERTA_RECOMPRA_ACOES
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Deliberacao",
		"Data_Final_Prazo",
	)
	_LABEL: ClassVar[str] = "programas de recompra"
