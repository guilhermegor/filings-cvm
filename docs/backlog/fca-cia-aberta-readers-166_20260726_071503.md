# Work ledger — #166 CIA_ABERTA/DOC/FCA readers (10 membros)

Branch `feat/166-fca-cia-aberta-readers`. Fecha **#166**. **Com release** (`feat`, diff em `src/`)
→ PATCH. **3ª das 7 fatias `DOC`** (agora 3/7). O maior salto de forma do sub-root.

## Forma (medida)

10 membros: índice (9 cols) + 9 tabelas de detalhe — auditor 15, canal_divulgacao 7,
departamento_acionistas 23, dri 26, endereco 21, escriturador 24, geral 26,
pais_estrangeiro_negociacao 7, valor_mobiliario 18. Base privada `_base_fca_reader.py` (molde
VLMO/`_base_inf_mensal_fii_reader`). Contracts **gerados dos 10 headers** e pinados a fixtures
verbatim **header-only** (há CPF).

## ⚠️ Armadilha 1 — o índice usa OUTRA convenção de nomes que os próprios satélites

| | índice | 9 satélites |
|---|---|---|
| CNPJ | `CNPJ_CIA` | `CNPJ_Companhia` |
| data ref. | `DT_REFER` | `Data_Referencia` |
| denominação | `DENOM_CIA` | `Nome_Empresarial` |
| id doc | `ID_DOC` | `ID_Documento` |
| versão | `VERSAO` | `Versao` |

Maiúsculas abreviadas (estilo `cad_cia_aberta.csv`) contra CamelCase por extenso. **Gerar os 10 de
um molde único quebraria o índice em silêncio.** Anti-cópia pinada **nas duas direções** (o índice
não tem os nomes dos satélites; nenhum satélite tem os do índice). **Controle negativo:** renomear
`DT_REFER`→`Data_Referencia` no contract falha **2** testes (o oráculo do header e o anti-cópia).

## ⚠️ Armadilha 2 — `departamento_acionistas` é HEADER-ONLY (0 linhas em 2025)

`tuple_cnpj_cols` **tem de ser `()`**. **Provado por mutação:** acrescentando `("CNPJ_Companhia",)`,
a leitura do membro vazio levanta
`Column 'CNPJ_Companhia' … holds no valid CNPJ (unexpected data type)`.
É a classe de falha da lição `value-presence-contract-tolerates-empty-artifact` (CRI) — **desta vez
pega no grounding, antes de escrever**, não num live-verify depois do merge.

## ⚠️ Armadilha 3 — PRIMEIROS CPF DO ROOT (LGPD)

| coluna | membro | 2025 |
|---|---|---|
| `CPF_Responsavel` | `dri` | **1.003 CPF + 4 CNPJ** (mista) |
| `CPF_Responsavel_Tecnico` | `auditor` | 49 CPF, 1.020 em branco |
| `CPF_CNPJ_Auditor` | `auditor` | 1.069 CNPJ válidos, mas **misto por definição** |

Todos texto exato, **nenhum** em `tuple_cnpj_cols` (um CPF não satisfaz o check; declarar
`CPF_CNPJ_Auditor` quebraria num ano com CPF — precedente `cedente_devedor.CNPJ`). **Fixtures
header-only** por causa disso. `escriturador` é o único com **2** CNPJ cols reais
(`CNPJ_Companhia` + `CNPJ_Escriturador`, ambas 100% válidas) e as duas são declaradas.

## ⚠️ A META é `fca_cia_aberta.zip` — SEM o prefixo `meta_`

O caso mais forte do portal para "URL constante por dataset, jamais derivada":

| candidato | resultado |
|---|---|
| `meta_fca_cia_aberta.txt` | **404** |
| `meta_fca_cia_aberta.zip` | **404** |
| **`fca_cia_aberta.zip`** | **200**, 10 membros |

E o vizinho `CIA_ABERTA/CAD` **serve** `meta_cad_cia_aberta.txt` normalmente — o prefixo **não é
política do portal**, varia por dataset. (Este ponto surgiu de uma pergunta do user apontando a URL
do CAD; medi as 4 e a tabela resolveu.) Os 10 contadores de campo da META (9/15/7/23/26/21/24/26/
7/18) batem exatamente com os headers reais.

## Feito

- [x] 10 readers + base privada + `MetaFcaCiaAbertaReader` (**40º**).
- [x] 10 contracts gerados dos headers + 10 fixtures verbatim header-only.
- [x] Registrado nas 5 camadas de `__init__` (+ contracts) e no `_META_MEMBERS` do drift (10 membros).
  **203 nomes públicos, 197 readers, 40 Meta.**
- [x] Docs: página nova + nav + `api.md` (seção com a tabela dos 10 + Meta 40) + `meta.md` (3
  contagens + linha marcando o "sem prefixo") + **`CLAUDE.md` (catálogo, árvore e contagem META
  39→40, no mesmo commit — #161)** + `test_meta_readers.py` 39→40.
- [x] 59 testes novos (56 pass + 3 skips deliberados: o membro vazio nos testes que exigem linha).

## Verificação

- [x] **Oráculo anti-tautologia dos 10 contracts** contra os headers verbatim, + as 10 larguras
  pinadas (`[9,15,7,23,26,21,24,26,7,18]`).
- [x] **Controle negativo do membro vazio** (o mais valioso): com CNPJ col, a leitura vazia
  **levanta**; sem, devolve 0 linhas com todas as colunas. A decisão é load-bearing, não estética.
- [x] **Controle negativo do anti-cópia:** o rename no índice falha 2 testes.
- [x] Blanks de data → `NaT` em **todos** os membros com >1 date col (o `geral` tem 9).
- [x] ruff + format limpos, mypy **372** arquivos, `check_dtypes`/`typing`/`provenance`/`docstrings`
  OK, suíte completa, mkdocs --strict, codespell.
- [x] ⚠️ **O gerador produziu 9 linhas >99 chars** (docstrings de classe com labels longos, e prosa).
  Corrigido encurtando o template do summary e reembrulhando; **um dos meus `str.replace` de rewrap
  quebrou um comentário em 3 linhas** e foi consertado à mão. Gerar código economiza digitação, não
  revisão.

## Aberto / próximo

- [ ] PR (`Closes #166`) → aprovação → merge → **release PATCH**.
- [ ] `DOC` restante (4): **CGVN** (4,01 MiB) → **FRE** (8,10) → **DFP** (12,12) → **ITR** (30,14),
  depois `EVENTOS/RECOMPRA_ACOES`. Nenhum tem contagem de membros medida ainda — **grounding próprio
  para cada**, e **conferir a URL da META no portal** (já vimos `.txt` solto, `.zip`, `_txt` infixo e
  agora **sem prefixo**).
