"""CVM Complemento FI -- main member reader.

The ``compl_fi`` member of ``compl_fi_AAAAMM.zip`` (dataset ``FI/DOC/COMPL``): 20 columns of
policy text (risk, voting, rating agency, distribution). Months ``201801``-``201904`` only.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import COMPL_FI, FileContract
from filings_cvm.ingestion.fi.doc.compl._base_compl_reader import _BaseComplReader


class ComplFiReader(_BaseComplReader):
	"""Read the Complemento FI main member (`compl_fi`) into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "compl_fi"
	_CONTRACT: ClassVar[FileContract] = COMPL_FI
	_LABEL: ClassVar[str] = "policy"
