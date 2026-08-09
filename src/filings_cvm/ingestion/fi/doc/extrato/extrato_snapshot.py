"""CVM Extrato FI snapshot — ingestion (leitura) reader.

Reads `extrato_fi.csv` (dataset `FI/DOC/EXTRATO`) — the **latest extrato of each fund/class**, at a
fixed URL with no year in the name, so this reader takes **no `date_ref`**. CVM overwrites the file
in place; persist `path_raw` to keep a day's snapshot.

⚠️ **The unpartitioned name invites the wrong reading.** It is *not* the accumulated series: it is
one row per fund. Measured on the published file — 38.454 rows over **38.454 distinct**
`CNPJ_FUNDO_CLASSE`, with `DT_COMPTC` spanning 2015–2026 because each fund carries the date of *its
own* last filing. Every row also appears in the matching yearly file (0 rows present only here),
while the yearly files carry far more. "Latest" is verified, not assumed: across the 2.469 funds
that filed more than once in 2025, the snapshot date equals that year's maximum or is later —
**zero** counter-examples.

⚠️ **This is the one reader in the library that asserts a unique key.** One row per
`CNPJ_FUNDO_CLASSE` is a measured property of *this artifact*; it does **not** hold for
:class:`ExtratoFiReader`, whose grain is the filing.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.extrato_fi import EXTRATO_FI_SNAPSHOT
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.fi.doc.extrato._base_extrato_reader import _BaseExtratoReader


class ExtratoFiSnapshotReader(_BaseExtratoReader):
	"""Read the CVM Extrato FI snapshot into a typed DataFrame.

	Concrete :class:`IngestionReader` for `extrato_fi.csv` — **one row per fund/class**, carrying
	that fund's most recent extrato.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the snapshot into a validated DataFrame (inherited).
	"""

	_CONTRACT: ClassVar[FileContract] = EXTRATO_FI_SNAPSHOT
	_LABEL: ClassVar[str] = "snapshot"
