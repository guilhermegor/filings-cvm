"""CVM Informe Anual FII — membro *geral* (cadastro e administrador) reader.

The ``inf_anual_fii_geral`` member of ``inf_anual_fii_AAAA.zip``: the fund's identification,
mandate, trading venues and administrator. See ``_base_inf_anual_fii_reader`` for the shared
behaviour (yearly partition, ``path_raw``, retry policy).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_ANUAL_FII_GERAL, FileContract
from filings_cvm.ingestion.fii.doc.inf_anual._base_inf_anual_fii_reader import (
	_BaseInfAnualFiiReader,
)


class InfAnualFiiGeralReader(_BaseInfAnualFiiReader):
	"""Read the Informe Anual FII *geral* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_anual_fii_geral"
	_CONTRACT: ClassVar[FileContract] = INF_ANUAL_FII_GERAL
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Entrega",
		"Data_Funcionamento",
		"Data_Prazo_Duracao",
	)
	_LABEL: ClassVar[str] = "geral"
