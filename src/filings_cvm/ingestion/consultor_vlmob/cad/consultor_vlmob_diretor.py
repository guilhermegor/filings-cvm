"""CVM CONSULTOR_VLMOB/CAD — managing-director table reader.

The ``cad_consultor_vlmob_diretor.csv`` member of ``cad_consultor_vlmob.zip``: one row per managing
director of a securities-consultant firm (the firm's ``CNPJ``, the director's name, and whether
they are the default director). ⚠️ Carries personal data (``DIRETOR``) but **no CPF column**, and
**no date column at all** — so ``_DATE_COLS`` is empty and every column is exact source text. See
``_base_consultor_vlmob_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_CONSULTOR_VLMOB_DIRETOR, FileContract
from filings_cvm.ingestion.consultor_vlmob.cad._base_consultor_vlmob_reader import (
	_BaseConsultorVlmobReader,
)


class ConsultorVlmobDiretorReader(_BaseConsultorVlmobReader):
	"""Read the CONSULTOR_VLMOB/CAD managing-director table into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_consultor_vlmob_diretor.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_CONSULTOR_VLMOB_DIRETOR
	_DATE_COLS: ClassVar[tuple[str, ...]] = ()
	_LABEL: ClassVar[str] = "diretor"
