"""CVM CROWDFUNDING/CAD — responsible-administrator reader.

The ``cad_crowdfunding_adm_resp.csv`` member of ``cad_crowdfunding.zip``: the administrators
answering for each registered platform, keyed by the **platform's** ``CNPJ`` (not a ``pf``/``pj``
split of the registry).

⚠️ Two columns and **no date column at all** (``_DATE_COLS = ()``), so every column comes back as
exact source text. ``ADM_RESP`` holds a person's name but the source publishes **no CPF column**.
See ``_base_crowdfunding_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_CROWDFUNDING_ADM_RESP, FileContract
from filings_cvm.ingestion.crowdfunding.cad._base_crowdfunding_reader import (
	_BaseCrowdfundingReader,
)


class CrowdfundingAdmRespReader(_BaseCrowdfundingReader):
	"""Read the CROWDFUNDING/CAD responsible-administrator table into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_crowdfunding_adm_resp.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_CROWDFUNDING_ADM_RESP
	_DATE_COLS: ClassVar[tuple[str, ...]] = ()
	_LABEL: ClassVar[str] = "administrador responsável por plataforma"
