"""CVM Informe Mensal FIAGRO — informe proper reader.

The ``inf_mensal_fiagro`` member of ``inf_mensal_fiagro_AAAAMM.zip``: the FIAGRO monthly report
(133 columns) — cadastro da classe, cotistas por tipo, patrimônio, composição da carteira
(agronegócio, securitização, direitos creditórios), prazos a vencer/vencidos e passivo. One row
per fund class per reference month. See ``_base_inf_mensal_fiagro_reader`` for the shared
behaviour (monthly ``date_ref``, shared archive, ``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_FIAGRO, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.fiagro.doc.inf_mensal._base_inf_mensal_fiagro_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalFiagroReader,
)


class InfMensalFiagroReader(_BaseInfMensalFiagroReader):
	"""Read the Informe Mensal FIAGRO (informe proper) into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_fiagro"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_FIAGRO
	_LABEL: ClassVar[str] = "informe"
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia", "Data_Entrega", "Data_Registro")
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
