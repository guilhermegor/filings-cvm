"""CVM Informe Trimestral FII — membro *geral* (cadastro e administrador) reader.

The ``inf_trimestral_fii_geral`` member of ``inf_trimestral_fii_AAAA.zip``: the fund's
identification, mandate, trading venues and administrator. See ``_base_inf_trimestral_fii_reader``
for the shared behaviour — in particular that the dump is partitioned by **year**, so ``date_ref``
selects the year, not the quarter.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_TRIMESTRAL_FII_GERAL, FileContract
from filings_cvm.ingestion.fii.doc.inf_trimestral._base_inf_trimestral_fii_reader import (
	_BaseInfTrimestralFiiReader,
)


class InfTrimestralFiiGeralReader(_BaseInfTrimestralFiiReader):
	"""Read the Informe Trimestral FII *geral* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_trimestral_fii_geral"
	_CONTRACT: ClassVar[FileContract] = INF_TRIMESTRAL_FII_GERAL
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Entrega",
		"Data_Funcionamento",
		"Data_Prazo_Duracao",
		"Data_Encerramento_Trimestre",
	)
	_LABEL: ClassVar[str] = "geral"
