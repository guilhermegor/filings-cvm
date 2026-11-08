"""CVM PROCESSO/SANCIONADOR — accused-parties reader.

The ``processo_sancionador_acusado.csv`` member of ``processo_sancionador.zip``: one row per
accused party of a proceeding, keyed by ``NUP`` (repeated — a proceeding has several accused).
Carries personal data (``Nome_Acusado`` names natural and legal persons) but **no CPF/CNPJ
column**. See ``_base_processo_sancionador_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import PROCESSO_SANCIONADOR_ACUSADO, FileContract
from filings_cvm.ingestion.processo.sancionador._base_processo_sancionador_reader import (
	_BaseProcessoSancionadorReader,
)


class ProcessoSancionadorAcusadoReader(_BaseProcessoSancionadorReader):
	"""Read the PROCESSO/SANCIONADOR accused-parties table into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "processo_sancionador_acusado.csv"
	_CONTRACT: ClassVar[FileContract] = PROCESSO_SANCIONADOR_ACUSADO
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Situacao",)
	_LABEL: ClassVar[str] = "acusado de processo sancionador"
