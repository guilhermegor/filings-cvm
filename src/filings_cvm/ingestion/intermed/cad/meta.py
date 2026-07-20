"""CVM **META** for the INTERMED Cadastro dataset (`INTERMED/CAD`, `cad_intermed.zip`).

The spec CVM publishes for the market-intermediary registry — the declared description, type and
size of each field. A ZIP of two members (`meta_cad_intermed.txt`, `meta_cad_intermed_resp.txt`),
so the parsed frame comes back as one long frame with each member's section in ``section``.

⚠️ This META lists its fields **alphabetically**, not in the published file's column order — the
real header stays the oracle for order (see ``docs/ingestion/meta.md``). It is the oracle for
*type*: it confirms `MOTIVO_CANCEL` is `varchar` (free text, not a date) and that
`CEP`/`TEL`/`FAX`/`CD_CVM` are `numeric`/`char` (kept `str` because they are identifiers).

⚠️ **The two ``section`` labels are asymmetric — ``cad_intermed`` and ``resp``, not a tidy pair.**
One member (`meta_cad_intermed.txt`) is named with the bare `_MEMBER_STEM` and carries no
`<stem>_` suffix to strip, so ``_section_of`` falls back to labelling it by the whole stem; its
sibling (`meta_cad_intermed_resp.txt`) reduces to ``resp``. That fallback is the base's documented
behaviour, and both labels stay distinct and unambiguous — so this is honoured, not "fixed" by
special-casing the shared base.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_CAD_INTERMED
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaIntermedReader(BaseMetaReader):
	"""Read the META of the CVM INTERMED Cadastro dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/INTERMED/CAD/META/meta_cad_intermed.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_CAD_INTERMED
	_MEMBER_STEM: ClassVar[str] = "cad_intermed"
