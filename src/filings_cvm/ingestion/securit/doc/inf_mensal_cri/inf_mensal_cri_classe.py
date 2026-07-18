"""CVM Informe Mensal CRI — classe reader.

The ``inf_mensal_cri_classe`` member of ``inf_mensal_cri_AAAA.zip``: one row per **class/series**
of the certificate — remuneration, subordination, amortisation and
maturity. **28 columns.** Naturally **long** (many rows per certificate).

⚠️ **``Indice_Subordinacao_Data_Base`` is NOT a date** despite its name — real values
are numeric (``0.00``). It is deliberately absent from ``_DATE_COLS`` and stays ``str``; the
only dates here are ``Data_Referencia`` and ``Data_Vencimento``.

See ``_base_inf_mensal_cri_reader`` for the shared behaviour (yearly ``date_ref``, shared archive,
``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_CRI_CLASSE, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_cri._base_inf_mensal_cri_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalCriReader,
)


class InfMensalCriClasseReader(_BaseInfMensalCriReader):
	"""Read the Informe Mensal CRI classe into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_cri_classe"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_CRI_CLASSE
	_LABEL: ClassVar[str] = "classe"
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Vencimento",
	)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
