"""CVM Informe Anual FII — membro *processo* reader.

The ``inf_anual_fii_processo`` member of ``inf_anual_fii_AAAA.zip``: the fund's lawsuits — one row
per processo (juízo, instância, data de instauração, valor da causa, partes, chance de perda e
análise de impacto). A **long** table. See ``_base_inf_anual_fii_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_ANUAL_FII_PROCESSO, FileContract
from filings_cvm.ingestion.fii.doc.inf_anual._base_inf_anual_fii_reader import (
	_BaseInfAnualFiiReader,
)


class InfAnualFiiProcessoReader(_BaseInfAnualFiiReader):
	"""Read the Informe Anual FII *processo* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_anual_fii_processo"
	_CONTRACT: ClassVar[FileContract] = INF_ANUAL_FII_PROCESSO
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia", "Data_Instauracao")
	_LABEL: ClassVar[str] = "processo"
