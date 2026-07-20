"""CVM **META** for the ADM_CART Cadastro dataset (`ADM_CART/CAD`, `cad_adm_cart.zip`).

The spec CVM publishes for the portfolio-manager registry — the declared description, type and size
of each field. A ZIP of five members (`meta_cad_adm_cart_{pf,pj,diretor,resp,socios}.txt`), so the
parsed frame comes back as one long frame with each member's section in ``section``.

⚠️ This META lists its fields **alphabetically**, not in the published file's column order — the
real header stays the oracle for order (see ``docs/ingestion/meta.md``). It is the oracle for
*type*, and here it corroborates the dataset's most unusual trait: `diretor`, `resp` and `socios`
declare **no `date` field at all**, which is why their readers carry an empty ``_DATE_COLS``. It
also confirms `MOTIVO_CANCEL` is `varchar` (free text, not a date) and that `CEP`/`TEL` are
`numeric` (kept `str` because they are identifiers).

Unlike INTERMED's META, all five members carry the ``<stem>_`` suffix, so the section labels come
back symmetric: ``pf``, ``pj``, ``diretor``, ``resp``, ``socios``.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_CAD_ADM_CART
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaAdmCartReader(BaseMetaReader):
	"""Read the META of the CVM ADM_CART Cadastro dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/ADM_CART/CAD/META/meta_cad_adm_cart.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_CAD_ADM_CART
	_MEMBER_STEM: ClassVar[str] = "cad_adm_cart"
