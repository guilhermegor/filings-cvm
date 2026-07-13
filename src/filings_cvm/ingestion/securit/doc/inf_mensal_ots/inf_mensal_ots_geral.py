"""CVM Informe Mensal OTS — geral (cadastro da operação) reader.

The ``inf_mensal_ots_geral`` member of ``inf_mensal_ots_AAAA.zip``: the operation's registry
section — securitisation company, fiduciary agent, custodian, issue and lastro details, totals,
risk rating and contingencies. See ``_base_inf_mensal_ots_reader`` for the shared behaviour (yearly
``date_ref``, shared archive, ``path_raw``).

This is the member with the **most date columns**: besides the shared ``Data_Referencia`` it
carries ``Data_Entrega``, ``Data_Emissao`` and ``Data_Classificacao_Risco`` (blank on every sampled
row → ``NaT``).

⚠️ CVM typo preserved **verbatim**: ``Outras_Contigencias_Relevantes`` (missing the *n* of
*Contingências*) — while ``Contingencias_Principais_Fatos``, in the same file, is spelled right.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_OTS_GERAL, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_ots._base_inf_mensal_ots_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalOtsReader,
)


class InfMensalOtsGeralReader(_BaseInfMensalOtsReader):
	"""Read the Informe Mensal OTS geral (cadastro da operação) into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_ots_geral"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_OTS_GERAL
	_LABEL: ClassVar[str] = "geral"
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Entrega",
		"Data_Emissao",
		"Data_Classificacao_Risco",
	)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
