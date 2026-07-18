"""CVM Informe Mensal CRI — modificação de carteira reader.

The ``inf_mensal_cri_carteira_modificacao`` member of ``inf_mensal_cri_AAAA.zip``:
portfolio-modification events (event, value, justification). **7 columns.** A **CRI-only**
member; naturally sparse (rows only when a modification occurred).

See ``_base_inf_mensal_cri_reader`` for the shared behaviour (yearly ``date_ref``, shared archive,
``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import (
	INF_MENSAL_CRI_CARTEIRA_MODIFICACAO,
	FileContract,
)
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_cri._base_inf_mensal_cri_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalCriReader,
)


class InfMensalCriCarteiraModificacaoReader(_BaseInfMensalCriReader):
	"""Read the Informe Mensal CRI modificação de carteira into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_cri_carteira_modificacao"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_CRI_CARTEIRA_MODIFICACAO
	_LABEL: ClassVar[str] = "modificação de carteira"
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
