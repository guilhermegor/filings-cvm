"""CVM CROWDFUNDING/CAD — platform partners reader.

The ``cad_crowdfunding_socios.csv`` member of ``cad_crowdfunding.zip``: the partners of each
registered platform, keyed by the **platform's** ``CNPJ`` (not a ``pf``/``pj`` split of the
registry).

⚠️ Two columns and **no date column at all** (``_DATE_COLS = ()``), so every column comes back as
exact source text. ``SOCIO`` mixes natural and legal persons (a partner may be an individual or a
company) and the source publishes **no CPF column**. See ``_base_crowdfunding_reader`` for the
shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_CROWDFUNDING_SOCIOS, FileContract
from filings_cvm.ingestion.crowdfunding.cad._base_crowdfunding_reader import (
	_BaseCrowdfundingReader,
)


class CrowdfundingSociosReader(_BaseCrowdfundingReader):
	"""Read the CROWDFUNDING/CAD partners table into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_crowdfunding_socios.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_CROWDFUNDING_SOCIOS
	_DATE_COLS: ClassVar[tuple[str, ...]] = ()
	_LABEL: ClassVar[str] = "sócio de plataforma"
