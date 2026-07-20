"""CVM **META** for the INVNR Cadastro dataset (`INVNR/CAD`, `cad_invnr_repres.zip`).

The spec CVM publishes for the non-resident-investor representative registry — the declared
description, type and size of each field. A ZIP of two members
(`meta_cad_invnr_repres_pf.txt`, `meta_cad_invnr_repres_pj.txt`), so the parsed frame comes back
as one long frame with each member's section in ``section``.

⚠️ This META lists its fields **alphabetically**, not in the published file's column order — the
real header stays the oracle for order (see ``docs/ingestion/meta.md``). It is, however, the oracle
for *type*: it is what confirms ``MOTIVO_CANCEL`` is ``varchar`` (free text, not a date) and
``DT_PATRIM_LIQ`` a genuine ``date``.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_CAD_INVNR_REPRES
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaInvnrRepresReader(BaseMetaReader):
	"""Read the META of the CVM INVNR Cadastro dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/INVNR/CAD/META/meta_cad_invnr_repres.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_CAD_INVNR_REPRES
	_MEMBER_STEM: ClassVar[str] = "cad_invnr_repres"
