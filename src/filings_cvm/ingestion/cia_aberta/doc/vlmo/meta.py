"""CVM **META** for the Companhias Abertas VLMO dataset (`CIA_ABERTA/DOC/VLMO`).

The spec CVM publishes for `vlmo_cia_aberta_AAAA.csv` and its `con` sibling — the declared
description, type and size of each field (12 and 17 respectively). It confirms both readers'
date columns (`date`) and that `Preco_Unitario`/`Volume` are `decimal` and `Quantidade` `bigint`.

⚠️ The URL is **constant per dataset and never derived**. Here the META is a **`.zip` of two
members** and `meta_vlmo_cia_aberta.txt` returns **404** — the exact inverse of the sibling IPE,
whose loose `.txt` is the only form that exists. Across the seven `CIA_ABERTA/DOC` datasets CVM
uses four different spellings.

⚠️ The two members are `meta_vlmo_cia_aberta.txt` and `meta_vlmo_cia_aberta_con.txt`, so the first
one **is the bare stem**. The shared base's `_section_of` therefore falls back to labelling it by
the whole stem, and the sections come back **asymmetric** (`meta_vlmo_cia_aberta` + `con`) — the
same shape as INTERMED and COORD_OFERTA. That is honoured as-is, not special-cased in the base.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_VLMO_CIA_ABERTA
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaVlmoCiaAbertaReader(BaseMetaReader):
	"""Read the META of the CVM Companhias Abertas VLMO dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/VLMO/META/meta_vlmo_cia_aberta.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_VLMO_CIA_ABERTA
