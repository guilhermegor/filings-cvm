"""CVM ADM_CART/CAD — natural-person (pessoa física) portfolio-manager registry reader.

The ``cad_adm_cart_pf.csv`` member of ``cad_adm_cart.zip``: the registry of individual portfolio
managers (name, dates/reason/situation, registration category). **Neither CNPJ nor CPF** — the
registry identifies a person manager by ``ADMIN`` alone. See ``_base_adm_cart_reader`` for the
shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_ADM_CART_PF, FileContract
from filings_cvm.ingestion.adm_cart.cad._base_adm_cart_reader import _BaseAdmCartReader


class AdmCartPfReader(_BaseAdmCartReader):
	"""Read the ADM_CART/CAD *pessoa física* registry into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_adm_cart_pf.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_ADM_CART_PF
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REG", "DT_CANCEL", "DT_INI_SIT")
	_LABEL: ClassVar[str] = "pessoa física"
