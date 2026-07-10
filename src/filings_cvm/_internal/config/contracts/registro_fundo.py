"""Data contract for the CVM open-data *registro_fundo* CSV (ingestion).

The post-**Resolução CVM 175** registry ships `registro_fundo_classe.zip`, whose
`registro_fundo.csv` member is the **fund** level of the fund → class → subclass hierarchy.
Verified against the real archive (89,124 rows): 21 columns, in this order.

Unlike the legacy `cad_fi.csv`, this is where **live** funds are — 34,172 rows are
``Em Funcionamento Normal`` here versus 22 there. `CNPJ_Fundo` arrives as **bare digits**
(``00016999000167``, not masked) and is the only column declared as a CNPJ column:
`CPF_CNPJ_Gestor` holds a **CPF** where ``Tipo_Pessoa_Gestor == "PF"`` (211 rows), and
`CNPJ_Administrador` is a counterparty identifier — neither is validated here.

All 21 columns are declared required so a column CVM drops or renames fails loudly at read
time. `ID_Registro_Fundo` is the surrogate key that `registro_classe` references.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
REGISTRO_FUNDO = FileContract(
	"Registro Fundo (RCVM 175)",
	"registro_fundo",
	(
		"ID_Registro_Fundo",
		"CNPJ_Fundo",
		"Codigo_CVM",
		"Data_Registro",
		"Data_Constituicao",
		"Tipo_Fundo",
		"Denominacao_Social",
		"Data_Cancelamento",
		"Situacao",
		"Data_Inicio_Situacao",
		"Data_Adaptacao_RCVM175",
		"Data_Inicio_Exercicio_Social",
		"Data_Fim_Exercicio_Social",
		"Patrimonio_Liquido",
		"Data_Patrimonio_Liquido",
		"Diretor",
		"CNPJ_Administrador",
		"Administrador",
		"Tipo_Pessoa_Gestor",
		"CPF_CNPJ_Gestor",
		"Gestor",
	),
	("CNPJ_Fundo",),
)
