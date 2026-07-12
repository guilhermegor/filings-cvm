"""Data contract for the CVM open-data *Medidas Mensais FIE* CSV (ingestion).

``medidas_mes_fie_AAAAMM.csv`` (dataset ``FIE/MEDIDAS``) is a **plain CSV, not a ZIP** — the
monthly headline measures of the *Fundos de Investimento Especialmente constituídos* (FIE): one row
per fund × competency month, carrying net worth and the shareholder count. Verified against the
real file (``202606``): the 6 columns below are exactly as published, **in file order** — which
differs from the META's alphabetical listing (``VL_PATRIM_LIQ`` precedes ``NR_COTST``).

Uses the pre-RCVM 175 ``TP_FUNDO`` / ``CNPJ_FUNDO`` naming. ``VL_PATRIM_LIQ`` (net worth) and
``NR_COTST`` (shareholder count) stay exact source text — never float/int.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
MEDIDAS_MES_FIE = FileContract(
	"Medidas Mensais FIE",
	"medidas_mes_fie",
	(
		"TP_FUNDO",
		"CNPJ_FUNDO",
		"DENOM_SOCIAL",
		"DT_COMPTC",
		"VL_PATRIM_LIQ",
		"NR_COTST",
	),
	("CNPJ_FUNDO",),
)
