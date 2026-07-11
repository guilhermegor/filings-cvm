"""CVM Informe Anual FII — membro *transação de ativo* reader.

The ``inf_anual_fii_ativo_transacao`` member of ``inf_anual_fii_AAAA.zip``: asset transactions in
the year — one row per transação (natureza, data, valor envolvido, contraparte, and the assembleia
that approved it). The largest member. See ``_base_inf_anual_fii_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_ANUAL_FII_ATIVO_TRANSACAO, FileContract
from filings_cvm.ingestion.fii.doc.inf_anual._base_inf_anual_fii_reader import (
	_BaseInfAnualFiiReader,
)


class InfAnualFiiAtivoTransacaoReader(_BaseInfAnualFiiReader):
	"""Read the Informe Anual FII *transação de ativo* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_anual_fii_ativo_transacao"
	_CONTRACT: ClassVar[FileContract] = INF_ANUAL_FII_ATIVO_TRANSACAO
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Transacao",
		"Data_Assembleia",
	)
	_LABEL: ClassVar[str] = "transação de ativo"
