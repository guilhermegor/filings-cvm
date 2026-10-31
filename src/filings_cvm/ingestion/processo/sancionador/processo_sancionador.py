"""CVM PROCESSO/SANCIONADOR — sanctioning-proceedings reader.

The ``processo_sancionador.csv`` member of ``processo_sancionador.zip``: one row per proceeding,
keyed by the unique ``NUP``, with its object, summary (``Ementa``, empty for ~35%), current phase
and location. Holds no personal data — the accused are in the sibling member. See
``_base_processo_sancionador_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import PROCESSO_SANCIONADOR, FileContract
from filings_cvm.ingestion.processo.sancionador._base_processo_sancionador_reader import (
	_BaseProcessoSancionadorReader,
)


class ProcessoSancionadorReader(_BaseProcessoSancionadorReader):
	"""Read the PROCESSO/SANCIONADOR proceedings table into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "processo_sancionador.csv"
	_CONTRACT: ClassVar[FileContract] = PROCESSO_SANCIONADOR
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Abertura", "Data_Ultima_Movimentacao")
	_LABEL: ClassVar[str] = "processo sancionador"
