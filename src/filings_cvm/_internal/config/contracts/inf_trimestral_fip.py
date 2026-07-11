"""Data contract for the CVM open-data *Informe Trimestral FIP* CSV (ingestion).

``inf_trimestral_fip_AAAA.csv`` (dataset ``FIP/DOC/INF_TRIMESTRAL``) is the **quarterly** report a
Fundo de Investimento em Participações delivered under the pre-RCVM 175 regime: one row per fund
per competency quarter, carrying the fund's net worth and quota position, the committed /
subscribed / paid-in capital, and the subscriber breakdown by investor category (number of holders
``NR_COTST_SUBSCR_*`` and percentage of subscribed quotas ``PR_COTA_SUBSCR_*``), plus the
per-class quota fields. Verified against the real file (``2023``): the 54 columns below are exactly
as published, in order.

Two things to keep in mind, both reflected in the reader:

- **Partitioned by year** (``inf_trimestral_fip_2023.csv``), and a **plain CSV**, not a ZIP. The
  series runs 2010–2023; from 2024 the report became quadrimestral (:mod:`inf_quadrimestral_fip`).
- The fund is keyed by ``CNPJ_FUNDO`` here — the pre-175 identifier. Its post-175 sibling
  (:data:`INF_QUADRIMESTRAL_FIP`) keys on ``CNPJ_FUNDO_CLASSE`` instead.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
INF_TRIMESTRAL_FIP = FileContract(
	"Informe Trimestral FIP",
	"inf_trimestral_fip",
	(
		"CNPJ_FUNDO",
		"DENOM_SOCIAL",
		"DT_COMPTC",
		"VL_PATRIM_LIQ",
		"QT_COTA",
		"VL_PATRIM_COTA",
		"NR_COTST",
		"ENTID_INVEST",
		"PUBLICO_ALVO",
		"VL_CAP_COMPROM",
		"QT_COTA_SUBSCR",
		"VL_CAP_SUBSCR",
		"QT_COTA_INTEGR",
		"VL_CAP_INTEGR",
		"VL_INVEST_FIP_COTA",
		"NR_COTST_SUBSCR_PF",
		"PR_COTA_SUBSCR_PF",
		"NR_COTST_SUBSCR_PJ_NAO_FINANC",
		"PR_COTA_SUBSCR_PJ_NAO_FINANC",
		"NR_COTST_SUBSCR_BANCO",
		"PR_COTA_SUBSCR_BANCO",
		"NR_COTST_SUBSCR_CORRETORA_DISTRIB",
		"PR_COTA_SUBSCR_CORRETORA_DISTRIB",
		"NR_COTST_SUBSCR_PJ_FINANC",
		"PR_COTA_SUBSCR_PJ_FINANC",
		"NR_COTST_SUBSCR_INVNR",
		"PR_COTA_SUBSCR_INVNR",
		"NR_COTST_SUBSCR_EAPC",
		"PR_COTA_SUBSCR_EAPC",
		"NR_COTST_SUBSCR_EFPC",
		"PR_COTA_SUBSCR_EFPC",
		"NR_COTST_SUBSCR_RPPS",
		"PR_COTA_SUBSCR_RPPS",
		"NR_COTST_SUBSCR_SEGUR",
		"PR_COTA_SUBSCR_SEGUR",
		"NR_COTST_SUBSCR_CAPITALIZ",
		"PR_COTA_SUBSCR_CAPITALIZ",
		"NR_COTST_SUBSCR_FII",
		"PR_COTA_SUBSCR_FII",
		"NR_COTST_SUBSCR_FI",
		"PR_COTA_SUBSCR_FI",
		"NR_COTST_SUBSCR_DISTRIB",
		"PR_COTA_SUBSCR_DISTRIB",
		"NR_COTST_SUBSCR_OUTRO",
		"PR_COTA_SUBSCR_OUTRO",
		"NR_TOTAL_COTST_SUBSCR",
		"PR_TOTAL_COTA_SUBSCR",
		"CLASSE_COTA",
		"NR_COTST_SUBSCR_CLASSE",
		"QT_COTA_SUBSCR_CLASSE",
		"QT_COTA_INTEGR_CLASSE",
		"VL_QUOTA_CLASSE",
		"DIREITO_POLIT_CLASSE",
		"DIREITO_ECON_CLASSE",
	),
	("CNPJ_FUNDO",),
)
