"""CVM ADM_CART/CAD — partner table reader.

The ``cad_adm_cart_socios.csv`` member of ``cad_adm_cart.zip``: one row per partner of a
portfolio-manager firm (the firm's ``CNPJ`` and the partner's name). ⚠️ ``SOCIOS`` mixes natural and
legal persons and is personal data, but there is **no CPF column**, and **no date column at all** —
so ``_DATE_COLS`` is empty and every column is exact source text. See ``_base_adm_cart_reader`` for
the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_ADM_CART_SOCIOS, FileContract
from filings_cvm.ingestion.adm_cart.cad._base_adm_cart_reader import _BaseAdmCartReader


class AdmCartSociosReader(_BaseAdmCartReader):
	"""Read the ADM_CART/CAD partner table into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_adm_cart_socios.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_ADM_CART_SOCIOS
	_DATE_COLS: ClassVar[tuple[str, ...]] = ()
	_LABEL: ClassVar[str] = "sócio"
