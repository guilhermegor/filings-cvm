"""CVM Balancete FI (fund/class regime) -- ingestion (leitura) reader.

Reads `balancete_fi_AAAAMM.zip` (dataset `FI/DOC/BALANCETE`) for `202311` onward -- **6 columns**,
keyed by `TP_FUNDO_CLASSE` + `CNPJ_FUNDO_CLASSE`. For `201501`-`202310` use
:class:`BalanceteFiPre202311Reader`, whose 5-column header has a single `CNPJ_FUNDO`.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.balancete_fi import BALANCETE_FI
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.fi.doc.balancete._base_balancete_reader import _BaseBalanceteReader


class BalanceteFiReader(_BaseBalanceteReader):
	"""Read the CVM Balancete FI monthly dump (`202311` onward) into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip and parse the reference month's balancete (inherited).
	"""

	_CONTRACT: ClassVar[FileContract] = BALANCETE_FI
	_LABEL: ClassVar[str] = "fund/class"
	_SIBLING: ClassVar[str] = "BalanceteFiPre202311Reader"

	# Cut measured over the published headers; legacy ends one month earlier.
	_FIRST_YM: ClassVar[int | None] = 202311
	_LAST_YM: ClassVar[int | None] = None
