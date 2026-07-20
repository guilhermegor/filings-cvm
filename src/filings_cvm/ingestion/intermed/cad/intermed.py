"""CVM INTERMED/CAD — market-intermediary registry reader.

The ``cad_intermed.csv`` member of ``cad_intermed.zip``: the registry of market intermediaries
(masked CNPJ, corporate and commercial names, dates/reason/situation, CVM code, activity sector,
shareholding control, net worth, address, phone, fax, e-mail, website). See
``_base_intermed_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_INTERMED, FileContract
from filings_cvm.ingestion.intermed.cad._base_intermed_reader import _BaseIntermedReader


class IntermedReader(_BaseIntermedReader):
	"""Read the INTERMED/CAD intermediary registry into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_intermed.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_INTERMED
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"DT_REG",
		"DT_CANCEL",
		"DT_INI_SIT",
		"DT_PATRIM_LIQ",
	)
	_LABEL: ClassVar[str] = "intermediário"
