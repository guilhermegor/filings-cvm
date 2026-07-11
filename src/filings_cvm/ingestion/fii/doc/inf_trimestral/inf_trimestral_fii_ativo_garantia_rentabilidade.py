"""CVM Informe Trimestral FII — membro *ativo com garantia de rentabilidade* reader.

The ``inf_trimestral_fii_ativo_garantia_rentabilidade`` member of ``inf_trimestral_fii_AAAA.zip``:
assets carrying a rentabilidade guarantee — the guarantor and the guarantee's characteristics. See
``_base_inf_trimestral_fii_reader`` for the shared behaviour — in particular that the dump is
partitioned by **year**, so ``date_ref`` selects the year, not the quarter.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import (
	INF_TRIMESTRAL_FII_ATIVO_GARANTIA_RENTABILIDADE,
	FileContract,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral._base_inf_trimestral_fii_reader import (
	_BaseInfTrimestralFiiReader,
)


class InfTrimestralFiiAtivoGarantiaRentabilidadeReader(_BaseInfTrimestralFiiReader):
	"""Read the Informe Trimestral FII *ativo com garantia de rentabilidade* member."""

	_MEMBER_STEM: ClassVar[str] = "inf_trimestral_fii_ativo_garantia_rentabilidade"
	_CONTRACT: ClassVar[FileContract] = INF_TRIMESTRAL_FII_ATIVO_GARANTIA_RENTABILIDADE
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "ativo com garantia de rentabilidade"
