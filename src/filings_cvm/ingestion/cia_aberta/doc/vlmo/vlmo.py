"""CVM VLMO CIA_ABERTA (índice) — ingestion (leitura) reader.

The **index** member of `vlmo_cia_aberta_AAAA.zip` (dataset `CIA_ABERTA/DOC/VLMO`): one row per
*Informe de Valores Mobiliários* a listed company filed in the year, carrying its reference and
delivery dates, the document's taxonomy, its protocol and version, and a `Link_Download` pointing
at the document on CVM's RAD portal.

**This is an index, not the document** — the reader returns the link as text and **does not follow
it**, the same as `IpeCiaAbertaReader`. The actual holdings/movements live in the sibling
`con` member (`VlmoCiaAbertaConReader`).

`Motivo_Reapresentacao` is the one column IPE's index does not have; it arrives mostly blank (452
of 5,812 rows in 2025) — a required *column*, not a required *value*.

Download/unzip/parse is inherited from the private `_BaseVlmoReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.vlmo_cia_aberta import VLMO_CIA_ABERTA
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.vlmo._base_vlmo_reader import _BaseVlmoReader


class VlmoCiaAbertaReader(_BaseVlmoReader):
	"""Read the index member of the CVM VLMO CIA_ABERTA yearly dump into a typed DataFrame.

	Its two date columns are both 100% ISO in the real file, and the META declares each of them
	as a date — two oracles agreeing.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's VLMO index (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "vlmo_cia_aberta"
	_CONTRACT: ClassVar[FileContract] = VLMO_CIA_ABERTA
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia", "Data_Entrega")
	_LABEL: ClassVar[str] = "índice"
