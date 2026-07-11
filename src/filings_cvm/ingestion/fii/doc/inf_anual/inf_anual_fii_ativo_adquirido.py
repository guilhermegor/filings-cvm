"""CVM Informe Anual FII — membro *ativo adquirido* reader.

The ``inf_anual_fii_ativo_adquirido`` member of ``inf_anual_fii_AAAA.zip``: assets acquired during
the year — one row per asset (objetivos, montante investido, origem dos recursos). A **long**
table. See ``_base_inf_anual_fii_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_ANUAL_FII_ATIVO_ADQUIRIDO, FileContract
from filings_cvm.ingestion.fii.doc.inf_anual._base_inf_anual_fii_reader import (
	_BaseInfAnualFiiReader,
)


class InfAnualFiiAtivoAdquiridoReader(_BaseInfAnualFiiReader):
	"""Read the Informe Anual FII *ativo adquirido* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_anual_fii_ativo_adquirido"
	_CONTRACT: ClassVar[FileContract] = INF_ANUAL_FII_ATIVO_ADQUIRIDO
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "ativo adquirido"
