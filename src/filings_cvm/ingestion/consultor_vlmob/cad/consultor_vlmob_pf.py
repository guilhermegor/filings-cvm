"""CVM CONSULTOR_VLMOB/CAD — natural-person (pessoa física) consultant registry reader.

The ``cad_consultor_vlmob_pf.csv`` member of ``cad_consultor_vlmob.zip``: the registry of
individual securities consultants (name, dates/reason/situation, website). **No CNPJ, no CPF** —
the registry identifies a person consultant by ``NOME`` alone. See
``_base_consultor_vlmob_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_CONSULTOR_VLMOB_PF, FileContract
from filings_cvm.ingestion.consultor_vlmob.cad._base_consultor_vlmob_reader import (
	_BaseConsultorVlmobReader,
)


class ConsultorVlmobPfReader(_BaseConsultorVlmobReader):
	"""Read the CONSULTOR_VLMOB/CAD *pessoa física* registry into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_consultor_vlmob_pf.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_CONSULTOR_VLMOB_PF
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REG", "DT_CANCEL", "DT_INI_SIT")
	_LABEL: ClassVar[str] = "pessoa física"
