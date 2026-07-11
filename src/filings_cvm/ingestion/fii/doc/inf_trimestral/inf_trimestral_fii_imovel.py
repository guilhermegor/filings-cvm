"""CVM Informe Trimestral FII — membro *imóvel* reader.

The ``inf_trimestral_fii_imovel`` member of ``inf_trimestral_fii_AAAA.zip``: the fund's properties
— one row per imóvel, with area, occupancy, vacancy/inadimplência/locação percentages and
construction progress. A **long** table. See ``_base_inf_trimestral_fii_reader`` for the shared
behaviour — in particular that the dump is partitioned by **year**, so ``date_ref`` selects the
year, not the quarter.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_TRIMESTRAL_FII_IMOVEL, FileContract
from filings_cvm.ingestion.fii.doc.inf_trimestral._base_inf_trimestral_fii_reader import (
	_BaseInfTrimestralFiiReader,
)


class InfTrimestralFiiImovelReader(_BaseInfTrimestralFiiReader):
	"""Read the Informe Trimestral FII *imóvel* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_trimestral_fii_imovel"
	_CONTRACT: ClassVar[FileContract] = INF_TRIMESTRAL_FII_IMOVEL
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "imóvel"
