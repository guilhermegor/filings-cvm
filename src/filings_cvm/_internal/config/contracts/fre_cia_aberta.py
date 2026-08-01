"""Data contracts for the CVM open-data *FRE CIA_ABERTA* CSVs (ingestion) — groups 1–3 of 4.

`fre_cia_aberta_AAAA.zip` (dataset `CIA_ABERTA/DOC/FRE`, *Formulário de Referência*) is the largest
dataset in this portal: **36 members, ~131k rows**. It is implemented in four themed slices; this
module holds the first three — the **index** plus the **capital-structure** tables, the
**administração/pessoas** tables (every CPF-bearing member of the dataset), and the
**diversidade** tables. The remaining group (remuneração) appends its contracts here.

⚠️ **The diversidade members are AGGREGATE COUNTS, not sensitive personal data.** Names like
`administrador_declaracao_raca` / `*_declaracao_genero` / `*_PCD` / `*_faixa_etaria` read as
individual-level protected attributes; the columns are `Quantidade_Preto`, `Quantidade_Feminino`,
`Quantidade_PCD` — **totals per company and organ/position**, with no identifiable individual. This
was misclassified once from the member *name* alone; reading the columns disproved it. The real
personal data of FRE sits in the administração/pessoas members above.

⚠️ **Eleven diversidade members, five colliding column counts, and no two headers alike.**
`empregado_local_*` and `empregado_posicao_*` differ only in their grouping column (`Local` vs
`Posicao`), and `administrador_PCD` and `empregado_PCD` both have 10 columns while sharing only
six. Every contract is generated from **its own** header; copying a sibling would ship a wrong
column list that only the pinned fixture can catch.

Every column list is **generated from the real 2025 headers**, not transcribed, and pinned to
`tests/fixtures/fre_cia_aberta/` verbatim.

⚠️ **The index uses a different naming convention from its own satellites** — `CNPJ_CIA` /
`DT_REFER` / `DT_RECEB` / `DENOM_CIA`, the `cad_cia_aberta.csv` style — while every satellite uses
`CNPJ_Companhia` / `Data_Referencia`. FCA does the same; CGVN does **not**. There is no rule to
infer across `DOC` datasets, only per-dataset measurement.

⚠️ **FRE uses six different CNPJ column names across its 36 members** (`CNPJ`, `CNPJ_Auditor`,
`CNPJ_CIA`, `CNPJ_Companhia`, `CNPJ_Emissor`, `CNPJ_Emissor_Pessoa_Relacionada`), so each member
declares its own rather than inheriting a shared assumption.

⚠️ **A CNPJ column is one that holds only CNPJ — the name is not the test.** Three measured cases
in this dataset make the point, and each was resolved by counting the real values, not by reading
the header:

- `auditor.CNPJ_Auditor` holds **bare 14-digit** values (`49928567000111`) while
  `auditor.CNPJ_Companhia` in the *same row* is masked (`00.000.000/0001-91`). Both are declared —
  the validator normalises punctuation — but the mask style is **not** uniform within a member.
- `relacao_subordinacao.Documento_Pessoa_Relacionada` carries **CNPJ and CPF together** (8.462
  CNPJ + 34 CPF in 2025, matching its own `Tipo_Pessoa_Relacionada` PJ/PF flag) despite having
  neither word in its name, so it is **excluded**.
- `posicao_acionaria`'s three `CPF_CNPJ_*` columns are mixed by definition and are **excluded**;
  so is every `CPF*` column, which additionally carries personal data.

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

# --- Group 2 of 4: administração/pessoas — every CPF-bearing member of the dataset. ---
# No `CPF*` column is declared as a CNPJ column: they hold personal data, and several are mixed
# CPF/CNPJ by design, so a year whose values happened to be all-CNPJ would silently set the
# expectation that the next year breaks.

FRE_CIA_ABERTA_AUDITOR = FileContract(
	"FRE CIA_ABERTA — auditores independentes",
	"fre_cia_aberta_auditor",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"ID_Auditor",
		"Auditor",
		"CPF_Auditor",
		"CNPJ_Auditor",
		"Codigo_CVM_Auditor",
		"Tipo_Origem_Auditor",
		"Data_Inicio_Contratacao",
		"Data_Fim_Contratacao",
		"Data_Inicio_Prestacao_Servico",
		"Servico_Contratado",
		"Remuneracao_Auditor",
		"Justificativa_Substituicao",
		"Razao_Apresentada",
	),
	("CNPJ_Companhia", "CNPJ_Auditor"),
)

FRE_CIA_ABERTA_ADMINISTRADOR_MEMBRO_CONSELHO_FISCAL = FileContract(
	"FRE CIA_ABERTA — administradores e membros do conselho fiscal",
	"fre_cia_aberta_administrador_membro_conselho_fiscal",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"Orgao_Administracao",
		"Nome",
		"CPF",
		"Profissao",
		"Cargo_Eletivo_Ocupado",
		"Complemento_Cargo_Eletivo_Ocupado",
		"Data_Eleicao",
		"Data_Posse",
		"Data_Inicio_Primeiro_Mandato",
		"Prazo_Mandato",
		"Eleito_Controlador",
		"Outro_Cargo_Funcao",
		"Experiencia_Profissional",
		"Data_Nascimento",
		"Numero_Mandatos_Consecutivos",
		"Percentual_Participacao_Reunioes",
	),
	("CNPJ_Companhia",),
)

FRE_CIA_ABERTA_MEMBRO_COMITE = FileContract(
	"FRE CIA_ABERTA — membros de comitês",
	"fre_cia_aberta_membro_comite",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"Nome",
		"CPF",
		"Profissao",
		"Tipo_Comite",
		"Descricao_Outros_Comites",
		"Cargo_Ocupado",
		"Descricao_Outro_Cargo_Ocupado",
		"Data_Eleicao",
		"Data_Posse",
		"Data_Inicio_Primeiro_Mandato",
		"Prazo_Mandato",
		"Outro_Cargo_Funcao",
		"Experiencia_Profissional",
		"Data_Nascimento",
		"Numero_Mandatos_Consecutivos",
		"Percentual_Participacao_Reunioes",
	),
	("CNPJ_Companhia",),
)

FRE_CIA_ABERTA_RELACAO_FAMILIAR = FileContract(
	"FRE CIA_ABERTA — relações familiares",
	"fre_cia_aberta_relacao_familiar",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"Nome_Administrador",
		"CPF_Administrador",
		"Nome_Emissor",
		"CNPJ_Emissor",
		"Cargo_Administrador",
		"Nome_Pessoa_Relacionada",
		"CPF_Pessoa_Relacionada",
		"Nome_Emissor_Pessoa_Relacionada",
		"CNPJ_Emissor_Pessoa_Relacionada",
		"Cargo_Pessoa_Relacionada",
		"Tipo_Parentesco",
		"Observacao",
	),
	("CNPJ_Companhia", "CNPJ_Emissor", "CNPJ_Emissor_Pessoa_Relacionada"),
)

FRE_CIA_ABERTA_RELACAO_SUBORDINACAO = FileContract(
	"FRE CIA_ABERTA — relações de subordinação",
	"fre_cia_aberta_relacao_subordinacao",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"Data_Inicio_Exercicio_Social",
		"Data_Fim_Exercicio_Social",
		"Nome_Administrador",
		"CPF_Administrador",
		"Cargo_Administrador",
		"Nome_Pessoa_Relacionada",
		"Tipo_Pessoa_Relacionada",
		"Documento_Pessoa_Relacionada",
		"Cargo_Pessoa_Relacionada",
		"Categoria_Pessoa_Relacionada",
		"Tipo_Relacao",
		"Observacao",
	),
	("CNPJ_Companhia",),
)

FRE_CIA_ABERTA_POSICAO_ACIONARIA = FileContract(
	"FRE CIA_ABERTA — posição acionária",
	"fre_cia_aberta_posicao_acionaria",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"ID_Acionista",
		"Acionista",
		"Tipo_Pessoa_Acionista",
		"CPF_CNPJ_Acionista",
		"ID_Acionista_Relacionado",
		"Acionista_Relacionado",
		"Tipo_Pessoa_Acionista_Relacionado",
		"CPF_CNPJ_Acionista_Relacionado",
		"Quantidade_Acao_Ordinaria_Circulacao",
		"Percentual_Acao_Ordinaria_Circulacao",
		"Quantidade_Acao_Preferencial_Circulacao",
		"Percentual_Acao_Preferencial_Circulacao",
		"Quantidade_Total_Acoes_Circulacao",
		"Percentual_Total_Acoes_Circulacao",
		"Nacionalidade",
		"Sigla_UF",
		"Residente_Exterior",
		"Representante_Legal",
		"Tipo_Pessoa_Representante_Legal",
		"CPF_CNPJ_Representante_legal",
		"Data_Composicao_Capital_Social",
		"Data_Ultima_Alteracao",
		"Acionista_Controlador",
		"Participante_Acordo_Acionistas",
	),
	("CNPJ_Companhia",),
)

FRE_CIA_ABERTA_POSICAO_ACIONARIA_CLASSE_ACAO = FileContract(
	"FRE CIA_ABERTA — posição acionária por classe de ação",
	"fre_cia_aberta_posicao_acionaria_classe_acao",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"ID_Acionista",
		"Tipo_Classe_Acao_Preferencial",
		"Quantidade_Acoes",
		"Percentual_Acoes",
	),
	("CNPJ_Companhia",),
)
FRE_CIA_ABERTA_ADMINISTRADOR_PCD = FileContract(
	"FRE CIA_ABERTA — administradores PCD",
	"fre_cia_aberta_administrador_PCD",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"Orgao_Administracao",
		"Quantidade_PCD",
		"Quantidade_Nao_PCD",
		"Quantidade_Sem_Resposta",
		"Nao_Aplicavel",
	),
	("CNPJ_Companhia",),
)

FRE_CIA_ABERTA_ADMINISTRADOR_DECLARACAO_GENERO = FileContract(
	"FRE CIA_ABERTA — gênero declarado (administradores)",
	"fre_cia_aberta_administrador_declaracao_genero",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"Orgao_Administracao",
		"Quantidade_Feminino",
		"Quantidade_Masculino",
		"Quantidade_Nao_Binario",
		"Quantidade_Outros",
		"Quantidade_Sem_Resposta",
		"Nao_Aplicavel",
	),
	("CNPJ_Companhia",),
)

FRE_CIA_ABERTA_ADMINISTRADOR_DECLARACAO_RACA = FileContract(
	"FRE CIA_ABERTA — raça declarada (administradores)",
	"fre_cia_aberta_administrador_declaracao_raca",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"Orgao_Administracao",
		"Quantidade_Amarelo",
		"Quantidade_Branco",
		"Quantidade_Preto",
		"Quantidade_Pardo",
		"Quantidade_Indigena",
		"Quantidade_Outros",
		"Quantidade_Sem_Resposta",
		"Nao_Aplicavel",
	),
	("CNPJ_Companhia",),
)

FRE_CIA_ABERTA_EMPREGADO_PCD = FileContract(
	"FRE CIA_ABERTA — empregados PCD",
	"fre_cia_aberta_empregado_PCD",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"Codigo_Posicao",
		"Posicao",
		"Quantidade_PCD",
		"Quantidade_Nao_PCD",
		"Quantidade_Sem_Resposta",
	),
	("CNPJ_Companhia",),
)

FRE_CIA_ABERTA_EMPREGADO_LOCAL_DECLARACAO_GENERO = FileContract(
	"FRE CIA_ABERTA — gênero declarado (empregados por local)",
	"fre_cia_aberta_empregado_local_declaracao_genero",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"Local",
		"Quantidade_Feminino",
		"Quantidade_Masculino",
		"Quantidade_Nao_Binario",
		"Quantidade_Outros",
		"Quantidade_Sem_Resposta",
	),
	("CNPJ_Companhia",),
)

FRE_CIA_ABERTA_EMPREGADO_LOCAL_DECLARACAO_RACA = FileContract(
	"FRE CIA_ABERTA — raça declarada (empregados por local)",
	"fre_cia_aberta_empregado_local_declaracao_raca",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"Local",
		"Quantidade_Amarelo",
		"Quantidade_Branco",
		"Quantidade_Preto",
		"Quantidade_Pardo",
		"Quantidade_Indigena",
		"Quantidade_Outros",
		"Quantidade_Sem_Resposta",
	),
	("CNPJ_Companhia",),
)

FRE_CIA_ABERTA_EMPREGADO_LOCAL_FAIXA_ETARIA = FileContract(
	"FRE CIA_ABERTA — faixa etária (empregados por local)",
	"fre_cia_aberta_empregado_local_faixa_etaria",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"Local",
		"Quantidade_Ate30Anos",
		"Quantidade_30a50Anos",
		"Quantidade_Acima50Anos",
	),
	("CNPJ_Companhia",),
)

FRE_CIA_ABERTA_EMPREGADO_POSICAO_DECLARACAO_GENERO = FileContract(
	"FRE CIA_ABERTA — gênero declarado (empregados por posição)",
	"fre_cia_aberta_empregado_posicao_declaracao_genero",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"Posicao",
		"Quantidade_Feminino",
		"Quantidade_Masculino",
		"Quantidade_Nao_Binario",
		"Quantidade_Outros",
		"Quantidade_Sem_Resposta",
	),
	("CNPJ_Companhia",),
)

FRE_CIA_ABERTA_EMPREGADO_POSICAO_DECLARACAO_RACA = FileContract(
	"FRE CIA_ABERTA — raça declarada (empregados por posição)",
	"fre_cia_aberta_empregado_posicao_declaracao_raca",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"Posicao",
		"Quantidade_Amarelo",
		"Quantidade_Branco",
		"Quantidade_Preto",
		"Quantidade_Pardo",
		"Quantidade_Indigena",
		"Quantidade_Outros",
		"Quantidade_Sem_Resposta",
	),
	("CNPJ_Companhia",),
)

FRE_CIA_ABERTA_EMPREGADO_POSICAO_FAIXA_ETARIA = FileContract(
	"FRE CIA_ABERTA — faixa etária (empregados por posição)",
	"fre_cia_aberta_empregado_posicao_faixa_etaria",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"Posicao",
		"Quantidade_Ate30Anos",
		"Quantidade_30a50Anos",
		"Quantidade_Acima50Anos",
	),
	("CNPJ_Companhia",),
)

FRE_CIA_ABERTA_EMPREGADO_POSICAO_LOCAL = FileContract(
	"FRE CIA_ABERTA — empregados por posição e local",
	"fre_cia_aberta_empregado_posicao_local",
	(
		"CNPJ_Companhia",
		"Data_Referencia",
		"Versao",
		"ID_Documento",
		"Nome_Companhia",
		"Posicao",
		"Quantidade_Norte",
		"Quantidade_Nordeste",
		"Quantidade_Centro_Oeste",
		"Quantidade_Sudeste",
		"Quantidade_Sul",
		"Quantidade_Exterior",
	),
	("CNPJ_Companhia",),
)
