"""CVM Informe Trimestral FII — membro *desempenho do imóvel* reader.

The ``inf_trimestral_fii_imovel_desempenho`` member of ``inf_trimestral_fii_AAAA.zip``:
justifications for a property's performance below plan or cost above plan. See
``_base_inf_trimestral_fii_reader`` for the shared behaviour — in particular that the dump is
partitioned by **year**, so ``date_ref`` selects the year, not the quarter.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import (
	INF_TRIMESTRAL_FII_IMOVEL_DESEMPENHO,
	FileContract,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral._base_inf_trimestral_fii_reader import (
	_BaseInfTrimestralFiiReader,
)


class InfTrimestralFiiImovelDesempenhoReader(_BaseInfTrimestralFiiReader):
	"""Read the Informe Trimestral FII *desempenho do imóvel* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_trimestral_fii_imovel_desempenho"
	_CONTRACT: ClassVar[FileContract] = INF_TRIMESTRAL_FII_IMOVEL_DESEMPENHO
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "desempenho do imóvel"
