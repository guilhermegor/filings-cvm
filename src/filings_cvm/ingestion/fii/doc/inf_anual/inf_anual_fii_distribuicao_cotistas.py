"""CVM Informe Anual FII — membro *distribuição de cotistas* reader.

The ``inf_anual_fii_distribuicao_cotistas`` member of ``inf_anual_fii_AAAA.zip``: the shareholder
base bucketed by the share of the fund each holds (up to 5%, 5–10%, …, above 50%), with the split
between pessoa física and jurídica. See ``_base_inf_anual_fii_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import (
	INF_ANUAL_FII_DISTRIBUICAO_COTISTAS,
	FileContract,
)
from filings_cvm.ingestion.fii.doc.inf_anual._base_inf_anual_fii_reader import (
	_BaseInfAnualFiiReader,
)


class InfAnualFiiDistribuicaoCotistasReader(_BaseInfAnualFiiReader):
	"""Read the Informe Anual FII *distribuição de cotistas* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_anual_fii_distribuicao_cotistas"
	_CONTRACT: ClassVar[FileContract] = INF_ANUAL_FII_DISTRIBUICAO_COTISTAS
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "distribuição de cotistas"
