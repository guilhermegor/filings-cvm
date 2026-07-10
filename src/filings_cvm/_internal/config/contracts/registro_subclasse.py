"""Data contract for the CVM open-data *registro_subclasse* CSV (ingestion).

The `registro_subclasse.csv` member of `registro_fundo_classe.zip` is the **subclass** level
of the post-**Resolução CVM 175** fund → class → subclass hierarchy. Verified against the real
archive (8,849 rows): 14 columns, in this order.

`ID_Subclasse` is the subclass's surrogate key; `ID_Registro_Classe` is the foreign key back to
`registro_classe` (resolves 100% on the real file). This member carries **no CNPJ column** — a
subclass has no CNPJ of its own — so the contract declares an empty CNPJ tuple. The remaining
columns beyond the keys and dates are membership flags (`Exclusivo`, `Previdenciario`,
`Exclusivo_INR`, …).

All 14 columns are declared required so a column CVM drops or renames fails loudly at read time.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
REGISTRO_SUBCLASSE = FileContract(
	"Registro Subclasse (RCVM 175)",
	"registro_subclasse",
	(
		"ID_Registro_Classe",
		"ID_Subclasse",
		"Codigo_CVM",
		"Data_Constituicao",
		"Data_Inicio",
		"Denominacao_Social",
		"Situacao",
		"Data_Inicio_Situacao",
		"Forma_Condominio",
		"Exclusivo",
		"Publico_Alvo",
		"Previdenciario",
		"Exclusivo_INR",
		"Exclusivo_Previdencia_Complementar",
	),
	(),
)
