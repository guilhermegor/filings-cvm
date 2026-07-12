"""CVM Informe Mensal FIAGRO — subclasse reader.

The ``inf_mensal_fiagro_subclasse`` member of ``inf_mensal_fiagro_AAAAMM.zip``: the per-subclasse
breakdown of each fund class (6 columns — ``CNPJ_Classe``, ``Nome_Classe``, ``Data_Referencia``,
``Nome_Subclasse``, ``Numero_Cotas``, ``Valor_Patrimonial_Cota``). Naturally **long**: one row per
subclasse of a class. See ``_base_inf_mensal_fiagro_reader`` for the shared behaviour (monthly
``date_ref``, shared archive, ``path_raw``). Its only date column is ``Data_Referencia``.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_FIAGRO_SUBCLASSE, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.fiagro.doc.inf_mensal._base_inf_mensal_fiagro_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalFiagroReader,
)


class InfMensalFiagroSubclasseReader(_BaseInfMensalFiagroReader):
	"""Read the Informe Mensal FIAGRO subclasse breakdown into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_fiagro_subclasse"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_FIAGRO_SUBCLASSE
	_LABEL: ClassVar[str] = "subclasse"
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
