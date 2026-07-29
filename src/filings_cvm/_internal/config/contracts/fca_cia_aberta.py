"""Data contracts for the CVM open-data *FCA CIA_ABERTA* CSVs (ingestion).

`fca_cia_aberta_AAAA.zip` (dataset `CIA_ABERTA/DOC/FCA`, *Formulário Cadastral*) ships **ten
members**: an index plus nine detail tables. Every column list below was **generated from the real
2025 headers**, not transcribed, and is pinned to `tests/fixtures/fca_cia_aberta/` verbatim.

Three measured facts drive the declarations here:

- ⚠️ **The index member uses a different naming convention from its own nine satellites.**
  `fca_cia_aberta.csv` is `CNPJ_CIA` / `DT_REFER` / `VERSAO` / `DENOM_CIA` / `CD_CVM` / `ID_DOC` /
  `DT_RECEB` / `LINK_DOC` — uppercase and abbreviated, the `cad_cia_aberta.csv` style — while every
  satellite uses `CNPJ_Companhia` / `Data_Referencia` / `Versao` / `ID_Documento` /
  `Nome_Empresarial`. Writing the ten from one template silently breaks the index.
- ⚠️ **`departamento_acionistas` is header-only** (0 rows in 2025), so its `tuple_cnpj_cols` is
  **empty**: the CNPJ check requires a *present* valid value, and a legitimately empty artifact
  would otherwise raise. Same failure class as the CRI header-only members.
- ⚠️ **CPF columns stay out of `tuple_cnpj_cols`.** `dri.CPF_Responsavel` holds 1,003 CPFs and 4
  CNPJs, `auditor.CPF_Responsavel_Tecnico` 49 CPFs, and `auditor.CPF_CNPJ_Auditor` is a
  by-name-mixed column (all CNPJ in 2025, but a CPF year would break a CNPJ check). They are
  required *columns*, never CNPJ columns — and the fixtures are header-only because of them.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.

FCA_CIA_ABERTA = FileContract(
	"FCA CIA_ABERTA — índice dos formulários",
	"fca_cia_aberta",
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

FCA_CIA_ABERTA_AUDITOR = FileContract(
	"FCA CIA_ABERTA — auditores",
	"fca_cia_aberta_auditor",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Empresarial",
		"Auditor",
		"CPF_CNPJ_Auditor",
		"Codigo_CVM_Auditor",
		"Origem_Auditor",
		"Data_Inicio_Atuacao_Auditor",
		"Data_Fim_Atuacao_Auditor",
		"Responsavel_Tecnico",
		"CPF_Responsavel_Tecnico",
		"Data_Inicio_Atuacao_Responsavel_Tecnico",
		"Data_Fim_Atuacao_Responsavel_Tecnico",
	),
	("CNPJ_Companhia",),
)

FCA_CIA_ABERTA_CANAL_DIVULGACAO = FileContract(
	"FCA CIA_ABERTA — canais de divulgação",
	"fca_cia_aberta_canal_divulgacao",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Empresarial",
		"Canal_Divulgacao",
		"Sigla_UF",
	),
	("CNPJ_Companhia",),
)

FCA_CIA_ABERTA_DEPARTAMENTO_ACIONISTAS = FileContract(
	"FCA CIA_ABERTA — departamento de acionistas",
	"fca_cia_aberta_departamento_acionistas",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Empresarial",
		"Contato",
		"Data_Inicio_Contato",
		"Data_Fim_Contato",
		"Tipo_Endereco",
		"Logradouro",
		"Complemento",
		"Bairro",
		"Cidade",
		"Sigla_UF",
		"Pais",
		"CEP",
		"DDI_Telefone",
		"DDD_Telefone",
		"Telefone",
		"DDI_Fax",
		"DDD_Fax",
		"Fax",
		"Email",
	),
	(),
)

FCA_CIA_ABERTA_DRI = FileContract(
	"FCA CIA_ABERTA — diretor de relações com investidores",
	"fca_cia_aberta_dri",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Empresarial",
		"Tipo_Responsavel",
		"Responsavel",
		"CPF_Responsavel",
		"Tipo_Endereco",
		"Logradouro",
		"Complemento",
		"Bairro",
		"Cidade",
		"Sigla_UF",
		"UF",
		"Pais",
		"CEP",
		"DDI_Telefone",
		"DDD_Telefone",
		"Telefone",
		"DDI_Fax",
		"DDD_Fax",
		"Fax",
		"Email",
		"Data_Inicio_Atuacao",
		"Data_Fim_Atuacao",
	),
	("CNPJ_Companhia",),
)

FCA_CIA_ABERTA_ENDERECO = FileContract(
	"FCA CIA_ABERTA — endereços",
	"fca_cia_aberta_endereco",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Empresarial",
		"Tipo_Endereco",
		"Logradouro",
		"Complemento",
		"Bairro",
		"Cidade",
		"Sigla_UF",
		"Pais",
		"CEP",
		"Caixa_Postal",
		"DDI_Telefone",
		"DDD_Telefone",
		"Telefone",
		"DDI_Fax",
		"DDD_Fax",
		"Fax",
		"Email",
	),
	("CNPJ_Companhia",),
)

FCA_CIA_ABERTA_ESCRITURADOR = FileContract(
	"FCA CIA_ABERTA — escrituradores",
	"fca_cia_aberta_escriturador",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Empresarial",
		"Escriturador",
		"CNPJ_Escriturador",
		"Tipo_Endereco",
		"Logradouro",
		"Complemento",
		"Bairro",
		"Cidade",
		"Sigla_UF",
		"Pais",
		"CEP",
		"DDI_Telefone",
		"DDD_Telefone",
		"Telefone",
		"DDI_Fax",
		"DDD_Fax",
		"Fax",
		"Email",
		"Data_Inicio_Atuacao",
		"Data_Fim_Atuacao",
	),
	("CNPJ_Companhia", "CNPJ_Escriturador"),
)

FCA_CIA_ABERTA_GERAL = FileContract(
	"FCA CIA_ABERTA — dados gerais",
	"fca_cia_aberta_geral",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Empresarial",
		"Data_Nome_Empresarial",
		"Nome_Empresarial_Anterior",
		"Data_Constituicao",
		"Codigo_CVM",
		"Data_Registro_CVM",
		"Categoria_Registro_CVM",
		"Data_Categoria_Registro_CVM",
		"Situacao_Registro_CVM",
		"Data_Situacao_Registro_CVM",
		"Pais_Origem",
		"Pais_Custodia_Valores_Mobiliarios",
		"Setor_Atividade",
		"Descricao_Atividade",
		"Situacao_Emissor",
		"Data_Situacao_Emissor",
		"Especie_Controle_Acionario",
		"Data_Especie_Controle_Acionario",
		"Dia_Encerramento_Exercicio_Social",
		"Mes_Encerramento_Exercicio_Social",
		"Data_Alteracao_Exercicio_Social",
		"Pagina_Web",
	),
	("CNPJ_Companhia",),
)

FCA_CIA_ABERTA_PAIS_ESTRANGEIRO_NEGOCIACAO = FileContract(
	"FCA CIA_ABERTA — países estrangeiros de negociação",
	"fca_cia_aberta_pais_estrangeiro_negociacao",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Empresarial",
		"Pais",
		"Data_Admissao_Negociacao",
	),
	("CNPJ_Companhia",),
)

FCA_CIA_ABERTA_VALOR_MOBILIARIO = FileContract(
	"FCA CIA_ABERTA — valores mobiliários",
	"fca_cia_aberta_valor_mobiliario",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Empresarial",
		"Valor_Mobiliario",
		"Sigla_Classe_Acao_Preferencial",
		"Classe_Acao_Preferencial",
		"Codigo_Negociacao",
		"Composicao_BDR_Unit",
		"Mercado",
		"Sigla_Entidade_Administradora",
		"Entidade_Administradora",
		"Data_Inicio_Negociacao",
		"Data_Fim_Negociacao",
		"Segmento",
		"Data_Inicio_Listagem",
		"Data_Fim_Listagem",
	),
	("CNPJ_Companhia",),
)
