"""Data contract for the CVM open-data *Balancete FIE* CSV (ingestion).

``balancete_fie_AAAAMM.zip`` (dataset ``FIE/DOC/BALANCETE``) ships a single CSV member — the
monthly accounting trial balance of the *Fundos de Investimento Especialmente constituídos* (FIE):
one row per fund/classe × competency month × account, carrying the account balance. Verified
against the real archive (``202606``): the 6 columns below are exactly as published, in order.

Uses the **post-RCVM 175** naming (``TP_FUNDO_CLASSE`` / ``CNPJ_FUNDO_CLASSE``) — the series starts
``202401``. Its sibling :data:`BALANCO_FIE` (the discontinued yearly balance, 2005–2020) keeps the
**pre-175** ``TP_FUNDO`` / ``CNPJ_FUNDO`` instead; the regime split explains the two spellings.
``VL_SALDO_BALCTE`` (the balance) and the account code stay exact source text — never float.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
BALANCETE_FIE = FileContract(
	"Balancete FIE",
	"balancete_fie",
	(
		"TP_FUNDO_CLASSE",
		"CNPJ_FUNDO_CLASSE",
		"DT_COMPTC",
		"PLANO_CONTA_BALCTE",
		"CD_CONTA_BALCTE",
		"VL_SALDO_BALCTE",
	),
	("CNPJ_FUNDO_CLASSE",),
)
