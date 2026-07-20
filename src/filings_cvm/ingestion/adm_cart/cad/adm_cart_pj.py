"""CVM ADM_CART/CAD — legal-person (pessoa jurídica) portfolio-manager registry reader.

The ``cad_adm_cart_pj.csv`` member of ``cad_adm_cart.zip``: the registry of portfolio-manager firms
(masked CNPJ, corporate and commercial names, dates/reason/situation, registration category and
sub-category, shareholding control, address, phone, net worth, e-mail, website). See
``_base_adm_cart_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_ADM_CART_PJ, FileContract
from filings_cvm.ingestion.adm_cart.cad._base_adm_cart_reader import _BaseAdmCartReader


class AdmCartPjReader(_BaseAdmCartReader):
	"""Read the ADM_CART/CAD *pessoa jurídica* registry into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_adm_cart_pj.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_ADM_CART_PJ
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"DT_REG",
		"DT_CANCEL",
		"DT_INI_SIT",
		"DT_PATRIM_LIQ",
	)
	_LABEL: ClassVar[str] = "pessoa jurídica"
