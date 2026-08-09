"""Data contracts for the CVM open-data *Extrato das Informações sobre o Fundo* (ingestion).

The dataset ``FI/DOC/EXTRATO`` publishes **two different artifacts**, not one series — a fact the
directory listing gives away and the filenames do not:

=========================  ==================================  ==========================
artifact                   shape                               grain
=========================  ==================================  ==========================
``extrato_fi_AAAA.csv``    plain CSV, **by year**               **every** filing that year
``extrato_fi.csv``         plain CSV, **fixed URL**             the **latest** filing per fund
=========================  ==================================  ==========================

⚠️ **``extrato_fi.csv`` is a SNAPSHOT, not the accumulated series** — the reading its unpartitioned
name invites. Measured: 38.454 rows over **38.454 distinct** ``CNPJ_FUNDO_CLASSE`` (exactly one row
per fund), with ``DT_COMPTC`` spanning 2015–2026 because each fund carries the date of *its own*
last extrato. Every one of its rows also exists in the matching yearly file (0 rows present only in
the snapshot), while the yearly files carry far more (2025: 13.590 rows against 8.455 dated 2025 in
the snapshot). "Latest" was **verified**, not assumed: across the 2.469 funds with more than one
filing in 2025, the snapshot date equals that year's maximum or is later — **zero** exceptions.

⚠️ **This is the first artifact in the library with a genuine unique key.** Every other reader
asserts "no grain is asserted"; here one row per ``CNPJ_FUNDO_CLASSE`` is a measured trait of the
snapshot (it does **not** hold for the yearly files, where a fund may file repeatedly).

⚠️ **The yearly series carries two schemas, and the cutover is NOT RCVM 175.** Measured over the
published headers:

===================  ==========  ======  =========================================
regime               years       cols    leading key block
===================  ==========  ======  =========================================
pre-2020             2015–2019      116  ``CNPJ_FUNDO``
2020 onward          2020–2026      117  ``TP_FUNDO_CLASSE`` + ``CNPJ_FUNDO_CLASSE``
===================  ==========  ======  =========================================

It is the *same column change* the Perfil Mensal underwent — but that one's cutover is ``202312``
and this one's is **2020**, while Resolução CVM 175 dates from **December 2022**. So the regulation
cannot be the cause here: CVM reached the same columns twice, years apart, by different routes.
The contracts below are therefore named for the **measured year**, never for a regulation, and each
is generated from and pinned to its own published header in ``tests/fixtures/extrato_fi/``.

⚠️ The other **115 columns are identical** between the two regimes (measured, position for
position), so deriving one contract from the other is right about 115 of 116 names — the same copy
trap the Perfil Mensal carries, and the reason both tuples are pinned rather than derived.

⚠️ **Only ``DT_COMPTC`` is a date** (1 of 117; the META declares exactly one ``date`` field).
``PRAZO`` is ``varchar`` and holds values like ``01/03/2033`` — a ``DD/MM/YYYY`` string that is
**not** a date column, and coercing it would misparse day/month. Everything that is not
``DT_COMPTC`` stays exact source text: the META declares **74 ``numeric`` + 4 ``decimal`` + 4
``int``** fields, some carrying **12 decimal places** (``TAXA_PERFM`` arrives as
``0.010000000000``), where a float would silently destroy the published scale.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# The 115 columns shared by both yearly regimes **and** the snapshot, in published file order —
# everything from ``DENOM_SOCIAL`` onward. Declared once because the headers were **measured**
# identical here; the regimes differ only in the key block that precedes it.
_TUPLE_SHARED_TAIL: tuple[str, ...] = (
	"DENOM_SOCIAL",
	"DT_COMPTC",
	"CONDOM",
	"NEGOC_MERC",
	"MERCADO",
	"TP_PRAZO",
	"PRAZO",
	"PUBLICO_ALVO",
	"REG_ANBIMA",
	"CLASSE_ANBIMA",
	"DISTRIB",
	"POLIT_INVEST",
	"APLIC_MAX_FUNDO_LIGADO",
	"RESULT_CART_INCORP_PL",
	"FUNDO_COTAS",
	"FUNDO_ESPELHO",
	"APLIC_MIN",
	"ATUALIZ_DIARIA_COTA",
	"PRAZO_ATUALIZ_COTA",
	"COTA_EMISSAO",
	"COTA_PL",
	"QT_DIA_CONVERSAO_COTA",
	"QT_DIA_PAGTO_COTA",
	"QT_DIA_RESGATE_COTAS",
	"QT_DIA_PAGTO_RESGATE",
	"TP_DIA_PAGTO_RESGATE",
	"TAXA_SAIDA_PAGTO_RESGATE",
	"TAXA_ADM",
	"TAXA_CUSTODIA_MAX",
	"EXISTE_TAXA_PERFM",
	"TAXA_PERFM",
	"PARAM_TAXA_PERFM",
	"PR_INDICE_REFER_TAXA_PERFM",
	"VL_CUPOM",
	"CALC_TAXA_PERFM",
	"INF_TAXA_PERFM",
	"EXISTE_TAXA_INGRESSO",
	"TAXA_INGRESSO_REAL",
	"TAXA_INGRESSO_PR",
	"EXISTE_TAXA_SAIDA",
	"TAXA_SAIDA_REAL",
	"TAXA_SAIDA_PR",
	"OPER_DERIV",
	"FINALIDADE_OPER_DERIV",
	"OPER_VL_SUPERIOR_PL",
	"FATOR_OPER_VL_SUPERIOR_PL",
	"CONTRAP_LIGADO",
	"INVEST_EXTERIOR",
	"APLIC_MAX_ATIVO_EXTERIOR",
	"ATIVO_CRED_PRIV",
	"APLIC_MAX_ATIVO_CRED_PRIV",
	"PR_INSTITUICAO_FINANC_MIN",
	"PR_INSTITUICAO_FINANC_MAX",
	"PR_CIA_MIN",
	"PR_CIA_MAX",
	"PR_FI_MIN",
	"PR_FI_MAX",
	"PR_UNIAO_MIN",
	"PR_UNIAO_MAX",
	"PR_ADMIN_GESTOR_MIN",
	"PR_ADMIN_GESTOR_MAX",
	"PR_EMISSOR_OUTRO_MIN",
	"PR_EMISSOR_OUTRO_MAX",
	"PR_COTA_FI_MIN",
	"PR_COTA_FI_MAX",
	"PR_COTA_FIC_MIN",
	"PR_COTA_FIC_MAX",
	"PR_COTA_FI_QUALIF_MIN",
	"PR_COTA_FI_QUALIF_MAX",
	"PR_COTA_FIC_QUALIF_MIN",
	"PR_COTA_FIC_QUALIF_MAX",
	"PR_COTA_FI_PROF_MIN",
	"PR_COTA_FI_PROF_MAX",
	"PR_COTA_FIC_PROF_MIN",
	"PR_COTA_FIC_PROF_MAX",
	"PR_COTA_FII_MIN",
	"PR_COTA_FII_MAX",
	"PR_COTA_FIDC_MIN",
	"PR_COTA_FIDC_MAX",
	"PR_COTA_FICFIDC_MIN",
	"PR_COTA_FICFIDC_MAX",
	"PR_COTA_FIDC_NP_MIN",
	"PR_COTA_FIDC_NP_MAX",
	"PR_COTA_FICFIDC_NP_MIN",
	"PR_COTA_FICFIDC_NP_MAX",
	"PR_COTA_ETF_MIN",
	"PR_COTA_ETF_MAX",
	"PR_CRI_MIN",
	"PR_CRI_MAX",
	"PR_TITPUB_MIN",
	"PR_TITPUB_MAX",
	"PR_OURO_MIN",
	"PR_OURO_MAX",
	"PR_TIT_INSTITUICAO_FINANC_BACEN_MIN",
	"PR_TIT_INSTITUICAO_FINANC_BACEN_MAX",
	"PR_VLMOB_MIN",
	"PR_VLMOB_MAX",
	"PR_ACAO_MIN",
	"PR_ACAO_MAX",
	"PR_DEBENTURE_MIN",
	"PR_DEBENTURE_MAX",
	"PR_NP_MIN",
	"PR_NP_MAX",
	"PR_COMPROM_MIN",
	"PR_COMPROM_MAX",
	"PR_DERIV_MIN",
	"PR_DERIV_MAX",
	"PR_ATIVO_OUTRO_MIN",
	"PR_ATIVO_OUTRO_MAX",
	"PR_COTA_FMIEE_MIN",
	"PR_COTA_FMIEE_MAX",
	"PR_COTA_FIP_MIN",
	"PR_COTA_FIP_MAX",
	"PR_COTA_FICFIP_MIN",
	"PR_COTA_FICFIP_MAX",
)

# The leading key block of the current regime, shared by the yearly (2020+) and snapshot artifacts.
_TUPLE_KEY_BLOCK: tuple[str, ...] = ("TP_FUNDO_CLASSE", "CNPJ_FUNDO_CLASSE")


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
# Yearly artifact, 2020 onward: every filing delivered in the reference year.
EXTRATO_FI = FileContract(
	"Extrato FI",
	"extrato_fi",
	(*_TUPLE_KEY_BLOCK, *_TUPLE_SHARED_TAIL),
	("CNPJ_FUNDO_CLASSE",),
)

# Yearly artifact, 2015-2019: one identifier column, and no ``TP_FUNDO_CLASSE``.
EXTRATO_FI_PRE2020 = FileContract(
	"Extrato FI (pre-2020)",
	"extrato_fi_pre2020",
	("CNPJ_FUNDO", *_TUPLE_SHARED_TAIL),
	("CNPJ_FUNDO",),
)

# Snapshot at a fixed URL: the latest filing per fund. Same columns as the current yearly file —
# **measured**, not assumed — but a different grain and a different source, so it carries its own
# contract and its own ``source_key`` rather than reusing the yearly one.
EXTRATO_FI_SNAPSHOT = FileContract(
	"Extrato FI (snapshot)",
	"extrato_fi_snapshot",
	(*_TUPLE_KEY_BLOCK, *_TUPLE_SHARED_TAIL),
	("CNPJ_FUNDO_CLASSE",),
)
