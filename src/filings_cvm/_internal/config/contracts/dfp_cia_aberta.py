"""Data contracts for the CVM open-data *DFP CIA_ABERTA* CSVs (ingestion) — all 19 members.

`dfp_cia_aberta_AAAA.zip` (dataset `CIA_ABERTA/DOC/DFP`, *Demonstrações Financeiras Padronizadas*)
holds **19 members and ~1,17 million rows** in 2025: the filing index, eight statement types each
published in a *consolidado* (`_con`) and an *individual* (`_ind`) variant, plus the share
composition and the auditor's opinion.

Every column list is **generated from the real 2025 headers**, not transcribed, and pinned verbatim
to `tests/fixtures/dfp_cia_aberta/`.

⚠️⚠️ **This dataset INVERTS the hazard every earlier one carried.** In CRA, CRI, FCA and FRE the
rule was *"members of equal width have different columns — never copy the sibling"*. Here the
sixteen statement members collapse into **three** column lists, and members really are identical:

- **14 columns** — `BPA_con/ind`, `BPP_con/ind`. A balance sheet is a point in time, so it carries
  only `DT_FIM_EXERC`.
- **15 columns** — `DFC_MD`, `DFC_MI`, `DRA`, `DRE` and `DVA`, each in `_con` and `_ind`. A flow
  statement covers a period, so it adds `DT_INI_EXERC`.
- **16 columns** — `DMPL_con/ind`, which adds `COLUNA_DF`, the equity column a movement belongs to.

Nineteen members, **six** distinct lists in total (the three above plus the index, the share
composition and the opinion).

**This is measured, not assumed.** Each contract is still generated from **its own** published
header, and a test asserts the grouping against the pinned fixtures. Presuming members are
identical and presuming they differ are the same mistake — neither is measurement. The precedent is
CRI, where two of seven sections genuinely matched CRA and the coincidence belonged to the source.

⚠️⚠️ **`VL_CONTA` is money and stays exact text.** It arrives with ten decimal places
(`2398719197.0000000000`) — the shape where a binary float drops published digits silently, already
measured on VLMO. And **its scale lives in a different column**: `ESCALA_MOEDA` is `MIL` or
`UNIDADE`, so summing `VL_CONTA` without reading `ESCALA_MOEDA` is wrong by a factor of a thousand.
The readers do not rescale — that would destroy the published figure.

⚠️ **`CD_CVM` arrives with a leading zero** (`001023`), so it is text; a numeric type drops it
silently (measured before on CGVN).

⚠️ **Every member uses `CNPJ_CIA` / `DT_REFER`**, the index's own naming — unlike FCA and FRE, whose
satellites switch to `CNPJ_Companhia` / `Data_Referencia`. There is no rule across the `DOC`
datasets, only per-dataset measurement.

⚠️ **No unique key is asserted anywhere.** `ORDEM_EXERC` (`ÚLTIMO` / `PENÚLTIMO`) repeats each
account for the comparative period.

Counts (`QT_ACAO_*`) are exact text too; see `bin/check_dtypes.py`.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.

DFP_CIA_ABERTA = FileContract(
	"DFP CIA_ABERTA — índice dos formulários",
	"dfp_cia_aberta",
	(
		"CNPJ_CIA",
		"DT_REFER",
		"VERSAO",
		"DENOM_CIA",
		"CD_CVM",
		"CATEG_DOC",
		"ID_DOC",
		"DT_RECEB",
		"LINK_DOC",
	),
	("CNPJ_CIA",),
)

DFP_CIA_ABERTA_BPA_CON = FileContract(
	"DFP CIA_ABERTA — balanço patrimonial ativo (consolidado)",
	"dfp_cia_aberta_BPA_con",
	(
		"CNPJ_CIA",
		"DT_REFER",
		"VERSAO",
		"DENOM_CIA",
		"CD_CVM",
		"GRUPO_DFP",
		"MOEDA",
		"ESCALA_MOEDA",
		"ORDEM_EXERC",
		"DT_FIM_EXERC",
		"CD_CONTA",
		"DS_CONTA",
		"VL_CONTA",
		"ST_CONTA_FIXA",
	),
	("CNPJ_CIA",),
)

DFP_CIA_ABERTA_BPA_IND = FileContract(
	"DFP CIA_ABERTA — balanço patrimonial ativo (individual)",
	"dfp_cia_aberta_BPA_ind",
	(
		"CNPJ_CIA",
		"DT_REFER",
		"VERSAO",
		"DENOM_CIA",
		"CD_CVM",
		"GRUPO_DFP",
		"MOEDA",
		"ESCALA_MOEDA",
		"ORDEM_EXERC",
		"DT_FIM_EXERC",
		"CD_CONTA",
		"DS_CONTA",
		"VL_CONTA",
		"ST_CONTA_FIXA",
	),
	("CNPJ_CIA",),
)

DFP_CIA_ABERTA_BPP_CON = FileContract(
	"DFP CIA_ABERTA — balanço patrimonial passivo (consolidado)",
	"dfp_cia_aberta_BPP_con",
	(
		"CNPJ_CIA",
		"DT_REFER",
		"VERSAO",
		"DENOM_CIA",
		"CD_CVM",
		"GRUPO_DFP",
		"MOEDA",
		"ESCALA_MOEDA",
		"ORDEM_EXERC",
		"DT_FIM_EXERC",
		"CD_CONTA",
		"DS_CONTA",
		"VL_CONTA",
		"ST_CONTA_FIXA",
	),
	("CNPJ_CIA",),
)

DFP_CIA_ABERTA_BPP_IND = FileContract(
	"DFP CIA_ABERTA — balanço patrimonial passivo (individual)",
	"dfp_cia_aberta_BPP_ind",
	(
		"CNPJ_CIA",
		"DT_REFER",
		"VERSAO",
		"DENOM_CIA",
		"CD_CVM",
		"GRUPO_DFP",
		"MOEDA",
		"ESCALA_MOEDA",
		"ORDEM_EXERC",
		"DT_FIM_EXERC",
		"CD_CONTA",
		"DS_CONTA",
		"VL_CONTA",
		"ST_CONTA_FIXA",
	),
	("CNPJ_CIA",),
)

DFP_CIA_ABERTA_DFC_MD_CON = FileContract(
	"DFP CIA_ABERTA — fluxo de caixa, método direto (consolidado)",
	"dfp_cia_aberta_DFC_MD_con",
	(
		"CNPJ_CIA",
		"DT_REFER",
		"VERSAO",
		"DENOM_CIA",
		"CD_CVM",
		"GRUPO_DFP",
		"MOEDA",
		"ESCALA_MOEDA",
		"ORDEM_EXERC",
		"DT_INI_EXERC",
		"DT_FIM_EXERC",
		"CD_CONTA",
		"DS_CONTA",
		"VL_CONTA",
		"ST_CONTA_FIXA",
	),
	("CNPJ_CIA",),
)

DFP_CIA_ABERTA_DFC_MD_IND = FileContract(
	"DFP CIA_ABERTA — fluxo de caixa, método direto (individual)",
	"dfp_cia_aberta_DFC_MD_ind",
	(
		"CNPJ_CIA",
		"DT_REFER",
		"VERSAO",
		"DENOM_CIA",
		"CD_CVM",
		"GRUPO_DFP",
		"MOEDA",
		"ESCALA_MOEDA",
		"ORDEM_EXERC",
		"DT_INI_EXERC",
		"DT_FIM_EXERC",
		"CD_CONTA",
		"DS_CONTA",
		"VL_CONTA",
		"ST_CONTA_FIXA",
	),
	("CNPJ_CIA",),
)

DFP_CIA_ABERTA_DFC_MI_CON = FileContract(
	"DFP CIA_ABERTA — fluxo de caixa, método indireto (consolidado)",
	"dfp_cia_aberta_DFC_MI_con",
	(
		"CNPJ_CIA",
		"DT_REFER",
		"VERSAO",
		"DENOM_CIA",
		"CD_CVM",
		"GRUPO_DFP",
		"MOEDA",
		"ESCALA_MOEDA",
		"ORDEM_EXERC",
		"DT_INI_EXERC",
		"DT_FIM_EXERC",
		"CD_CONTA",
		"DS_CONTA",
		"VL_CONTA",
		"ST_CONTA_FIXA",
	),
	("CNPJ_CIA",),
)

DFP_CIA_ABERTA_DFC_MI_IND = FileContract(
	"DFP CIA_ABERTA — fluxo de caixa, método indireto (individual)",
	"dfp_cia_aberta_DFC_MI_ind",
	(
		"CNPJ_CIA",
		"DT_REFER",
		"VERSAO",
		"DENOM_CIA",
		"CD_CVM",
		"GRUPO_DFP",
		"MOEDA",
		"ESCALA_MOEDA",
		"ORDEM_EXERC",
		"DT_INI_EXERC",
		"DT_FIM_EXERC",
		"CD_CONTA",
		"DS_CONTA",
		"VL_CONTA",
		"ST_CONTA_FIXA",
	),
	("CNPJ_CIA",),
)

DFP_CIA_ABERTA_DMPL_CON = FileContract(
	"DFP CIA_ABERTA — mutações do patrimônio líquido (consolidado)",
	"dfp_cia_aberta_DMPL_con",
	(
		"CNPJ_CIA",
		"DT_REFER",
		"VERSAO",
		"DENOM_CIA",
		"CD_CVM",
		"GRUPO_DFP",
		"MOEDA",
		"ESCALA_MOEDA",
		"ORDEM_EXERC",
		"DT_INI_EXERC",
		"DT_FIM_EXERC",
		"COLUNA_DF",
		"CD_CONTA",
		"DS_CONTA",
		"VL_CONTA",
		"ST_CONTA_FIXA",
	),
	("CNPJ_CIA",),
)

DFP_CIA_ABERTA_DMPL_IND = FileContract(
	"DFP CIA_ABERTA — mutações do patrimônio líquido (individual)",
	"dfp_cia_aberta_DMPL_ind",
	(
		"CNPJ_CIA",
		"DT_REFER",
		"VERSAO",
		"DENOM_CIA",
		"CD_CVM",
		"GRUPO_DFP",
		"MOEDA",
		"ESCALA_MOEDA",
		"ORDEM_EXERC",
		"DT_INI_EXERC",
		"DT_FIM_EXERC",
		"COLUNA_DF",
		"CD_CONTA",
		"DS_CONTA",
		"VL_CONTA",
		"ST_CONTA_FIXA",
	),
	("CNPJ_CIA",),
)

DFP_CIA_ABERTA_DRA_CON = FileContract(
	"DFP CIA_ABERTA — resultado abrangente (consolidado)",
	"dfp_cia_aberta_DRA_con",
	(
		"CNPJ_CIA",
		"DT_REFER",
		"VERSAO",
		"DENOM_CIA",
		"CD_CVM",
		"GRUPO_DFP",
		"MOEDA",
		"ESCALA_MOEDA",
		"ORDEM_EXERC",
		"DT_INI_EXERC",
		"DT_FIM_EXERC",
		"CD_CONTA",
		"DS_CONTA",
		"VL_CONTA",
		"ST_CONTA_FIXA",
	),
	("CNPJ_CIA",),
)

DFP_CIA_ABERTA_DRA_IND = FileContract(
	"DFP CIA_ABERTA — resultado abrangente (individual)",
	"dfp_cia_aberta_DRA_ind",
	(
		"CNPJ_CIA",
		"DT_REFER",
		"VERSAO",
		"DENOM_CIA",
		"CD_CVM",
		"GRUPO_DFP",
		"MOEDA",
		"ESCALA_MOEDA",
		"ORDEM_EXERC",
		"DT_INI_EXERC",
		"DT_FIM_EXERC",
		"CD_CONTA",
		"DS_CONTA",
		"VL_CONTA",
		"ST_CONTA_FIXA",
	),
	("CNPJ_CIA",),
)

DFP_CIA_ABERTA_DRE_CON = FileContract(
	"DFP CIA_ABERTA — demonstração do resultado (consolidado)",
	"dfp_cia_aberta_DRE_con",
	(
		"CNPJ_CIA",
		"DT_REFER",
		"VERSAO",
		"DENOM_CIA",
		"CD_CVM",
		"GRUPO_DFP",
		"MOEDA",
		"ESCALA_MOEDA",
		"ORDEM_EXERC",
		"DT_INI_EXERC",
		"DT_FIM_EXERC",
		"CD_CONTA",
		"DS_CONTA",
		"VL_CONTA",
		"ST_CONTA_FIXA",
	),
	("CNPJ_CIA",),
)

DFP_CIA_ABERTA_DRE_IND = FileContract(
	"DFP CIA_ABERTA — demonstração do resultado (individual)",
	"dfp_cia_aberta_DRE_ind",
	(
		"CNPJ_CIA",
		"DT_REFER",
		"VERSAO",
		"DENOM_CIA",
		"CD_CVM",
		"GRUPO_DFP",
		"MOEDA",
		"ESCALA_MOEDA",
		"ORDEM_EXERC",
		"DT_INI_EXERC",
		"DT_FIM_EXERC",
		"CD_CONTA",
		"DS_CONTA",
		"VL_CONTA",
		"ST_CONTA_FIXA",
	),
	("CNPJ_CIA",),
)

DFP_CIA_ABERTA_DVA_CON = FileContract(
	"DFP CIA_ABERTA — valor adicionado (consolidado)",
	"dfp_cia_aberta_DVA_con",
	(
		"CNPJ_CIA",
		"DT_REFER",
		"VERSAO",
		"DENOM_CIA",
		"CD_CVM",
		"GRUPO_DFP",
		"MOEDA",
		"ESCALA_MOEDA",
		"ORDEM_EXERC",
		"DT_INI_EXERC",
		"DT_FIM_EXERC",
		"CD_CONTA",
		"DS_CONTA",
		"VL_CONTA",
		"ST_CONTA_FIXA",
	),
	("CNPJ_CIA",),
)

DFP_CIA_ABERTA_DVA_IND = FileContract(
	"DFP CIA_ABERTA — valor adicionado (individual)",
	"dfp_cia_aberta_DVA_ind",
	(
		"CNPJ_CIA",
		"DT_REFER",
		"VERSAO",
		"DENOM_CIA",
		"CD_CVM",
		"GRUPO_DFP",
		"MOEDA",
		"ESCALA_MOEDA",
		"ORDEM_EXERC",
		"DT_INI_EXERC",
		"DT_FIM_EXERC",
		"CD_CONTA",
		"DS_CONTA",
		"VL_CONTA",
		"ST_CONTA_FIXA",
	),
	("CNPJ_CIA",),
)

DFP_CIA_ABERTA_COMPOSICAO_CAPITAL = FileContract(
	"DFP CIA_ABERTA — composição do capital",
	"dfp_cia_aberta_composicao_capital",
	(
		"CNPJ_CIA",
		"DT_REFER",
		"VERSAO",
		"DENOM_CIA",
		"QT_ACAO_ORDIN_CAP_INTEGR",
		"QT_ACAO_PREF_CAP_INTEGR",
		"QT_ACAO_TOTAL_CAP_INTEGR",
		"QT_ACAO_ORDIN_TESOURO",
		"QT_ACAO_PREF_TESOURO",
		"QT_ACAO_TOTAL_TESOURO",
	),
	("CNPJ_CIA",),
)

DFP_CIA_ABERTA_PARECER = FileContract(
	"DFP CIA_ABERTA — parecer e declarações",
	"dfp_cia_aberta_parecer",
	(
		"CNPJ_CIA",
		"DT_REFER",
		"VERSAO",
		"DENOM_CIA",
		"TP_RELAT_AUD",
		"TP_PARECER_DECL",
		"NUM_ITEM_PARECER_DECL",
		"TXT_PARECER_DECL",
	),
	("CNPJ_CIA",),
)
