"""Data contracts for the CVM open-data *Perfil Mensal FI* CSV (ingestion).

``perfil_mensal_fi_AAAAMM.csv`` (dataset ``FI/DOC/PERFIL_MENSAL``) is a **plain CSV, not a ZIP**,
**partitioned by month**, carrying one row per fund/class per competency month: shareholder counts
by investor category, VaR and stress figures, derivative notionals, and the concentration blocks
for counterparties (*comitentes*) and issuers.

⚠️ **The series carries TWO schemas, and the cutover is inside one filename pattern.** Measured by
binary search over the published headers:

===================  ===================  ======  =========================================
regime               months               cols    leading key block
===================  ===================  ======  =========================================
pre-RCVM 175         ``201901``–``202311``   106  ``CNPJ_FUNDO``
post-RCVM 175        ``202312``–present      107  ``TP_FUNDO_CLASSE`` + ``CNPJ_FUNDO_CLASSE``
===================  ===================  ======  =========================================

⚠️⚠️ **The other 105 columns are identical** — measured, ``pre[2:] == post[3:]``. The *only*
difference is that leading key block, where RCVM 175's fund/class split replaced one identifier
column with two. That makes this the tightest copy trap in the sweep so far: deriving one contract
from the other by "just fixing the first column" is right about 105 of 106 names and would pass
every test except the pinned-header one. **Both tuples below are generated from the real published
headers and pinned** to ``tests/fixtures/perfil_mensal_fi/*_header.csv``, and a test asserts they
differ *exactly* in that block.

⚠️ **The META describes only the post-175 regime.** ``meta_perfil_mensal_fi.txt`` lists 107 fields
equal to the post-175 header exactly (zero on either side, measured) and has no ``CNPJ_FUNDO``, so
it is **not** an oracle for the pre-175 contract — that one's oracle is its own pinned header.

⚠️ **Only ``CNPJ_FUNDO_CLASSE`` / ``CNPJ_FUNDO`` is a CNPJ column.** The six ``CPF_CNPJ_*`` columns
(``COMITENTE_1..3``, ``EMISSOR_1..3``) are CPF-or-CNPJ **by definition** — each has a sibling
``PF_PJ_*`` column whose domain is ``PF``/``PJ`` — and the ``PF`` case **occurs in practice**
(measured in ``PF_PJ_COMITENTE_2``). Declaring one as a CNPJ column would pass in an all-PJ month
and raise on the first individual, so they stay out of ``tuple_cnpj_cols``. They are also personal
data: the fixtures are header-only.

⚠️ **The five ``CENARIO_FPR_*`` columns look numeric and are not** — they carry values like
``-0,0004`` (a **comma** decimal separator) mixed with free text (``pessimista``, ``-``), and the
META declares them ``varchar(150)``. They stay exact text, like every other column the reader does
not coerce to a date.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# The 105 columns shared by both regimes, in published file order — everything from
# ``DENOM_SOCIAL`` onward. Declared once because the two headers were **measured** identical here;
# the regimes differ only in the key block before it, which each contract spells out for itself.
_TUPLE_SHARED_TAIL: tuple[str, ...] = (
	"DENOM_SOCIAL",
	"DT_COMPTC",
	"VERSAO",
	"NR_COTST_PF_PB",
	"NR_COTST_PF_VAREJO",
	"NR_COTST_PJ_NAO_FINANC_PB",
	"NR_COTST_PJ_NAO_FINANC_VAREJO",
	"NR_COTST_BANCO",
	"NR_COTST_CORRETORA_DISTRIB",
	"NR_COTST_PJ_FINANC",
	"NR_COTST_INVNR",
	"NR_COTST_EAPC",
	"NR_COTST_EFPC",
	"NR_COTST_RPPS",
	"NR_COTST_SEGUR",
	"NR_COTST_CAPITALIZ",
	"NR_COTST_FI_CLUBE",
	"NR_COTST_DISTRIB",
	"NR_COTST_OUTRO",
	"PR_PL_COTST_PF_PB",
	"PR_PL_COTST_PF_VAREJO",
	"PR_PL_COTST_PJ_NAO_FINANC_PB",
	"PR_PL_COTST_PJ_NAO_FINANC_VAREJO",
	"PR_PL_COTST_BANCO",
	"PR_PL_COTST_CORRETORA_DISTRIB",
	"PR_PL_COTST_PJ_FINANC",
	"PR_PL_COTST_INVNR",
	"PR_PL_COTST_EAPC",
	"PR_PL_COTST_EFPC",
	"PR_PL_COTST_RPPS",
	"PR_PL_COTST_SEGUR",
	"PR_PL_COTST_CAPITALIZ",
	"PR_PL_COTST_FI_CLUBE",
	"PR_PL_COTST_DISTRIB",
	"PR_PL_COTST_OUTRO",
	"VOTO_ADMIN_ASSEMB",
	"JUSTIF_VOTO_ADMIN_ASSEMB",
	"PR_VAR_CARTEIRA",
	"MOD_VAR",
	"PRAZO_CARTEIRA_TITULO",
	"DELIB_ASSEMB",
	"VL_CONTRATO_COMPRA_DOLAR",
	"VL_CONTRATO_VENDA_DOLAR",
	"PR_VARIACAO_DIARIA_COTA",
	"FPR",
	"CENARIO_FPR_IBOVESPA",
	"CENARIO_FPR_JUROS",
	"CENARIO_FPR_CUPOM",
	"CENARIO_FPR_DOLAR",
	"CENARIO_FPR_OUTRO",
	"PR_VARIACAO_DIARIA_COTA_ESTRESSE",
	"PR_VARIACAO_DIARIA_PL_TAXA_ANUAL",
	"PR_VARIACAO_DIARIA_PL_TAXA_CAMBIO",
	"PR_VARIACAO_DIARIA_PL_IBOVESPA",
	"FATOR_RISCO_OUTRO",
	"PR_VARIACAO_DIARIA_OUTRO",
	"PR_COLATERAL_DERIV",
	"FATOR_RISCO_NOCIONAL",
	"VL_FATOR_RISCO_NOCIONAL_LONG_IBOVESPA",
	"VL_FATOR_RISCO_NOCIONAL_LONG_JUROS",
	"VL_FATOR_RISCO_NOCIONAL_LONG_CUPOM",
	"VL_FATOR_RISCO_NOCIONAL_LONG_DOLAR",
	"VL_FATOR_RISCO_NOCIONAL_LONG_OUTRO",
	"VL_FATOR_RISCO_NOCIONAL_SHORT_IBOVESPA",
	"VL_FATOR_RISCO_NOCIONAL_SHORT_JUROS",
	"VL_FATOR_RISCO_NOCIONAL_SHORT_CUPOM",
	"VL_FATOR_RISCO_NOCIONAL_SHORT_DOLAR",
	"VL_FATOR_RISCO_NOCIONAL_SHORT_OUTRO",
	"PF_PJ_COMITENTE_1",
	"CPF_CNPJ_COMITENTE_1",
	"COMITENTE_LIGADO_1",
	"PR_COMITENTE_1",
	"PF_PJ_COMITENTE_2",
	"CPF_CNPJ_COMITENTE_2",
	"COMITENTE_LIGADO_2",
	"PR_COMITENTE_2",
	"PF_PJ_COMITENTE_3",
	"CPF_CNPJ_COMITENTE_3",
	"COMITENTE_LIGADO_3",
	"PR_COMITENTE_3",
	"PR_ATIVO_EMISSOR_LIGADO",
	"PF_PJ_EMISSOR_1",
	"CPF_CNPJ_EMISSOR_1",
	"EMISSOR_LIGADO_1",
	"PR_EMISSOR_1",
	"PF_PJ_EMISSOR_2",
	"CPF_CNPJ_EMISSOR_2",
	"EMISSOR_LIGADO_2",
	"PR_EMISSOR_2",
	"PF_PJ_EMISSOR_3",
	"CPF_CNPJ_EMISSOR_3",
	"EMISSOR_LIGADO_3",
	"PR_EMISSOR_3",
	"PR_ATIVO_CRED_PRIV",
	"VEDAC_TAXA_PERFM",
	"DT_COTA_TAXA_PERFM",
	"VL_COTA_TAXA_PERFM",
	"VL_DIREITO_DISTRIB",
	"NR_COTST_ENTID_PREVID_COMPL",
	"PR_COTST_ENTID_PREVID_COMPL",
	"PR_PATRIM_LIQ_MAIOR_COTST",
	"NR_DIA_CINQU_PERC",
	"NR_DIA_CEM_PERC",
	"ST_LIQDEZ",
	"PR_PATRIM_LIQ_CONVTD_CAIXA",
)


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
# Post-RCVM 175 (``202312`` onward): the fund/class split puts TWO identifier columns up front.
PERFIL_MENSAL_FI = FileContract(
	"Perfil Mensal FI",
	"perfil_mensal_fi",
	("TP_FUNDO_CLASSE", "CNPJ_FUNDO_CLASSE", *_TUPLE_SHARED_TAIL),
	("CNPJ_FUNDO_CLASSE",),
)

# Pre-RCVM 175 (``201901``–``202311``): one identifier column, and no ``TP_FUNDO_CLASSE``.
PERFIL_MENSAL_FI_PRE175 = FileContract(
	"Perfil Mensal FI (pre-RCVM 175)",
	"perfil_mensal_fi_pre175",
	("CNPJ_FUNDO", *_TUPLE_SHARED_TAIL),
	("CNPJ_FUNDO",),
)
