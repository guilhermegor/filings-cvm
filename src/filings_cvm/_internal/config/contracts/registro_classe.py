"""Data contract for the CVM open-data *registro_classe* CSV (ingestion).

The `registro_classe.csv` member of `registro_fundo_classe.zip` is the **class** level of the
post-**Resolução CVM 175** fund → class → subclass hierarchy. Verified against the real
archive (36,389 rows): 30 columns, in this order.

`ID_Registro_Classe` is the class's surrogate key; `ID_Registro_Fundo` is the foreign key back
to `registro_fundo` (resolves 100% on the real file). `CNPJ_Classe` arrives as **bare digits**
and is the only column declared as a CNPJ column — `CNPJ_Auditor`, `CNPJ_Custodiante` and
`CNPJ_Controlador` are counterparty identifiers, null on many rows, not validated here.

All 30 columns are declared required so a column CVM drops or renames fails loudly at read time.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
REGISTRO_CLASSE = FileContract(
	"Registro Classe (RCVM 175)",
	"registro_classe",
	(
		"ID_Registro_Fundo",
		"ID_Registro_Classe",
		"CNPJ_Classe",
		"Codigo_CVM",
		"Data_Registro",
		"Data_Constituicao",
		"Data_Inicio",
		"Tipo_Classe",
		"Denominacao_Social",
		"Situacao",
		"Data_Inicio_Situacao",
		"Classificacao",
		"Indicador_Desempenho",
		"Classe_Cotas",
		"Classificacao_Anbima",
		"Tributacao_Longo_Prazo",
		"Entidade_Investimento",
		"Permitido_Aplicacao_CemPorCento_Exterior",
		"Classe_ESG",
		"Forma_Condominio",
		"Exclusivo",
		"Publico_Alvo",
		"Patrimonio_Liquido",
		"Data_Patrimonio_Liquido",
		"CNPJ_Auditor",
		"Auditor",
		"CNPJ_Custodiante",
		"Custodiante",
		"CNPJ_Controlador",
		"Controlador",
	),
	("CNPJ_Classe",),
)
