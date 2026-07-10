"""Data contract for the CVM open-data *Cadastro de Fundos* (CAD/FI) CSV (ingestion).

`cad_fi.csv` is a **current-state snapshot** of the fund registry — a bare CSV, not a monthly
ZIP, and not partitioned by reference month. Verified against the real file (46,809 rows):
41 columns, in this order.

All 41 are declared required. This is a single-layout file, so a column CVM drops or renames
must fail loudly at read time rather than surfacing as a `KeyError` deep in a consumer's
transform. Extra columns are tolerated; missing ones are not.

`CNPJ_FUNDO` arrives **masked** (`00.000.684/0001-21`) and is the only column declared as a
CNPJ column. Deliberately excluded:

- `CPF_CNPJ_GESTOR` holds a **CPF** for 47 rows (`PF_PJ_GESTOR == "PF"`), so a CNPJ check
  would reject a valid registry.
- `CNPJ_ADMIN`, `CNPJ_AUDITOR`, `CNPJ_CUSTODIANTE`, `CNPJ_CONTROLADOR` are counterparty
  identifiers that are null on most rows; the contract's check demands at least one valid
  value, which they satisfy, but validating them here would conflate a defect in *this* file
  with a defect in a counterparty's registration.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
CAD_FI = FileContract(
	"Cadastro de Fundos (CAD/FI)",
	"cad_fi",
	(
		"TP_FUNDO",
		"CNPJ_FUNDO",
		"DENOM_SOCIAL",
		"DT_REG",
		"DT_CONST",
		"CD_CVM",
		"DT_CANCEL",
		"SIT",
		"DT_INI_SIT",
		"DT_INI_ATIV",
		"DT_INI_EXERC",
		"DT_FIM_EXERC",
		"CLASSE",
		"DT_INI_CLASSE",
		"RENTAB_FUNDO",
		"CONDOM",
		"FUNDO_COTAS",
		"FUNDO_EXCLUSIVO",
		"TRIB_LPRAZO",
		"PUBLICO_ALVO",
		"ENTID_INVEST",
		"TAXA_PERFM",
		"INF_TAXA_PERFM",
		"TAXA_ADM",
		"INF_TAXA_ADM",
		"VL_PATRIM_LIQ",
		"DT_PATRIM_LIQ",
		"DIRETOR",
		"CNPJ_ADMIN",
		"ADMIN",
		"PF_PJ_GESTOR",
		"CPF_CNPJ_GESTOR",
		"GESTOR",
		"CNPJ_AUDITOR",
		"AUDITOR",
		"CNPJ_CUSTODIANTE",
		"CUSTODIANTE",
		"CNPJ_CONTROLADOR",
		"CONTROLADOR",
		"INVEST_CEMPR_EXTER",
		"CLASSE_ANBIMA",
	),
	("CNPJ_FUNDO",),
)
