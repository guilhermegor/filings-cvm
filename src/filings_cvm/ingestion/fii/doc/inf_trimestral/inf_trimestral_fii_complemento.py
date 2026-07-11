"""CVM Informe Trimestral FII — membro *complemento* reader.

The ``inf_trimestral_fii_complemento`` member of ``inf_trimestral_fii_AAAA.zip``: the maturity and
indexer breakdown of the portfolio, the insurance policies, and the liquidity assets. See
``_base_inf_trimestral_fii_reader`` for the shared behaviour — in particular that the dump is
partitioned by **year**, so ``date_ref`` selects the year, not the quarter.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_TRIMESTRAL_FII_COMPLEMENTO, FileContract
from filings_cvm.ingestion.fii.doc.inf_trimestral._base_inf_trimestral_fii_reader import (
	_BaseInfTrimestralFiiReader,
)


class InfTrimestralFiiComplementoReader(_BaseInfTrimestralFiiReader):
	"""Read the Informe Trimestral FII *complemento* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_trimestral_fii_complemento"
	_CONTRACT: ClassVar[FileContract] = INF_TRIMESTRAL_FII_COMPLEMENTO
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "complemento"
