"""CVM Complemento FI -- information-disclosure member reader.

The ``compl_fi_inf`` member (6 columns): by which means, where and how the fund discloses
information. Months ``201801``-``201904`` only.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import COMPL_FI_INF, FileContract
from filings_cvm.ingestion.fi.doc.compl._base_compl_reader import _BaseComplReader


class ComplFiInfReader(_BaseComplReader):
	"""Read the Complemento FI information member (`compl_fi_inf`) into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "compl_fi_inf"
	_CONTRACT: ClassVar[FileContract] = COMPL_FI_INF
	_LABEL: ClassVar[str] = "information"
