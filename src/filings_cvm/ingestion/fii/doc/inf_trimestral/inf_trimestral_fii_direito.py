"""CVM Informe Trimestral FII — membro *direito* reader.

The ``inf_trimestral_fii_direito`` member of ``inf_trimestral_fii_AAAA.zip``: real-estate rights
held by the fund — one row per right (name, characteristics, value). See
``_base_inf_trimestral_fii_reader`` for the shared behaviour — in particular that the dump is
partitioned by **year**, so ``date_ref`` selects the year, not the quarter.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_TRIMESTRAL_FII_DIREITO, FileContract
from filings_cvm.ingestion.fii.doc.inf_trimestral._base_inf_trimestral_fii_reader import (
	_BaseInfTrimestralFiiReader,
)


class InfTrimestralFiiDireitoReader(_BaseInfTrimestralFiiReader):
	"""Read the Informe Trimestral FII *direito* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_trimestral_fii_direito"
	_CONTRACT: ClassVar[FileContract] = INF_TRIMESTRAL_FII_DIREITO
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "direito"
