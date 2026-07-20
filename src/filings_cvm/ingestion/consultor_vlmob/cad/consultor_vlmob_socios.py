"""CVM CONSULTOR_VLMOB/CAD — partner table reader.

The ``cad_consultor_vlmob_socios.csv`` member of ``cad_consultor_vlmob.zip``: one row per partner
of a securities-consultant firm (the firm's ``CNPJ`` and the partner's name). ⚠️ ``SOCIOS`` is
personal data, but there is **no CPF column**, and **no date column at all** — so ``_DATE_COLS`` is
empty and every column is source text. See ``_base_consultor_vlmob_reader`` for shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_CONSULTOR_VLMOB_SOCIOS, FileContract
from filings_cvm.ingestion.consultor_vlmob.cad._base_consultor_vlmob_reader import (
	_BaseConsultorVlmobReader,
)


class ConsultorVlmobSociosReader(_BaseConsultorVlmobReader):
	"""Read the CONSULTOR_VLMOB/CAD partner table into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_consultor_vlmob_socios.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_CONSULTOR_VLMOB_SOCIOS
	_DATE_COLS: ClassVar[tuple[str, ...]] = ()
	_LABEL: ClassVar[str] = "sócio"
