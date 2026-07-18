"""CVM Informe Mensal CRI — ativo/passivo reader.

The ``inf_mensal_cri_ativo_passivo`` member of ``inf_mensal_cri_AAAA.zip``: the balance sheet
(assets, liabilities, derivatives) plus the payment waterfall. **65 columns.**

See ``_base_inf_mensal_cri_reader`` for the shared behaviour (yearly ``date_ref``, shared archive,
``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_CRI_ATIVO_PASSIVO, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_cri._base_inf_mensal_cri_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalCriReader,
)


class InfMensalCriAtivoPassivoReader(_BaseInfMensalCriReader):
	"""Read the Informe Mensal CRI ativo/passivo into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_cri_ativo_passivo"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_CRI_ATIVO_PASSIVO
	_LABEL: ClassVar[str] = "ativo/passivo"
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
