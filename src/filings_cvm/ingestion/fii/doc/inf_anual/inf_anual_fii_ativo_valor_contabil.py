"""CVM Informe Anual FII — membro *valor contábil do ativo* reader.

The ``inf_anual_fii_ativo_valor_contabil`` member of ``inf_anual_fii_AAAA.zip``: each asset's book
value, fair value and the resulting valorização/desvalorização. A **long** table. Money columns
keep CVM's exact decimal text. See ``_base_inf_anual_fii_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import (
	INF_ANUAL_FII_ATIVO_VALOR_CONTABIL,
	FileContract,
)
from filings_cvm.ingestion.fii.doc.inf_anual._base_inf_anual_fii_reader import (
	_BaseInfAnualFiiReader,
)


class InfAnualFiiAtivoValorContabilReader(_BaseInfAnualFiiReader):
	"""Read the Informe Anual FII *valor contábil do ativo* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_anual_fii_ativo_valor_contabil"
	_CONTRACT: ClassVar[FileContract] = INF_ANUAL_FII_ATIVO_VALOR_CONTABIL
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "valor contábil do ativo"
