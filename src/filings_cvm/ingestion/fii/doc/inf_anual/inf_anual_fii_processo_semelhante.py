"""CVM Informe Anual FII — membro *processo semelhante* reader.

The ``inf_anual_fii_processo_semelhante`` member of ``inf_anual_fii_AAAA.zip``: repetitive lawsuits
grouped by their common cause — one row per group (números, valores, causa da contingência). See
``_base_inf_anual_fii_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_ANUAL_FII_PROCESSO_SEMELHANTE, FileContract
from filings_cvm.ingestion.fii.doc.inf_anual._base_inf_anual_fii_reader import (
	_BaseInfAnualFiiReader,
)


class InfAnualFiiProcessoSemelhanteReader(_BaseInfAnualFiiReader):
	"""Read the Informe Anual FII *processo semelhante* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_anual_fii_processo_semelhante"
	_CONTRACT: ClassVar[FileContract] = INF_ANUAL_FII_PROCESSO_SEMELHANTE
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "processo semelhante"
