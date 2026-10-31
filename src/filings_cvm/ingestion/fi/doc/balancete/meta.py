"""CVM **META** for the FI Balancete dataset (`FI/DOC/BALANCETE`).

The spec CVM publishes for `balancete_fi_AAAAMM.zip`: a flat `.txt`, `meta_balancete_fi.txt`.

⚠️ Its 6 fields equal the **fund/class** header (`202311` onward) and carry no `CNPJ_FUNDO`, so the
META is **not** an oracle for the legacy 5-column contract, which is pinned to its own header.
It declares `VL_SALDO_BALCTE` `numeric(23,2)`, `CD_CONTA_BALCTE` `char(8)` and `DT_COMPTC` `date`.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_BALANCETE_FI
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaBalanceteFiReader(BaseMetaReader):
	"""Read the META of the CVM FI Balancete dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/FI/DOC/BALANCETE/META/meta_balancete_fi.txt"
	)
	_CONTRACT: ClassVar[FileContract] = META_BALANCETE_FI
