"""CVM Balancete FI (legacy regime) -- ingestion (leitura) reader.

Reads `balancete_fi_AAAAMM.zip` (dataset `FI/DOC/BALANCETE`) for `201501` through `202310` --
**5 columns**, keyed by a single `CNPJ_FUNDO`. From `202311` use :class:`BalanceteFiReader`.

The name carries the measured cut month, not a regulation: the cut is one month before the Perfil
Mensal's `202312`.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.balancete_fi import BALANCETE_FI_PRE202311
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.fi.doc.balancete._base_balancete_reader import _BaseBalanceteReader


class BalanceteFiPre202311Reader(_BaseBalanceteReader):
	"""Read the legacy CVM Balancete FI monthly dump (`201501`-`202310`) into a DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip and parse the reference month's balancete (inherited).
	"""

	_CONTRACT: ClassVar[FileContract] = BALANCETE_FI_PRE202311
	_LABEL: ClassVar[str] = "legacy"
	_SIBLING: ClassVar[str] = "BalanceteFiReader"

	_FIRST_YM: ClassVar[int | None] = 201501
	_LAST_YM: ClassVar[int | None] = 202310
