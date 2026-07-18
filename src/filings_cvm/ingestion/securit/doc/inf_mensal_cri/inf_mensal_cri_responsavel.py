"""CVM Informe Mensal CRI — responsável reader.

The ``inf_mensal_cri_responsavel`` member of ``inf_mensal_cri_AAAA.zip``: the officer responsible
for the informe (name, role). **6 columns.** A **CRI-only** member;
naturally sparse.

See ``_base_inf_mensal_cri_reader`` for the shared behaviour (yearly ``date_ref``, shared archive,
``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_CRI_RESPONSAVEL, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_cri._base_inf_mensal_cri_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalCriReader,
)


class InfMensalCriResponsavelReader(_BaseInfMensalCriReader):
	"""Read the Informe Mensal CRI responsável into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_cri_responsavel"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_CRI_RESPONSAVEL
	_LABEL: ClassVar[str] = "responsável"
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
