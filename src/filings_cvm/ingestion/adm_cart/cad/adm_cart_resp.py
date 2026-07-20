"""CVM ADM_CART/CAD — responsible-officer table reader.

The ``cad_adm_cart_resp.csv`` member of ``cad_adm_cart.zip``: one row per responsible officer of a
portfolio-manager firm (the firm's ``CNPJ``, the officer's name and their role). ⚠️ Carries personal
data (``RESP``) but **no CPF column**, and **no date column at all** — so ``_DATE_COLS`` is empty
and every column is exact source text. See ``_base_adm_cart_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_ADM_CART_RESP, FileContract
from filings_cvm.ingestion.adm_cart.cad._base_adm_cart_reader import _BaseAdmCartReader


class AdmCartRespReader(_BaseAdmCartReader):
	"""Read the ADM_CART/CAD responsible-officer table into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_adm_cart_resp.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_ADM_CART_RESP
	_DATE_COLS: ClassVar[tuple[str, ...]] = ()
	_LABEL: ClassVar[str] = "responsável"
