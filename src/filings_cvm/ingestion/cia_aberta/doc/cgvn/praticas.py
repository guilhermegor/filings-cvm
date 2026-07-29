"""CVM CGVN CIA_ABERTA (práticas) — ingestion (leitura) reader.

The **content** member: one row per recommended governance practice per informe — the chapter and
principle it belongs to, whether the company adopted it (``Pratica_Adotada``, ``Sim``/``Não``), and
the free-text ``Explicacao`` when it did not. Far larger than the index (19,980 rows against 382 in
2025).

Two shape notes, both measured against the real bytes:

- ⚠️ ``ID_Item`` is a **hierarchical identifier** (``1.1.1``), so it stays exact text — a numeric
  cast is meaningless for it.
- The free text is long: ``Explicacao`` reaches ~6,000 characters (11,935 of 19,980 rows filled)
  and ``Pratica_Recomendada`` ~1,300. The ``;``-separated ``QUOTE_NONE`` read parses every row to a
  uniform width, so no field embeds the delimiter.

Only ``Data_Referencia`` is a date here — the fiscal-year and delivery dates live on the index.

Download/unzip/parse is inherited from the private `_BaseCgvnReader`.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.cgvn_cia_aberta import CGVN_CIA_ABERTA_PRATICAS
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.cgvn._base_cgvn_reader import _BaseCgvnReader


class CgvnCiaAbertaPraticasReader(_BaseCgvnReader):
	"""Read the CGVN CIA_ABERTA governance-practices member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's practices (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "cgvn_cia_aberta_praticas"
	_CONTRACT: ClassVar[FileContract] = CGVN_CIA_ABERTA_PRATICAS
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "práticas"
