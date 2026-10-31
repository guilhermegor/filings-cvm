"""CVM Complemento FI -- unitholder-information member reader.

The ``compl_fi_inf_cotst`` member (7 columns): how information reaches unitholders and who
answers for it. Months ``201801``-``201904`` only.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import COMPL_FI_INF_COTST, FileContract
from filings_cvm.ingestion.fi.doc.compl._base_compl_reader import _BaseComplReader


class ComplFiInfCotstReader(_BaseComplReader):
	"""Read the Complemento FI unitholder member (`compl_fi_inf_cotst`) into a DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "compl_fi_inf_cotst"
	_CONTRACT: ClassVar[FileContract] = COMPL_FI_INF_COTST
	_LABEL: ClassVar[str] = "unitholder information"
