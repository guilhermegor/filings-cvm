"""CVM Informe Trimestral FII — membro *rentabilidade efetiva* reader.

The ``inf_trimestral_fii_rentabilidade_efetiva`` member of ``inf_trimestral_fii_AAAA.zip``: the
fund's effective monthly return within the quarter — one row per reference month. See
``_base_inf_trimestral_fii_reader`` for the shared behaviour — in particular that the dump is
partitioned by **year**, so ``date_ref`` selects the year, not the quarter.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import (
	INF_TRIMESTRAL_FII_RENTABILIDADE_EFETIVA,
	FileContract,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral._base_inf_trimestral_fii_reader import (
	_BaseInfTrimestralFiiReader,
)


class InfTrimestralFiiRentabilidadeEfetivaReader(_BaseInfTrimestralFiiReader):
	"""Read the Informe Trimestral FII *rentabilidade efetiva* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_trimestral_fii_rentabilidade_efetiva"
	_CONTRACT: ClassVar[FileContract] = INF_TRIMESTRAL_FII_RENTABILIDADE_EFETIVA
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "rentabilidade efetiva"
