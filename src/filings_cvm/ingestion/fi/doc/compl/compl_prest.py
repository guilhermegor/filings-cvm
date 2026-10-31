"""CVM Complemento FI -- service-provider member reader.

The ``compl_fi_prest`` member (5 columns): service description and provider name. Months
``201801``-``201904`` only.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import COMPL_FI_PREST, FileContract
from filings_cvm.ingestion.fi.doc.compl._base_compl_reader import _BaseComplReader


class ComplFiPrestReader(_BaseComplReader):
	"""Read the Complemento FI provider member (`compl_fi_prest`) into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "compl_fi_prest"
	_CONTRACT: ClassVar[FileContract] = COMPL_FI_PREST
	_LABEL: ClassVar[str] = "service provider"
