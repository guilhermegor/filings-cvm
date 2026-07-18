"""CVM Informe Mensal CRI — cedente/devedor reader.

The ``inf_mensal_cri_cedente_devedor`` member of ``inf_mensal_cri_AAAA.zip``: one row per
**assignor/debtor** of the linked credits (type, identifier, percentage).
**7 columns.** Naturally **long**.

⚠️ Its ``CNPJ`` column is a **dirty free-text identifier** — it may hold a **CPF** when
the cedente/devedor is a natural person — so it is **not** declared a CNPJ column (declaring it
would fail a valid file). Read as exact text; being possibly a CPF, it is personal data.

See ``_base_inf_mensal_cri_reader`` for the shared behaviour (yearly ``date_ref``, shared archive,
``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_CRI_CEDENTE_DEVEDOR, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_cri._base_inf_mensal_cri_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalCriReader,
)


class InfMensalCriCedenteDevedorReader(_BaseInfMensalCriReader):
	"""Read the Informe Mensal CRI cedente/devedor into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_cri_cedente_devedor"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_CRI_CEDENTE_DEVEDOR
	_LABEL: ClassVar[str] = "cedente/devedor"
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
