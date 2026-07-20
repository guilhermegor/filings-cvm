"""CVM CONSULTOR_VLMOB/CAD — legal-person (pessoa jurídica) consultant registry reader.

The ``cad_consultor_vlmob_pj.csv`` member of ``cad_consultor_vlmob.zip``: the registry of
securities-consultant firms (masked CNPJ, corporate and commercial names, dates/reason/situation,
shareholding control, address, phone, e-mail, website). Unlike ADM_CART's ``pj`` it has no
``DT_PATRIM_LIQ``, so only three date columns. See ``_base_consultor_vlmob_reader`` for the shared
behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_CONSULTOR_VLMOB_PJ, FileContract
from filings_cvm.ingestion.consultor_vlmob.cad._base_consultor_vlmob_reader import (
	_BaseConsultorVlmobReader,
)


class ConsultorVlmobPjReader(_BaseConsultorVlmobReader):
	"""Read the CONSULTOR_VLMOB/CAD *pessoa jurídica* registry into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_consultor_vlmob_pj.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_CONSULTOR_VLMOB_PJ
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REG", "DT_CANCEL", "DT_INI_SIT")
	_LABEL: ClassVar[str] = "pessoa jurídica"
