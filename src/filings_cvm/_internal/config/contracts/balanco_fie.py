"""Data contract for the CVM open-data *Balanço FIE* CSV (ingestion).

``balanco_fie_AAAA.zip`` (dataset ``FIE/DOC/BALANCO``) ships a single CSV member — the yearly
accounting balance sheet of the *Fundos de Investimento Especialmente constituídos* (FIE): one row
per fund × competency date × account, carrying the account balance. Verified against the real
archive (``2020``): the 6 columns below are exactly as published, in order.

**Discontinued:** the series runs 2005–2020 only, and uses the **pre-RCVM 175** naming
(``TP_FUNDO`` / ``CNPJ_FUNDO``). Its live monthly sibling :data:`BALANCETE_FIE` uses the post-175
``TP_FUNDO_CLASSE`` / ``CNPJ_FUNDO_CLASSE`` instead. ``VL_SALDO_BALANCO`` (the account balance) and
the account code stay exact source text — never float.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
BALANCO_FIE = FileContract(
	"Balanço FIE",
	"balanco_fie",
	(
		"TP_FUNDO",
		"CNPJ_FUNDO",
		"DT_COMPTC",
		"PLANO_CONTA_BALANCO",
		"CD_CONTA_BALANCO",
		"VL_SALDO_BALANCO",
	),
	("CNPJ_FUNDO",),
)
