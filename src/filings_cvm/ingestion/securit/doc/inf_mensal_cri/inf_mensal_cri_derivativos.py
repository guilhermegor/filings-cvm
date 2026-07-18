"""CVM Informe Mensal CRI — derivativos reader.

The ``inf_mensal_cri_derivativos`` member of ``inf_mensal_cri_AAAA.zip``: derivatives exposure by
market (termo, futuros, opções, swap) and underlying. **20 columns.**

See ``_base_inf_mensal_cri_reader`` for the shared behaviour (yearly ``date_ref``, shared archive,
``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_CRI_DERIVATIVOS, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_cri._base_inf_mensal_cri_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalCriReader,
)


class InfMensalCriDerivativosReader(_BaseInfMensalCriReader):
	"""Read the Informe Mensal CRI derivativos into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_cri_derivativos"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_CRI_DERIVATIVOS
	_LABEL: ClassVar[str] = "derivativos"
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
