"""CVM Informe Trimestral FII — membro *aquisição de terreno* reader.

The ``inf_trimestral_fii_aquisicao_terreno`` member of ``inf_trimestral_fii_AAAA.zip``: land plots
acquired in the quarter — one row per acquisition. See ``_base_inf_trimestral_fii_reader`` for the
shared behaviour — in particular that the dump is partitioned by **year**, so ``date_ref`` selects
the year, not the quarter.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import (
	INF_TRIMESTRAL_FII_AQUISICAO_TERRENO,
	FileContract,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral._base_inf_trimestral_fii_reader import (
	_BaseInfTrimestralFiiReader,
)


class InfTrimestralFiiAquisicaoTerrenoReader(_BaseInfTrimestralFiiReader):
	"""Read the Informe Trimestral FII *aquisição de terreno* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_trimestral_fii_aquisicao_terreno"
	_CONTRACT: ClassVar[FileContract] = INF_TRIMESTRAL_FII_AQUISICAO_TERRENO
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "aquisição de terreno"
