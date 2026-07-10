"""Data contracts for the CVM open-data *CAD/FI histórico* CSVs (ingestion).

`cad_fi_hist.zip` ships **19 members**, one per mutable attribute of the legacy CAD/FI
registry — each a per-attribute **change-log** with `CNPJ_FUNDO`, `DT_REG`, the attribute's
value column(s), and its effective-date columns (`DT_INI_*`, usually `DT_FIM_*`). Verified
against the real archive: the column list and order below are exactly as published.

**Deviation from "one contract per file" — deliberate.** The rest of `contracts/` follows one
`FileContract` per module. These 19 are the members of a **single input artifact** (one ZIP,
one dataset page) and a **uniform family** (same shape, differing only by attribute), so 19
near-identical one-constant modules would be pure sprawl. They live together here, one constant
each, re-exported individually from `contracts/__init__`. `CNPJ_FUNDO` is the CNPJ column of
every member; a subclass reader pairs each constant with its date columns.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
CAD_FI_HIST_ADMIN = FileContract(
	"CAD/FI histórico — administrador",
	"cad_fi_hist_admin",
	("CNPJ_FUNDO", "DT_REG", "CNPJ_ADMIN", "ADMIN", "DT_INI_ADMIN", "DT_FIM_ADMIN"),
	("CNPJ_FUNDO",),
)

CAD_FI_HIST_AUDITOR = FileContract(
	"CAD/FI histórico — auditor",
	"cad_fi_hist_auditor",
	("CNPJ_FUNDO", "DT_REG", "CNPJ_AUDITOR", "AUDITOR", "DT_INI_AUDITOR", "DT_FIM_AUDITOR"),
	("CNPJ_FUNDO",),
)

CAD_FI_HIST_CLASSE = FileContract(
	"CAD/FI histórico — classe",
	"cad_fi_hist_classe",
	("CNPJ_FUNDO", "DT_REG", "CLASSE", "DT_INI_CLASSE", "DT_FIM_CLASSE"),
	("CNPJ_FUNDO",),
)

CAD_FI_HIST_CONDOM = FileContract(
	"CAD/FI histórico — condomínio",
	"cad_fi_hist_condom",
	("CNPJ_FUNDO", "DT_REG", "CONDOM", "DT_INI_CONDOM", "DT_FIM_CONDOM"),
	("CNPJ_FUNDO",),
)

CAD_FI_HIST_CONTROLADOR = FileContract(
	"CAD/FI histórico — controlador",
	"cad_fi_hist_controlador",
	(
		"CNPJ_FUNDO",
		"DT_REG",
		"CNPJ_CONTROLADOR",
		"CONTROLADOR",
		"DT_INI_CONTROLADOR",
		"DT_FIM_CONTROLADOR",
	),
	("CNPJ_FUNDO",),
)

CAD_FI_HIST_CUSTODIANTE = FileContract(
	"CAD/FI histórico — custodiante",
	"cad_fi_hist_custodiante",
	(
		"CNPJ_FUNDO",
		"DT_REG",
		"CNPJ_CUSTODIANTE",
		"CUSTODIANTE",
		"DT_INI_CUSTODIANTE",
		"DT_FIM_CUSTODIANTE",
	),
	("CNPJ_FUNDO",),
)

CAD_FI_HIST_DENOM_COMERC = FileContract(
	"CAD/FI histórico — denominação comercial",
	"cad_fi_hist_denom_comerc",
	("CNPJ_FUNDO", "DT_REG", "DENOM_COMERC", "DT_INI_DENOM_COMERC", "DT_FIM_DENOM_COMERC"),
	("CNPJ_FUNDO",),
)

CAD_FI_HIST_DENOM_SOCIAL = FileContract(
	"CAD/FI histórico — denominação social",
	"cad_fi_hist_denom_social",
	("CNPJ_FUNDO", "DT_REG", "DENOM_SOCIAL", "DT_INI_DENOM_SOCIAL", "DT_FIM_DENOM_SOCIAL"),
	("CNPJ_FUNDO",),
)

CAD_FI_HIST_DIRETOR_RESP = FileContract(
	"CAD/FI histórico — diretor responsável",
	"cad_fi_hist_diretor_resp",
	("CNPJ_FUNDO", "DT_REG", "DIRETOR", "DT_INI_DIRETOR", "DT_FIM_DIRETOR"),
	("CNPJ_FUNDO",),
)

CAD_FI_HIST_EXCLUSIVO = FileContract(
	"CAD/FI histórico — exclusivo",
	"cad_fi_hist_exclusivo",
	("CNPJ_FUNDO", "DT_REG", "FUNDO_EXCLUSIVO", "DT_INI_ST_EXCLUSIVO", "DT_FIM_ST_EXCLUSIVO"),
	("CNPJ_FUNDO",),
)

CAD_FI_HIST_EXERC_SOCIAL = FileContract(
	"CAD/FI histórico — exercício social",
	"cad_fi_hist_exerc_social",
	("CNPJ_FUNDO", "DT_REG", "DT_INI_EXERC", "DT_FIM_EXERC"),
	("CNPJ_FUNDO",),
)

CAD_FI_HIST_FIC = FileContract(
	"CAD/FI histórico — fundo de cotas",
	"cad_fi_hist_fic",
	("CNPJ_FUNDO", "DT_REG", "FUNDO_COTAS", "DT_INI_ST_COTAS", "DT_FIM_ST_COTAS"),
	("CNPJ_FUNDO",),
)

CAD_FI_HIST_GESTOR = FileContract(
	"CAD/FI histórico — gestor",
	"cad_fi_hist_gestor",
	(
		"CNPJ_FUNDO",
		"DT_REG",
		"PF_PJ_GESTOR",
		"CPF_CNPJ_GESTOR",
		"GESTOR",
		"DT_INI_GESTOR",
		"DT_FIM_GESTOR",
	),
	("CNPJ_FUNDO",),
)

CAD_FI_HIST_PUBLICO_ALVO = FileContract(
	"CAD/FI histórico — público-alvo",
	"cad_fi_hist_publico_alvo",
	("CNPJ_FUNDO", "DT_REG", "PUBLICO_ALVO", "DT_INI_PUBLICO_ALVO", "DT_FIM_PUBLICO_ALVO"),
	("CNPJ_FUNDO",),
)

CAD_FI_HIST_RENTAB = FileContract(
	"CAD/FI histórico — rentabilidade",
	"cad_fi_hist_rentab",
	("CNPJ_FUNDO", "DT_REG", "RENTAB_FUNDO", "DT_INI_RENTAB", "DT_FIM_RENTAB"),
	("CNPJ_FUNDO",),
)

CAD_FI_HIST_SIT = FileContract(
	"CAD/FI histórico — situação",
	"cad_fi_hist_sit",
	("CNPJ_FUNDO", "DT_REG", "SIT", "DT_INI_SIT", "DT_FIM_SIT"),
	("CNPJ_FUNDO",),
)

CAD_FI_HIST_TAXA_ADM = FileContract(
	"CAD/FI histórico — taxa de administração",
	"cad_fi_hist_taxa_adm",
	("CNPJ_FUNDO", "DT_REG", "TAXA_ADM", "INF_TAXA_ADM", "DT_INI_TAXA_ADM"),
	("CNPJ_FUNDO",),
)

CAD_FI_HIST_TAXA_PERFM = FileContract(
	"CAD/FI histórico — taxa de performance",
	"cad_fi_hist_taxa_perfm",
	("CNPJ_FUNDO", "DT_REG", "VL_TAXA_PERFM", "DS_TAXA_PERFM", "DT_INI_TAXA_PERFM"),
	("CNPJ_FUNDO",),
)

CAD_FI_HIST_TRIB_LPRAZO = FileContract(
	"CAD/FI histórico — tributação de longo prazo",
	"cad_fi_hist_trib_lprazo",
	("CNPJ_FUNDO", "DT_REG", "TRIB_LPRAZO", "DT_INI_ST_TRIB_LPRAZO", "DT_FIM_ST_TRIB_LPRAZO"),
	("CNPJ_FUNDO",),
)
