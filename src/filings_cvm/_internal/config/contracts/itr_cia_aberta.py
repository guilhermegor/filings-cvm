"""Data contracts for the CVM open-data *ITR CIA_ABERTA* CSVs (ingestion) — all 19 members.

`itr_cia_aberta_AAAA.zip` (dataset `CIA_ABERTA/DOC/ITR`, *Informações Trimestrais*) holds **19
members and 3.640.994 rows** in 2025 — three times the DFP, and the largest artifact this library
reads. Same shape as the annual filing: the index, eight statement types in a *consolidado*
(`_con`) and an *individual* (`_ind`) variant, plus the share composition and the reviewer's
opinion.

Every column list is **generated from the real 2025 headers**, not transcribed and **not copied
from DFP**, and pinned verbatim to `tests/fixtures/itr_cia_aberta/`.

⚠️⚠️ **Eighteen of the nineteen members are byte-identical to DFP's — and exactly one is not.**
Measured header by header against DFP's pinned fixtures:

| | DFP | ITR |
|---|---|---|
| `parecer`, column 5 | `TP_RELAT_AUD` | **`TP_RELAT_ESP`** |

It is semantically right — the annual filing is *audited*, the quarterly one gets a *revisão
especial* — and that is exactly what makes it dangerous. Copying DFP's `parecer` contract matches
the width (8), the position, and seven of the eight names; only the pinned header disagrees.

**This is the counterpart to the lesson DFP taught.** There the finding was that here, unlike
CRA / CRI / FCA / FRE, sibling members really are identical. Carrying *that* generalisation across
to the neighbouring dataset is the same mistake in a new coat: **18-of-19 identical is precisely
what makes someone copy the 19th.**

The sixteen statement members again collapse into three column lists:

- **14 columns** — `BPA_con/ind`, `BPP_con/ind`. A balance sheet is a point in time, so it carries
  only `DT_FIM_EXERC`.
- **15 columns** — `DFC_MD`, `DFC_MI`, `DRA`, `DRE` and `DVA`, each in `_con` and `_ind`. A flow
  statement covers a period, so it adds `DT_INI_EXERC`.
- **16 columns** — `DMPL_con/ind`, which adds `COLUNA_DF`, the equity column a movement belongs to.

⚠️⚠️ **`VL_CONTA` is money and stays exact text, and its scale lives in a different column.**
`ESCALA_MOEDA` is `MIL` or `UNIDADE`, so summing `VL_CONTA` without reading `ESCALA_MOEDA` is wrong
by a factor of a thousand. The readers do not rescale.

⚠️ **`CD_CVM` arrives with a leading zero**, so it is text. **Every member uses `CNPJ_CIA` /
`DT_REFER`** (100% valid, measured over distinct values), and every `DT_*` column is 100% ISO.

⚠️ **No unique key is asserted.** `ORDEM_EXERC` (`ÚLTIMO` / `PENÚLTIMO`) repeats each account for
the comparative period.

Counts (`QT_ACAO_*`) are exact text too; see `bin/check_dtypes.py`.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.

ITR_CIA_ABERTA = FileContract(
	"ITR CIA_ABERTA — índice dos formulários",
	"itr_cia_aberta",
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

ITR_CIA_ABERTA_BPA_CON = FileContract(
	"ITR CIA_ABERTA — balanço patrimonial ativo (consolidado)",
	"itr_cia_aberta_BPA_con",
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

ITR_CIA_ABERTA_BPA_IND = FileContract(
	"ITR CIA_ABERTA — balanço patrimonial ativo (individual)",
	"itr_cia_aberta_BPA_ind",
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

ITR_CIA_ABERTA_BPP_CON = FileContract(
	"ITR CIA_ABERTA — balanço patrimonial passivo (consolidado)",
	"itr_cia_aberta_BPP_con",
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

ITR_CIA_ABERTA_BPP_IND = FileContract(
	"ITR CIA_ABERTA — balanço patrimonial passivo (individual)",
	"itr_cia_aberta_BPP_ind",
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

ITR_CIA_ABERTA_DFC_MD_CON = FileContract(
	"ITR CIA_ABERTA — fluxo de caixa, método direto (consolidado)",
	"itr_cia_aberta_DFC_MD_con",
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

ITR_CIA_ABERTA_DFC_MD_IND = FileContract(
	"ITR CIA_ABERTA — fluxo de caixa, método direto (individual)",
	"itr_cia_aberta_DFC_MD_ind",
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

ITR_CIA_ABERTA_DFC_MI_CON = FileContract(
	"ITR CIA_ABERTA — fluxo de caixa, método indireto (consolidado)",
	"itr_cia_aberta_DFC_MI_con",
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

ITR_CIA_ABERTA_DFC_MI_IND = FileContract(
	"ITR CIA_ABERTA — fluxo de caixa, método indireto (individual)",
	"itr_cia_aberta_DFC_MI_ind",
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

ITR_CIA_ABERTA_DMPL_CON = FileContract(
	"ITR CIA_ABERTA — mutações do patrimônio líquido (consolidado)",
	"itr_cia_aberta_DMPL_con",
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

ITR_CIA_ABERTA_DMPL_IND = FileContract(
	"ITR CIA_ABERTA — mutações do patrimônio líquido (individual)",
	"itr_cia_aberta_DMPL_ind",
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

ITR_CIA_ABERTA_DRA_CON = FileContract(
	"ITR CIA_ABERTA — resultado abrangente (consolidado)",
	"itr_cia_aberta_DRA_con",
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

ITR_CIA_ABERTA_DRA_IND = FileContract(
	"ITR CIA_ABERTA — resultado abrangente (individual)",
	"itr_cia_aberta_DRA_ind",
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

ITR_CIA_ABERTA_DRE_CON = FileContract(
	"ITR CIA_ABERTA — demonstração do resultado (consolidado)",
	"itr_cia_aberta_DRE_con",
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

ITR_CIA_ABERTA_DRE_IND = FileContract(
	"ITR CIA_ABERTA — demonstração do resultado (individual)",
	"itr_cia_aberta_DRE_ind",
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

ITR_CIA_ABERTA_DVA_CON = FileContract(
	"ITR CIA_ABERTA — valor adicionado (consolidado)",
	"itr_cia_aberta_DVA_con",
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

ITR_CIA_ABERTA_DVA_IND = FileContract(
	"ITR CIA_ABERTA — valor adicionado (individual)",
	"itr_cia_aberta_DVA_ind",
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

ITR_CIA_ABERTA_COMPOSICAO_CAPITAL = FileContract(
	"ITR CIA_ABERTA — composição do capital",
	"itr_cia_aberta_composicao_capital",
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

ITR_CIA_ABERTA_PARECER = FileContract(
	"ITR CIA_ABERTA — relatório de revisão especial e declarações",
	"itr_cia_aberta_parecer",
	(
		"CNPJ_CIA",
		"DT_REFER",
		"VERSAO",
		"DENOM_CIA",
		"TP_RELAT_ESP",
		"TP_PARECER_DECL",
		"NUM_ITEM_PARECER_DECL",
		"TXT_PARECER_DECL",
	),
	("CNPJ_CIA",),
)
