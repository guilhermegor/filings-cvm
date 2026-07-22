"""CVM CROWDFUNDING/CAD — crowdfunding-platform registry reader.

The ``cad_crowdfunding.csv`` member of ``cad_crowdfunding.zip``: the registry of the electronic
investment-crowdfunding platforms registered with the CVM (CNPJ, corporate and commercial names,
registration date, situation, website, e-mail, address and phone).

⚠️ Leaner than its COORD_OFERTA / INTERMED siblings — **no** ``DT_CANCEL`` / ``MOTIVO_CANCEL`` /
``CD_CVM``, and it spells the site column ``WEBSITE`` (not ``SITE_WEB``) and the area code ``DDD``
(not ``DDD_TEL``). See ``_base_crowdfunding_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_CROWDFUNDING, FileContract
from filings_cvm.ingestion.crowdfunding.cad._base_crowdfunding_reader import (
	_BaseCrowdfundingReader,
)


class CrowdfundingReader(_BaseCrowdfundingReader):
	"""Read the CROWDFUNDING/CAD platform registry into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_crowdfunding.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_CROWDFUNDING
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REG", "DT_INI_SIT")
	_LABEL: ClassVar[str] = "plataforma de crowdfunding"
