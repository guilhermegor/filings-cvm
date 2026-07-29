"""Data contracts for the CVM open-data *FRE CIA_ABERTA* CSVs (ingestion) — group 1 of 4.

`fre_cia_aberta_AAAA.zip` (dataset `CIA_ABERTA/DOC/FRE`, *Formulário de Referência*) is the largest
dataset in this portal: **36 members, ~131k rows**. It is implemented in four themed slices; this
module holds the first — the **index** plus the **capital-structure** tables. The remaining groups
(administração/pessoas, diversidade, remuneração) append their contracts here.

Every column list is **generated from the real 2025 headers**, not transcribed, and pinned to
`tests/fixtures/fre_cia_aberta/` verbatim.

⚠️ **The index uses a different naming convention from its own satellites** — `CNPJ_CIA` /
`DT_REFER` / `DT_RECEB` / `DENOM_CIA`, the `cad_cia_aberta.csv` style — while every satellite uses
`CNPJ_Companhia` / `Data_Referencia`. FCA does the same; CGVN does **not**. There is no rule to
infer across `DOC` datasets, only per-dataset measurement.

⚠️ **FRE uses six different CNPJ column names across its 36 members** (`CNPJ`, `CNPJ_Auditor`,
`CNPJ_CIA`, `CNPJ_Companhia`, `CNPJ_Emissor`, `CNPJ_Emissor_Pessoa_Relacionada`), so each member
declares its own rather than inheriting a shared assumption.

Monetary and count columns (`Valor_Capital`, `Quantidade_*`, `Percentual_*`) stay **exact source
text** — never a binary float; see `bin/check_dtypes.py`.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.

FRE_CIA_ABERTA = FileContract(
	"FRE CIA_ABERTA — índice dos formulários",
	"fre_cia_aberta",
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

FRE_CIA_ABERTA_CAPITAL_SOCIAL = FileContract(
	"FRE CIA_ABERTA — capital social",
	"fre_cia_aberta_capital_social",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"ID_Capital_Social",
		"Tipo_Capital",
		"Data_Autorizacao_Aprovacao",
		"Valor_Capital",
		"Prazo_Integralizacao",
		"Quantidade_Acoes_Ordinarias",
		"Quantidade_Acoes_Preferenciais",
		"Quantidade_Total_Acoes",
	),
	("CNPJ_Companhia",),
)

FRE_CIA_ABERTA_CAPITAL_SOCIAL_CLASSE_ACAO = FileContract(
	"FRE CIA_ABERTA — capital social por classe de ação",
	"fre_cia_aberta_capital_social_classe_acao",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"ID_Capital_Social",
		"Tipo_Classe_Acao_Preferencial",
		"Quantidade_Acoes",
	),
	("CNPJ_Companhia",),
)

FRE_CIA_ABERTA_CAPITAL_SOCIAL_TITULO_CONVERSIVEL = FileContract(
	"FRE CIA_ABERTA — títulos conversíveis",
	"fre_cia_aberta_capital_social_titulo_conversivel",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"ID_Capital_Social",
		"Titulo_Conversivel_Acao",
		"Condicoes_Conversao",
	),
	("CNPJ_Companhia",),
)

FRE_CIA_ABERTA_DISTRIBUICAO_CAPITAL = FileContract(
	"FRE CIA_ABERTA — distribuição do capital",
	"fre_cia_aberta_distribuicao_capital",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"Quantidade_Acionistas_PF",
		"Quantidade_Acionistas_PJ",
		"Quantidade_Acionistas_Investidores_Institucionais",
		"Quantidade_Acoes_Ordinarias_Circulacao",
		"Percentual_Acoes_Ordinarias_Circulacao",
		"Quantidade_Acoes_Preferenciais_Circulacao",
		"Percentual_Acoes_Preferenciais_Circulacao",
		"Quantidade_Total_Acoes_Circulacao",
		"Percentual_Total_Acoes_Circulacao",
		"Data_Ultima_Assembleia",
	),
	("CNPJ_Companhia",),
)

FRE_CIA_ABERTA_DISTRIBUICAO_CAPITAL_CLASSE_ACAO = FileContract(
	"FRE CIA_ABERTA — distribuição do capital por classe",
	"fre_cia_aberta_distribuicao_capital_classe_acao",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"Sigla_Classe_Acoes_Preferenciais",
		"Classe_Acoes_Preferenciais",
		"Quantidade_Acoes_Preferenciais_Circulacao",
		"Percentual_Acoes_Preferenciais_Circulacao",
	),
	("CNPJ_Companhia",),
)

FRE_CIA_ABERTA_RESPONSAVEL = FileContract(
	"FRE CIA_ABERTA — responsáveis pelo formulário",
	"fre_cia_aberta_responsavel",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"Nome_Responsavel",
		"Cargo_Responsavel",
	),
	("CNPJ_Companhia",),
)

FRE_CIA_ABERTA_MERCADO_ESTRANGEIRO = FileContract(
	"FRE CIA_ABERTA — mercados estrangeiros",
	"fre_cia_aberta_mercado_estrangeiro",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"Valor_Mobiliario",
		"Identificacao_Valor_Mobiliario",
		"Pais_Negociacao",
		"Mercado",
		"Administradora",
		"Data_Emissao",
		"Data_Inicio_Listagem",
		"Percentual",
		"Descricao_Segmento",
		"Descricao_Proporcao_Certificado",
		"Descricao_Banco_Depositario",
		"Descricao_Instituicao_Custodiante",
	),
	("CNPJ_Companhia",),
)
