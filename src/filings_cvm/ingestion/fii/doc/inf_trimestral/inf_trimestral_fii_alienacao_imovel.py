"""CVM Informe Trimestral FII — membro *alienação de imóvel* reader.

The ``inf_trimestral_fii_alienacao_imovel`` member of ``inf_trimestral_fii_AAAA.zip``: properties
sold in the quarter — one row per alienação, with the sale date. See
``_base_inf_trimestral_fii_reader`` for the shared behaviour — in particular that the dump is
partitioned by **year**, so ``date_ref`` selects the year, not the quarter.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import (
	INF_TRIMESTRAL_FII_ALIENACAO_IMOVEL,
	FileContract,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral._base_inf_trimestral_fii_reader import (
	_BaseInfTrimestralFiiReader,
)


class InfTrimestralFiiAlienacaoImovelReader(_BaseInfTrimestralFiiReader):
	"""Read the Informe Trimestral FII *alienação de imóvel* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_trimestral_fii_alienacao_imovel"
	_CONTRACT: ClassVar[FileContract] = INF_TRIMESTRAL_FII_ALIENACAO_IMOVEL
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia", "Data_Alienacao")
	_LABEL: ClassVar[str] = "alienação de imóvel"
