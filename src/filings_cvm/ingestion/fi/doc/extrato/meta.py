"""CVM **META** for the FI Extrato dataset (`FI/DOC/EXTRATO`).

The spec CVM publishes for the dataset — the declared description, type and size of each field. A
flat `.txt` and the **only** file in the dataset's `META/` directory (measured from the
listing), so the URL is pinned rather than derived from a naming rule.

Its **117 fields equal the current header exactly** (zero on either side, measured), so it
covers the 2020-onward yearly artifact and the snapshot — but **not** the 116-column pre-2020
contract, which is pinned to its own published header instead.

Useful as a type oracle, and it settled two calls: exactly **one** field is `date` (`DT_COMPTC`),
which is why `PRAZO` — full of `DD/MM/YYYY` strings — stays text; and **74 `numeric` + 4 `decimal`
+ 4 `int`** fields are why everything else is kept as exact source text rather than parsed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_EXTRATO_FI
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaExtratoFiReader(BaseMetaReader):
	"""Read the META of the CVM FI Extrato dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/FI/DOC/EXTRATO/META/meta_extrato_fi.txt"
	)
	_CONTRACT: ClassVar[FileContract] = META_EXTRATO_FI
