## cgvn-cia-aberta-readers-170_20260726_082941

# Work ledger — #170 CIA_ABERTA/DOC/CGVN readers (índice + práticas)

Branch `feat/170-cgvn-cia-aberta-readers`. Fecha **#170**. **Com release** (`feat`) → PATCH.
**4ª das 7 fatias `DOC`** (agora 4/7).

## Forma (medida) — molde do VLMO

| membro | reader | cols | linhas |
|---|---|---|---|
| `cgvn_cia_aberta.csv` | `CgvnCiaAbertaReader` | 12 | 382 |
| `cgvn_cia_aberta_praticas.csv` | `CgvnCiaAbertaPraticasReader` | 11 | **19.980** |

⚠️ **Os 4,01 MiB do ZIP são UM membro de conteúdo grande, não muitos membros** — a expectativa que eu
tinha pelo tamanho estava errada; a `Explicacao` chega a ~6.000 chars. **Nenhum membro header-only**
(o row-count por membro foi impresso no grounding, conforme a lição emendada no #166).

## ⚠️ Achado principal: o FCA era a EXCEÇÃO, não a regra

O índice do FCA usa `CNPJ_CIA`/`DT_REFER`/`DENOM_CIA`. **O do CGVN usa CamelCase**
(`CNPJ_Companhia`/`Data_Referencia`/`Nome_Empresarial`). Se eu tivesse generalizado a "regra do
índice" a partir do FCA — a fatia imediatamente anterior — este dataset sairia errado. **Anti-
generalização pinada** por um teste que compara os **dois** contracts diretamente, não só afirma o
deste.

## ⚠️ `Codigo_CVM` com zero à esquerda — o texto é load-bearing aqui

Valor real: **`001023`**. No IPE não havia zeros à esquerda, então tipar `Codigo_CVM` como texto era
**apenas convenção**; aqui é correção. **Provado por mutação:** com `int64`, a asserção falha com
`np.int64(1023) == '001023'`. `ID_Item` é hierárquico (`1.1.1`) e também fica texto.

## Outros achados

- `CNPJ_Companhia` **100% válido** nos dois membros (382 e 19.980), sem placeholder.
- **Date cols:** índice **4** (inclui `Data_Inicio_Exercicio_Social`/`Data_Fim_Exercicio_Social`),
  `praticas` **1**. Todas 100% ISO.
- `Explicacao` (11.935/19.980) e `Pratica_Recomendada` (até 1.262 chars) são texto livre longo;
  `QUOTE_NONE` dá **larguras uniformes** (medido) → nenhum `;` embutido.
- ⚠️ `Link_Download` é **`http://…/ENETCONSULTA/…`**, não o `https://…/ENET/…` do IPE/VLMO. Devolvido
  **como publicado** — o reader não normaliza esquema nem segue o link. Pinado por teste.
- ⚠️ **META = `meta_cgvn_cia_aberta.zip`** (forma padrão). As outras 3 dão **404** — inclusive
  `cgvn_cia_aberta.zip` **sem prefixo**, que é a forma **correta do FCA**. 5 datasets, 5 medições.

## Feito

- [x] 2 readers + base privada + `MetaCgvnCiaAbertaReader` (**41º**). **206 nomes públicos, 200
  readers, 41 Meta** (medido: 41 = 16 `.txt` + 25 `.zip`).
- [x] Contracts gerados dos headers + 2 fixtures verbatim; drift `_META_MEMBERS` atualizado.
- [x] Docs: página nova + nav + `api.md` (seção + Meta 41) + `meta.md` (3 contagens + linha) +
  **`CLAUDE.md` (catálogo, árvore e contagem META 40→41, mesmo commit — #161)** +
  `test_meta_readers.py` 40→41.
- [x] 17 testes novos.

## Verificação

- [x] **Oráculo anti-tautologia** dos 2 contracts contra os headers verbatim.
- [x] **Controle negativo do zero à esquerda:** `int64` → falha com `1023`; texto → passa.
- [x] **Controle negativo do anti-generalização:** renomear `Nome_Empresarial`→`DENOM_CIA` falha
  **2** testes (o oráculo e o comparativo CGVN×FCA).
- [x] ruff + format, mypy **378**, 4 check_*, suíte completa, mkdocs --strict, codespell.
- [x] ⚠️ Reincidência: rewrap de docstring por `str.replace` **empurra o overflow para a linha
  seguinte** — 3 rodadas de E501 nesta fatia. Reembrulhar o **parágrafo inteiro** de uma vez.

## Aberto / próximo

- [ ] PR (`Closes #170`) → aprovação → merge → **release PATCH**.
- [ ] `DOC` restante (3): **FRE** (8,10 MiB) → **DFP** (12,12) → **ITR** (30,14), depois
  `EVENTOS/RECOMPRA_ACOES`. **Nenhum tem contagem de membros medida** — imprimir **cols E linhas**
  por membro, e **medir a URL da META** (já vimos 5 resultados diferentes em 5 datasets).

## dfp-cia-aberta-readers-196_20260802_201820

# DFP CIA_ABERTA — 19 membros, ~1,17M linhas — #196

Branch: `feat/196-dfp-cia-aberta-readers` · Issue: #196 · Leva o sub-root `CIA_ABERTA/DOC` a
**6 de 7** datasets (só falta o ITR).

## Feito

- [x] Grounding contra os bytes reais (2025) — membros, cols **e** linhas, ragged, classificação de
      **toda** coluna por valor, e a **grafia da META medida** (4 candidatas).
- [x] 19 fixtures header-only verbatim + 19 contracts **gerados dos headers**.
- [x] 19 readers sobre a base privada `_base_dfp_reader.py` (molde do `_base_fre_reader.py`) +
      `MetaDfpCiaAbertaReader` (44º).
- [x] Registro nos **3** `__init__` da cadeia + os **2** contracts em `contracts/__init__.py`;
      `_META_MEMBERS` do drift estendido.
- [x] **Contagens RE-MEDIDAS, não incrementadas:** **259 readers** (era 239), **44 Meta readers =
      17 `.txt` + 27 `.zip`**, 22 roots.
- [x] 106 testes novos no arquivo do DFP; suíte **2597** unit + 4 integration.
- [x] Docs: página nova `docs/ingestion/dfp_cia_aberta.md` + `nav`, seção em `docs/api.md`,
      linha e contagens em `docs/ingestion/meta.md`, catálogo + layout + contagens no `CLAUDE.md`.

## Medições (2025)

19 membros, 12,73 MB, **~1,17 milhão de linhas**, **nenhum ragged**. `_con` = consolidado,
`_ind` = individual.

| grupo | membros | cols |
|---|---|---|
| índice | 1 | 9 |
| balanço (`BPA`/`BPP` × `con`/`ind`) | 4 | 14 |
| fluxo (`DFC_MD`/`DFC_MI`/`DRA`/`DRE`/`DVA` × `con`/`ind`) | 10 | 15 |
| mutações do PL (`DMPL` × `con`/`ind`) | 2 | 16 |
| composição do capital | 1 | 10 |
| parecer | 1 | 8 |

## ⚠️⚠️ O achado 1 — este dataset INVERTE a armadilha de todos os anteriores

Em CRA, CRI, FCA e FRE a lição era *"membros de mesma largura têm colunas diferentes — nunca copie o
irmão"*. **Aqui é o oposto:** os 16 membros de demonstração colapsam em **3** listas, e membros
diferentes são **genuinamente idênticos**. 19 membros → **6** listas distintas.

A diferença 14 × 15 é **exatamente `DT_INI_EXERC`**: balanço é retrato num instante, fluxo cobre
período. `DMPL` soma `COLUNA_DF`.

**Medido contra as fixtures**, não presumido — e o teste afirma o agrupamento, não só a contagem.
**Presumir "são iguais" e presumir "são diferentes" é o mesmo erro: não medir.** Precedente: no CRI,
2 das 7 seções eram de fato idênticas ao CRA, e a coincidência era da fonte.

## ⚠️⚠️ O achado 2 — o BURACO que as listas idênticas abrem (e a defesa que faltava)

Com 10 membros de lista **idêntica**, um reader apontado ao membro **errado** — o swap `con`↔`ind`
que a nomenclatura convida — devolve um frame **perfeitamente válido**: colunas conferem, tipos
conferem, contrato passa. **Nada fica vermelho.**

**Provado por mutação:** trocar o `_MEMBER_STEM` de `DRE_con` pelo de `DRE_ind` passava na suíte
**INTEIRA**. E o swap `BPA_con`→`BPA_ind` quebrava **1** teste — mas **incidentalmente**: aquele
teste constrói um `BPA_con` deliberadamente quebrado esperando `ContractError`, e o reader passou a
ler o irmão intacto. Não era defesa, era acidente.

**Defesa acrescentada:** cada membro sintético dos testes **se identifica** numa coluna que todos
têm (`DENOM_CIA`), e um teste parametrizado exige que cada reader leia **o seu**. Re-rodadas as duas
mutações: `BPA_con`→`BPA_ind` passa a falhar **2**, e `DRE_con`→`DRE_ind` — que antes passava por
completo — falha **1**, o teste novo.

⚠️ **Foi a contagem baixa do mutante que revelou isso**, exatamente como a lição
`a-negative-control-needs-a-verified-restore` prevê: uma falha só não é "defesa suficiente", é um
número a investigar.

## ⚠️⚠️ O achado 3 — a escala do valor está em OUTRA coluna

`VL_CONTA` chega com **10 casas decimais** (`2398719197.0000000000`) → **texto exato** (um `float64`
apaga os dígitos, como já medido no VLMO). Mas o número **sozinho não significa nada**:
`ESCALA_MOEDA` vale `MIL` ou `UNIDADE`, então **somar `VL_CONTA` sem ler `ESCALA_MOEDA` erra por
1000×**. Os readers **não reescalam** (ficam thin; reescalar destruiria o valor publicado) — está
documentado no docstring, na página e no `api.md`, com o exemplo de conversão a jusante.

## Outras armadilhas honradas

- `CD_CVM` vem `001023`, **zero à esquerda** — texto load-bearing (precedente CGVN).
- `ORDEM_EXERC` (`ÚLTIMO`/`PENÚLTIMO`) **duplica cada conta** → **nenhuma chave única**.
- **Todos os 19 membros usam `CNPJ_CIA`/`DT_REFER`**, inclusive os satélites — **diferente** do FCA
  e do FRE. O teste usa o FRE como **contra-exemplo vivo**.
- `COLUNA_DF` (DMPL) e `TP_RELAT_AUD` (parecer) parcialmente vazias.
- META = `meta_dfp_cia_aberta_txt.zip` (**infixo `_txt`**); as outras 3 dão **404**, inclusive a
  sem-prefixo que é a **correta do FCA**. A previsão do survey acertou pela 1ª vez — o que **não**
  torna o nome derivável.

## Controles negativos (todos vermelhos, restore por cópia de snapshot)

Baseline **87 → 106** passed, re-medido entre as mutações.

- [x] Dar `DT_INI_EXERC` ao balanço (a diferença de 1 coluna entre as 2 listas grandes) → **3**.
- [x] Declarar `CD_CVM` como coluna de CNPJ (classificar pelo nome) → **7**.
- [x] `BPA_con` lendo o membro do irmão → **1 antes** (incidental) / **2 depois** da defesa nova.
- [x] `DRE_con` lendo o membro do irmão → **0 antes** (!) / **1 depois**.

## Aberto / próximo

- [ ] **Release PATCH** ao mergear (`feat`, `src/` muda).
- [ ] **ITR** (`itr_cia_aberta_AAAA.zip`, 30,14 MiB) — **fecha o `DOC` (7/7)**; contagem de membros
      **a medir**, jamais presumida do DFP.
- [ ] Depois: `EVENTOS/RECOMPRA_ACOES`.
- [ ] #192 (testes dos 3 `bin/check_*` sem cobertura) segue em Ready.

## fca-cia-aberta-readers-166_20260726_071503

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

## fre-cia-aberta-readers-1-172_20260729_115854

# Work ledger — #172 CIA_ABERTA/DOC/FRE readers, fatia 1/4 (índice + capital)

Branch `feat/172-fre-cia-aberta-readers-1`. Fecha **#172**. **Com release** (`feat`) → PATCH.
**5ª das 7 fatias `DOC`** (`DOC` em 5/7, FRE parcial).

## Por que 4 PRs (decisão do user)

⚠️ **O FRE é o maior dataset do portal: 36 membros, 131.105 linhas, 8,5 MB** — 3,6× o FCA, que já
tinha sido um PR de 40 arquivos. Levei a decisão ao user com os números medidos; ele escolheu
**dividir em 4 PRs temáticos** em vez de um único. Racional: cada um revisável e releasável sozinho,
e **os 6 membros com CPF ficam concentrados na fatia 2**, num diff que dá para escrutinar.

| fatia | tema | membros |
|---|---|---|
| **1 (esta)** | índice + estrutura de capital | **8** |
| 2 | administração/pessoas (**todos com CPF**) | 7 |
| 3 | diversidade (agregados) | 11 |
| 4 | remuneração + val. mobiliários + transações | 10 |

## Feito nesta fatia

- [x] 8 readers + base privada `_base_fre_reader.py` (molde VLMO/FCA) + `MetaFreCiaAbertaReader`
  (**42º**). **215 nomes públicos, 209 readers, 42 Meta** (medido: 42 = 16 `.txt` + 26 `.zip`).
- [x] 8 contracts **gerados dos headers** + 8 fixtures verbatim; `_META_MEMBERS` do drift com os 8
  (as fatias 2–4 estendem essa tupla).
- [x] Docs: página nova (com a tabela das 4 fatias) + nav + `api.md` + `meta.md` +
  **`CLAUDE.md` (catálogo, árvore, contagem META 41→42, mesmo commit — #161)** +
  `test_meta_readers.py` 41→42.
- [x] 40 testes novos.

## ⚠️ Achados

- **O índice usa `CNPJ_CIA`/`DT_REFER`/`DT_RECEB`** (maiúsculas), os satélites `CNPJ_Companhia`/
  `Data_Referencia`. **O FCA faz igual; o CGVN NÃO.** Convenção do índice por dataset: FCA ✓, CGVN ✗,
  FRE ✓ — **não há regra a inferir**. Pinado nas 2 direções **com o CGVN como contra-exemplo
  explícito** no teste.
- **SEIS nomes de coluna de CNPJ** nos 36 membros → cada contrato declara o seu.
- Todas as datas 100% ISO; `Data_Ultima_Assembleia` tem linhas vazias → `NaT` (pinado).
- `Valor_Capital`/`Quantidade_*`/`Percentual_*` = **texto exato** (#157).
- **Nenhum membro header-only e nenhum ragged** nos 36 (row-count por membro impresso no grounding).
- ⚠️ **META = `meta_fre_cia_aberta.zip`** (padrão; as outras 3 dão 404, inclusive a sem-prefixo que é
  a correta do FCA). **50 membros para 36 de dados**, com prefixo interno **misto** (ao menos um
  membro sem `meta_`). Honrado como publicado.

## ⚠️ Dois erros MEUS, ambos pegos por medição/gate

1. **Marquei os membros `*_declaracao_raca`/`*_declaracao_genero`/`*_PCD`/`*_faixa_etaria` como
   DADO PESSOAL SENSÍVEL — pelo NOME.** Ler as **colunas** desmentiu: são `Quantidade_Preto`,
   `Quantidade_Feminino`, `Quantidade_PCD` — **contagens agregadas** por companhia/órgão, sem
   indivíduo algum. O PII real está em **6 outros membros** com `CPF`/`Nome`, vários dos quais o
   nome não anunciava. **Lição `ground-invariants-not-just-schema-in-artifact` emendada:** um NOME é
   hipótese de semântica, nunca o achado — classificar por VALORES.
2. **Escrevi uma asserção FALSA:** `str(float("1984223115.42")) != "1984223115.42"`. O `repr` do
   Python faz round-trip **exato** desse valor — o teste falhou e estava certo. O float destrói a
   **escala** (zeros à direita) e precisão além de ~15 dígitos significativos, **não toda string
   decimal** (o caso do VLMO, `61961072.9999543100`, perde mesmo). Asserção removida; o docstring
   agora explica **por que** o texto garante fidelidade para *todo* valor, não só onde o estrago é
   visível.

## Verificação

- [x] **Oráculo anti-tautologia** dos 8 contracts + as 8 larguras pinadas
  (`[9,13,8,8,15,9,7,17]`).
- [x] ⚠️ **O gate de contagem de docs (#155/#161) PEGOU a deriva** — a suíte reprovou porque eu tinha
  adicionado o 42º Meta reader sem atualizar `meta.md`/`api.md`/`CLAUDE.md`. **O gate funcionou
  exatamente como projetado**, antes do commit.
- [x] ruff + format, mypy **390**, 4 check_*, **2100 unit**, 4 integration, mkdocs --strict,
  codespell.

## Aberto / próximo

- [x] PR (`Closes #172`) → aprovação → merge → **release PATCH** — PR #173 mergeado, **0.25.26**
  publicado.
- [x] **Fatia 2 do FRE** (7 membros, **todos os com CPF**): `auditor`, `administrador_membro_conselho_fiscal`,
  `membro_comite`, `relacao_familiar`, `relacao_subordinacao`, `posicao_acionaria` (**3** cols
  `CPF_CNPJ_*` mistas, 31.508 linhas), `posicao_acionaria_classe_acao`. **Fixtures header-only
  obrigatórias**; CPF **fora** de `tuple_cnpj_cols`. → **#179 / PR #180, 0.25.27**; ledger próprio em
  `fre-cia-aberta-readers-2-179_20260801_143000.md`.
  ⚠️ **Uma previsão desta fatia saiu errada e a medição corrigiu:** o plano supunha que só as colunas
  `CPF*` ficariam de fora de `tuple_cnpj_cols`. Medido: `auditor` tem **2** cols de CNPJ,
  `relacao_familiar` tem **3**, e `relacao_subordinacao.Documento_Pessoa_Relacionada` guarda CNPJ
  **e** CPF sem dizer nenhum dos dois no nome. **Coluna de CNPJ é a que só guarda CNPJ.**
- [ ] Depois fatias 3 e 4, então **DFP** (12,12 MiB) e **ITR** (30,14) e `EVENTOS/RECOMPRA_ACOES`.
  ⚠️ **#91 (slim top-level `__all__`) vem ANTES das fatias 3–4** — decisão do user (2026-08-01).

**Completed — mantido como registro.** A única linha aberta acima é o roteiro seguinte, não trabalho
desta fatia.

## fre-cia-aberta-readers-2-179_20260801_143000

# FRE CIA_ABERTA — fatia 2 de 4 (administração/pessoas, os 7 membros com CPF) — #179

Branch: `feat/179-fre-readers-2-4-administracao-pessoas` · Issue: #179 · Fatia anterior: #172 / PR #173

## Feito

- [x] Grounding contra os bytes reais de `fre_cia_aberta_2025.zip` (8,5 MB) — cols **e** linhas por
      membro, validade de CNPJ/CPF por coluna, presença de header-only, campos com aspas.
- [x] 7 fixtures **header-only** verbatim (ISO-8859-1) em `tests/fixtures/fre_cia_aberta/`.
- [x] 7 contracts **gerados dos headers pinados**, nunca transcritos.
- [x] 7 readers sobre a base privada `_base_fre_reader.py` (zero infraestrutura nova).
- [x] Registro nos 5 `__init__` + contracts `__init__`; **contagem exportada conferida** (222 nomes,
      216 readers, 42 Meta, 15 FRE readers = 15 FRE contracts).
- [x] Testes: 73 no arquivo do FRE (era 45).
- [x] **Controles negativos rodados** (3 mutações) — ver abaixo.
- [x] Docs: `docs/ingestion/fre_cia_aberta.md`, `docs/api.md`, `CLAUDE.md` (catálogo + Layout).

## Medições que contrariaram o plano da issue

O plano dizia "CPF fora de `tuple_cnpj_cols`, fixtures header-only" — isso valeu. Três coisas **não**
estavam no plano e só apareceram por medir:

- [x] **`auditor` tem 2 colunas de CNPJ**, não 1: `CNPJ_Auditor` (1.096/1.096 válidos) além do
      `CNPJ_Companhia`. E as duas **têm máscaras diferentes na mesma linha** — a da companhia é
      pontuada, a do auditor vem em dígitos crus (`49928567000111`).
- [x] **`relacao_familiar` tem 3 colunas de CNPJ** (`CNPJ_Emissor`, `CNPJ_Emissor_Pessoa_Relacionada`
      além da companhia). O plano só mencionava as 2 de CPF.
- [x] **`relacao_subordinacao.Documento_Pessoa_Relacionada` guarda CNPJ *e* CPF** (8.462 × 34) e o
      nome **não diz nem um nem outro**. Uma varredura que só olha colunas com "CNPJ"/"CPF" no nome
      passa direto por ela. Fica **fora** de `tuple_cnpj_cols`.

Consequência de método: a asserção da fatia 1 `todo satélite == ("CNPJ_Companhia",)` **deixou de ser
verdade** e foi substituída por um mapa medido por membro. Uma regra derivada de 8 membros não
sobreviveu ao 9º.

## Controles negativos (todos rodados, todos vermelhos antes do fix)

- [x] **Declarar `CPF_Auditor` como coluna de CNPJ** → 7 testes falham, incluindo `ContractError` em
      runtime (`holds no valid CNPJ`). Duas defesas independentes.
- [x] **Dar a `membro_comite` as colunas de `administrador_membro_conselho_fiscal`** (os dois têm
      **21 colunas**) → falha o header pinado **e** o teste anti-cópia. Sem o header pinado, o
      contrato errado passaria.
- [x] ⚠️ **Tirar `Data_Fim_Contratacao` de `_DATE_COLS` → PASSOU (73 verdes).** Meu teste usava
      `isna().all()`, e **pandas transforma branco em NA sob `dtype="str"` também** — a asserção era
      verdadeira nos dois mundos. Medido: `datetime64[ns]`/`NaT` × `string`/`<NA>`. Reescrito para
      asserir o **dtype**; a mutação passou a falhar. **Um teste sobre uma coluna 100% vazia não pode
      asserir vazio — só o tipo distingue.**

## Aberto / próximo

- [x] PR #180 (`Closes #179`) → CI 8/8 verde → merge `--squash --delete-branch` → cascade nativa
      completa (issue CLOSED, branch remota deletada, card Done).
- [ ] **#91** (slim top-level `__all__`) — acordado com o user para **depois deste PR**, antes das
      fatias 3–4, para não colidir. O `__all__` plano já está em **216 readers** (a issue foi escrita
      com 94). ⚠️ **É breaking pela decisão registrada na issue** (`from filings_cvm import XReader`
      para de funcionar → **0.26.0**, MINOR em 0.x); a própria issue pede para **reconfirmar no
      início do PR** a versão dura vs a branda (manter importável mas fora do `__all__`,
      não-breaking, PATCH).
- [ ] **Fatia 3 de 4** — diversidade, 11 membros (contagens **agregadas**, não PII).
- [ ] **Fatia 4 de 4** — remuneração + valores mobiliários + transações, 10 membros.
- [ ] Estender `_META_MEMBERS` do drift conforme as fatias 3–4 entrarem.

## Release

- [x] `src/` muda → releasou. PATCH sobre 0.25.26 → **0.25.27** (feat, pré-1.0).
      **Zero jobs não-success**, incluindo `Create GitHub Release` (o step que só existe no workflow
      de produção e nunca é ensaiado) e `deploy_docs`/mike. Tag `v0.25.27` sozinha, `isDraft=false`,
      wheel+sdist. **Fix do #102 provado 21ª vez** (`files:` conferido ANTES de despachar).
      Test PyPI install-verify na attempt-1, PyPI na attempt-2 (CDN lag, padrão esperado).
      O install-verify provou **comportamento** do wheel, não só símbolos: as 2/3 cols de CNPJ, as
      exclusões de CPF/documento misto, a grafia minúscula e `membro_comite != administrador`.

**Completed — mantido como registro.** As linhas abertas acima são o roteiro seguinte (#91 e as
fatias 3–4), não trabalho desta fatia.

## fre-cia-aberta-readers-3-183_20260801_190000

# FRE CIA_ABERTA — fatia 3 de 4 (diversidade, 11 membros agregados) — #183

Branch: `feat/183-fre-readers-3-4-diversidade` · Issue: #183 · Fatias anteriores: #172/#179

**Primeira fatia depois do #91** — a superfície pública agora é o portal root.

## Feito

- [x] Grounding contra os bytes reais de 2025 — cols **e** linhas por membro, ragged, header-only,
      e classificação de **toda** coluna por valor.
- [x] 11 fixtures header-only verbatim + 11 contracts **gerados dos headers**.
- [x] 11 readers gerados por template sobre `_base_fre_reader.py` (zero infraestrutura nova).
- [x] Registro e **contagem conferida**: 227 readers (era 216), 26 FRE readers = 26 FRE contracts.
- [x] Testes: 126 no arquivo do FRE (era 73); suíte **2296** (+53).
- [x] Docs: `docs/ingestion/fre_cia_aberta.md`, `docs/api.md`, `CLAUDE.md`.

## Medições

Nenhum header-only, nenhum ragged, **11 headers distintos**. Todos com 1 col de data
(`Data_Referencia`, 100% ISO) e 1 de CNPJ (`CNPJ_Companhia`, 100% válido).

⚠️ **5 pares de mesma largura e listas diferentes** — o risco central desta fatia:
9 (`local` × `posicao` faixa etária) · 10 (`administrador_PCD` × `empregado_PCD`) ·
11 (`local` × `posicao` gênero) · 12 (`administrador_declaracao_genero` × `empregado_posicao_local`) ·
13 (`local` × `posicao` raça). `administrador_PCD` e `empregado_PCD` compartilham **8** das 10 (divergem em 2 cada).

⚠️ `administrador_PCD.Quantidade_*` chega ~1/5 **vazia** — declaração ausente, **não** zero.

## ⚠️ Duas armadilhas de MÉTODO nesta fatia

**1. O scan por valor produz falso-positivo de CNPJ/CPF em coluna numérica.** A lição emendada no
#179 manda classificar **toda** coluna por valor, e foi o que fiz — mas o resultado acusou
`Quantidade_Branco: CNPJ=8/3117` e `ID_Documento: CNPJ=50/3495`. **Não é achado, é ruído:**
`unmask_cnpj` faz **zero-pad à esquerda** (a CVM publica CNPJ sem zeros), então `'157767'` vira
`'00000000157767'` e passa nos dígitos verificadores por coincidência (~1/70). É comportamento
**deliberado e documentado**, não bug — não abri issue.
→ **A regra correta é ler a TAXA, não a presença:** `CNPJ_Companhia` dá **100%**, as colunas de
contagem dão ~0,1–1,4%. Só a primeira é coluna de CNPJ.

**2. `cia_aberta` precisa de TRÊS `__init__`, não dois.** O `CLAUDE.md` que **eu** escrevi no #91
dizia "exatamente DOIS" — errado para um root aninhado: aqui a cadeia é `doc/fre/` → `doc/` →
`cia_aberta/`. O `ImportError` apareceu na hora; **a guidance estava errada, não o código**, e foi
corrigida no mesmo commit. Também acrescentei que o contract precisa entrar em
`contracts/__init__.py` — eu tinha esquecido, e **nada falhou**: o reader importa o contract do
módulo direto, então só a **contagem exportada** (15 em vez de 26) denunciou.

## Controles negativos (2 mutações, ambas vermelhas)

- [x] **Dar ao `empregado_posicao_faixa_etaria` a coluna de agrupamento do irmão `local`** → 3
      testes falham (header pinado + os 2 anti-cópia). É exatamente o erro que os 5 pares convidam.
- [x] **Declarar uma `Quantidade_*` como coluna de CNPJ** (o erro de classificar pelo nome) → 7
      testes falham, incluindo `ContractError` em runtime.

## Aberto / próximo

- [ ] **Release PATCH 0.26.1** (`feat`, pós-0.26.0 — `src/` muda).
- [ ] **Fatia 4 de 4** — remuneração + valores mobiliários + transações (10 membros) → fecha o FRE.
- [ ] Depois: **DFP** (12,12 MiB) e **ITR** (30,14) e `EVENTOS/RECOMPRA_ACOES`.

## fre-cia-aberta-readers-4-190_20260802_072803

# FRE CIA_ABERTA — fatia 4 de 4 (remuneração + val. mobiliários + transações) — #190

Branch: `feat/190-fre-cia-aberta-readers-4-remuneracao` · Issue: #190 · Fatias anteriores:
#172 / #179 / #183

**Fecha o FRE (36/36)** — o maior dataset do portal — e leva o sub-root `CIA_ABERTA/DOC` a 5 de 7.

## Feito

- [x] Grounding contra os bytes reais de 2025 — cols **e** linhas por membro, ragged, header-only,
      e classificação de **toda** coluna por valor, lendo a **taxa** (não a presença).
- [x] META consultada como **oráculo de tipo** para as colunas 100% vazias.
- [x] 10 fixtures header-only verbatim + 10 contracts **gerados dos headers**.
- [x] 10 readers sobre `_base_fre_reader.py` (zero infraestrutura nova).
- [x] Registro nos **3** `__init__` da cadeia + `contracts/__init__.py`; **contagem conferida**:
      **237 readers** (era 227), **36 FRE readers = 36 FRE contracts**, 22 roots.
- [x] `_META_MEMBERS` do drift estendido para os 36.
- [x] Testes: **179** no arquivo do FRE (era 126); suíte **2389** unit (+92) + 4 integration.
- [x] Docs: `docs/ingestion/fre_cia_aberta.md`, `docs/api.md`, `CLAUDE.md`.
- [x] ⚠️ **Bug de doc corrigido de passagem:** o exemplo de uso da página do FRE ainda importava
      `from filings_cvm import ...`, que **quebra desde o #91/0.26.0**. Quem copiasse pegaria
      `ImportError`.
- [x] **Legado resolvido a pedido do user:** os 4 scripts de `bin/` indentados com espaços
      (`check_backlog_ledger`, `check_docstrings`, `check_provenance`, `check_typing`) passaram a
      usar tabs, fechando a divergência de `ruff format --check` (ver seção abaixo).

## Medições (2025, bytes reais)

10/10 membros presentes, **nenhum ragged**, **nenhum header-only**, 10 headers distintos.

| membro | cols | linhas | date cols | CNPJ cols |
|---|---|---|---|---|
| `acao_entregue` | 14 | 1.304 | 3 | `CNPJ_Companhia` |
| `remuneracao_acao` | 14 | 1.565 | 3 | `CNPJ_Companhia` |
| `remuneracao_maxima_minima_media` | 14 | 3.307 | 3 | `CNPJ_Companhia` |
| `remuneracao_total_orgao` | 27 | 6.320 | 3 | `CNPJ_Companhia` |
| `remuneracao_variavel` | 18 | 3.851 | 3 | `CNPJ_Companhia` |
| `outro_valor_mobiliario` | 24 | 2.735 | 3 | `CNPJ_Companhia` |
| `titular_valor_mobiliario` | 9 | 163 | 1 | `CNPJ_Companhia` |
| `titulo_exterior` | 21 | 122 | 3 | `CNPJ_Companhia` |
| `participacao_sociedade` | 21 | 6.511 | 3 | `CNPJ_Companhia`, **`CNPJ`** |
| `transacao_parte_relacionada` | 22 | 11.238 | 2 | `CNPJ_Companhia` |

## ⚠️ Achados que contrariaram a previsão da issue

**1. `participacao_sociedade` tem DUAS colunas de CNPJ, e 792 das 6.511 são o placeholder
`00000000000000`.** Não são malformadas: são **subsidiárias no exterior sem CNPJ brasileiro**
(`AMERICANAS LUX`, `St. Marys Cement Inc.`, `LOUISE HOLDINGS LIMITED LTD`). 5.719 válidos, **zero
com dígito verificador quebrado**, nenhum branco. Mesma classe do placeholder
`00.000.000/0000-00` do IPE → devolvido **como publicado**, e a coluna fica em `tuple_cnpj_cols`
porque o check exige **ao menos um** válido. A previsão da issue era 1 coluna de CNPJ; **a terceira
fatia seguida em que a previsão erra para baixo**.

**2. `transacao_parte_relacionada.Documento_Parte_Relacionada` chega 100% VAZIA em 2025** — e
**fica fora** de `tuple_cnpj_cols` assim mesmo. A irmã `Tipo_Pessoa` tem domínio **`PF/PJ`** na
META: a coluna é **mista por definição**, exatamente o
`relacao_subordinacao.Documento_Pessoa_Relacionada` da fatia 2 (8.462 CNPJ × 34 CPF). Declarar
hoje passaria — e quebraria no primeiro ano com dado.

**3. Doze colunas de `participacao_sociedade` e três de `outro_valor_mobiliario` chegam 100%
vazias**, incluindo `Data_Valor_Mercado` / `Data_Valor_Contabil`, que a META declara **`date`** →
ficam em `_DATE_COLS` (tudo `NaT`). ⚠️ A asserção é sobre o **dtype** (`datetime64` × `string`),
nunca sobre `isna().all()` — branco vira NA sob `dtype="str"` também (lição do #179).

**4. Falso-positivo de CNPJ/CPF em coluna monetária, de novo.** `Valor`, `Saldo_Devedor`,
`Montante_Envolvido` acusam 1–38 acertos em milhares de linhas (~0,1–0,4%) por causa do zero-pad
do `unmask_cnpj`. **Ler a taxa:** as colunas de CNPJ dão 100% (ou 88% com placeholder), o ruído dá
menos de 1%.

**5. `Duracao_Transacao` traz 879 valores em `DD/MM/YYYY`** — é campo de **texto livre**
(`varchar` na META, 11.238 linhas), não data. Fica `str`; nunca entra em `_DATE_COLS`.

## ⚠️ Anti-cópia — três larguras colidem

`acao_entregue` × `remuneracao_acao` × `remuneracao_maxima_minima_media` têm **14 colunas cada** e
**compartilham as 10 primeiras**, divergindo só nas 4 últimas; `titulo_exterior` ×
`participacao_sociedade` têm **21 cada** com listas quase disjuntas. Cada contract é gerado do
**próprio** header e pinado; anti-cópia pinada por teste.

## Densidade monetária

É a fatia mais monetária do dataset (`Valor_*`, `Preco_*`, `Montante_*`, `Saldo_*`, `Salario`,
`Bonus_*`, `Participacao_Valor_*`, `Total_Remuneracao*`, `Quantidade_*`, `Numero_*`). A META
declara `numeric`/`int`; todas ficam **texto exato** (regra do #157) — `Decimal` a jusante.

## Controles negativos (3 mutações, todas vermelhas, cada uma de árvore limpa)

Baseline limpo: **179 passed**.

- [x] Copiar as 4 últimas colunas de `remuneracao_acao` para o `acao_entregue` (mesma largura,
      mesmo prefixo de 10) → **4 falhas**.
- [x] Declarar `Documento_Parte_Relacionada` como coluna de CNPJ → **7 falhas**.
- [x] Tirar `Data_Valor_Mercado` de `_DATE_COLS` → **1 falha** — e o número baixo é o achado:
      **existe exatamente uma defesa**, a que assere o **dtype**. Nenhum outro teste distingue,
      porque a coluna é 100% vazia e branco vira NA sob `str` também.

### ⚠️ Armadilha de método: o restore dos mutantes não restaurou nada

A 1ª rodada usou `git checkout -- <contract> <reader>` para desfazer cada mutação. Os readers
**ainda são untracked**, e `git checkout` com um pathspec desconhecido **aborta inteiro** — então
as três mutações **se acumularam**, e os números saíram inflados (4 / 11 / 12). Só apareceu porque
conferi os **valores do contract** depois, não o vermelho/verde.

**Regra:** para desfazer uma mutação num arquivo que ainda não está em git, restaurar por **cópia
de um snapshot**, nunca por `git checkout`. E um controle negativo só vale se o **baseline** for
re-medido entre as mutações.

## Legado (fora do escopo original, pedido do user)

Os 4 scripts de `bin/` indentados com **espaços** divergiam do `ruff format` do repo (tabs) e
apareciam eternamente em `ruff format --check`. Resolvido:

- [x] Indentação convertida no **arquivo inteiro, docstrings incluídas** — converter só o código
      (o que `ruff format` faz sozinho) deixa os corpos de docstring em espaços e cascateia
      **82 E101**.
- [x] **5 `ERA001` em comentários de prosa byte-idênticos ao `main`** — o ERA001 dispara pela
      **indentação**, não pelo texto (já registrado no repo). Reescritos, **nunca `# noqa`**.
- [x] **Prova diferencial de que os gates continuam funcionando**, já que `check_docstrings`,
      `check_provenance` e `check_typing` **não têm teste unitário**: rodei a versão do `HEAD` e a
      reindentada sobre o **mesmo** módulo-probe com violação real → `exit=1 / exit=0 / exit=1`
      nos dois. "Sair 0 na árvore limpa" **não** prova nada: um gate quebrado sai 0 sempre.
- [x] `git diff -w` confere: fora os 4 comentários, só reflow do `ruff format` (2 expressões que
      passaram a caber em 99 colunas com tab=4).

## Aberto / próximo

- [ ] **Release PATCH** (`feat`, `src/` muda).
- [ ] **Próxima issue decidida com o user: `FI/DOC/EVENTUAL`** (`eventual_fi_AAAA.csv`), que está
      listado no inventário do #122 e ainda não tem issue própria. Vem **antes** de DFP/ITR.
- [ ] Depois: **DFP** (12,12 MiB) → **ITR** (30,14) → `EVENTOS/RECOMPRA_ACOES`.

## ingestion-cia-aberta-cad_20260722_190000

# Work ledger — CIA_ABERTA/CAD ingestion reader (#153)

Branch `feat/153-cia-aberta-cad-reader`. Adds `CadastroCiaAbertaReader` over `cad_cia_aberta.csv`
(`CIA_ABERTA/CAD`), inaugurating the `cia_aberta/` portal root — **the last and largest root of the
#41 sweep**. Sixth slice of Wave 4.

⚠️ **This PR is the `CAD` slice only.** `CIA_ABERTA` holds nine datasets: `CAD` (here), the seven
`DOC` financial-statement datasets (`CGVN`, `DFP`, `FCA`, `FRE`, `IPE`, `ITR`, `VLMO`) and
`EVENTOS`. Each needs its own grounding against real bytes and its own PR — the root is too big for
one slice, and the sibling roots have repeatedly proven that shape is not inheritable.

## Grounding (real bytes)

- `cad_cia_aberta.csv`: **bare CSV** (not a ZIP), ISO-8859-1, CRLF, `;`, **fixed URL** → snapshot,
  **no `date_ref`**. Mould = `CadastroCiaEstrangReader` / `CadastroCiaIncentReader`, not the
  multi-member ZIP readers of COORD_OFERTA / CROWDFUNDING / OFERTA.
- **47 columns, 2 677 rows** (live-verified). Returned frame = 53 cols (47 source + 6 provenance).
- ⚠️ **NOT a copy of its CIA_* siblings** — the issuer key is **`CNPJ_CIA`** (the others use plain
  `CNPJ`), and it adds **`TP_MERC`** (`BOLSA` / `BALCÃO ORGANIZADO` / `BALCÃO NÃO ORGANIZADO`),
  which neither CIA_ESTRANG (49 cols) nor CIA_INCENT (47 cols) has. Same column *count* as
  CIA_INCENT — a coincidence, not a shared shape; transcribing the sibling would have shipped a
  wrong contract green.
- **7 date columns** (`DT_REG`, `DT_CONST`, `DT_CANCEL`, `DT_INI_SIT`, `DT_INI_CATEG`,
  `DT_INI_SIT_EMISSOR`, `DT_INI_RESP`). ⚠️ `MOTIVO_CANCEL` is **free text**, not a date — verified
  live (`CANCELAMENTO VOLUNTÁRIO`, `ELISÃO POR INCORPORAÇÃO`).
- **Two CNPJ columns** → `tuple_cnpj_cols = ("CNPJ_CIA", "CNPJ_AUDITOR")`; live counts 2 677 / 2 577
  non-blank. `RESP` carries a legal representative's name but there is **no CPF column**.
- `CD_CVM` / `CEP` / `TEL` / `FAX` / `DDD_*` are `numeric`/`char` in the META but stay `str` — they
  are identifiers, not quantities (`CD_CVM` arrives as `'25224'`).
- ⚠️ **META is a bare `.txt`** (`meta_cad_cia_aberta.txt`, 47 fields, single section
  `cad_cia_aberta`) — unlike the `.zip` METAs of the three preceding Wave 4 slices. The URL is
  constant per dataset and never derived.

## Done

- [x] Header fixture `tests/fixtures/cad_cia_aberta/cad_cia_aberta_header.csv` (verbatim real bytes,
      header-only — no PII). The pinned oracle the contract is generated **from**.
- [x] Contract `_internal/config/contracts/cad_cia_aberta.py` (`CAD_CIA_ABERTA`, 47 cols generated
      from the fixture) + re-exports in `contracts/__init__.py`.
- [x] `META_CAD_CIA_ABERTA` in `contracts/meta.py` + re-export.
- [x] `CadastroCiaAbertaReader` (`cia_aberta/cad/cadastro/cadastro.py`) + `MetaCadCiaAbertaReader`
      (`meta.py`) — **37th Meta reader**.
- [x] Nested `__init__.py` (`cia_aberta/`, `cad/`, `cad/cadastro/`) + flat re-exports in
      `ingestion/__init__.py` and top `filings_cvm/__init__.py` (imports + `__all__`).
- [x] Drift registry `bin/check_contract_drift.py`: `_UNEXPOSED_CONTRACTS` +`_META_MEMBERS` entries.
- [x] Tests: new `FlatCase` in `tests/unit/test_securit_cepac_flat_ingestion.py` (the shared flat-CSV
      harness — reused, not duplicated) + anti-tautology header test reading the fixture. Bumped
      `test_meta_readers.py` 36 → 37.
- [x] Docs: `docs/ingestion/cia_aberta_cad.md` + mkdocs nav + `docs/api.md` + `docs/ingestion/index.md`
      + root `CLAUDE.md` catalog + Layout tree + META count 36 → 37 (and corrected the stale
      `.txt`/`.zip` split to the measured 15/22).
- [x] Live-verified vs real CVM bytes: 2 677 rows × 53 cols, 7 date cols coerced, `MOTIVO_CANCEL`
      text, `CNPJ_CIA` 2 677 / `CNPJ_AUDITOR` 2 577 non-blank, all 6 provenance columns stamped,
      META 47 fields / section `cad_cia_aberta` / key `meta_cad_cia_aberta`.

## Remaining

- [ ] Gates: ruff, mypy, full unit suite, `mkdocs --strict`, codespell, full pre-commit.
- [ ] Commit → PR `Closes #153` → wait for approval + merge.
- [ ] After merge: release PATCH. Then the rest of `cia_aberta/`: the 7 `DOC` datasets + `EVENTOS`,
      **grounded one at a time**.

## ipe-cia-aberta-reader-159_20260725_080825

# Work ledger — #159 CIA_ABERTA/DOC/IPE reader (índice de documentos)

Branch `feat/159-ipe-cia-aberta-reader`. Fecha **#159**. **Com release** (`feat`, há diff em
`src/`) → PATCH. **Sétima fatia da Wave 4 do #41; abre o sub-root `CIA_ABERTA/DOC`.**

## Por que o IPE primeiro

Survey do `CIA_ABERTA/DOC` (medido, não presumido): os 7 datasets são **todos ZIP anual**
(`<ds>_cia_aberta_AAAA.zip`), mas o número de membros varia muito. Ordenado pelo custo:

| dataset | zip 2025 | membros |
|---|---|---|
| **IPE** | 2,16 MiB | **1** ← esta fatia |
| VLMO | 0,78 MiB | 2 |
| FCA | 0,37 MiB | 10 |
| CGVN | 4,01 MiB | ? |
| FRE | 8,10 MiB | ? |
| DFP | 12,12 MiB | ? |
| ITR | 30,14 MiB | ? |

IPE é o mais barato (1 membro) e o de semântica mais simples — índice de documentos, molde já
existente no repo.

## Molde

Dois readers existentes combinados, nenhum código novo de infraestrutura:

- **`DfinFiiReader`** — semântica de **índice de documentos** (`Link_Download` devolvido como texto
  e não seguido) e, por coincidência confirmada, **exatamente o mesmo par de date cols**
  (`Data_Referencia` + `Data_Entrega`).
- **`BalanceteFieReader`** — extração de **ZIP de 1 membro** (`extract_all` + `find_member` por
  nome exato).

## Grounding (medido contra os bytes reais de 2025 — nada presumido)

- **13 colunas**, ~49,3k linhas. Contract **gerado do header** e **pinado** a
  `tests/fixtures/ipe_cia_aberta/ipe_cia_aberta_header.csv` (bytes verbatim, ISO-8859-1).
- **2 date cols**, ambas **100% ISO** `AAAA-MM-DD` — e o META as declara `date` (dois oráculos
  concordando).
- ⚠️ **`CNPJ_Companhia` tem 44 placeholders `00.000.000/0000-00`** (emissores estrangeiros sem CNPJ
  brasileiro, ex. JBS Foods International DAC) + **49.233 válidos**, **zero malformados**.
  Devolvidos **como publicados**. `tuple_cnpj_cols=("CNPJ_Companhia",)` é seguro — **provado** com
  `find_file_problems`: só-placeholders → `ContractError`, misto → válido. A aresta está **pinada
  por teste** (mesma classe da lição `value-presence-contract-tolerates-empty-artifact` do CRI).
- `Codigo_CVM` (`Domínio: Numérico`) e `Versao` (`smallint`) no META ficam **`str`** —
  identificadores, não quantidades (precedente `DfinFiiReader`).
- `Tipo` (41.190), `Especie` (17.334), `Assunto` (32.777), `Protocolo_Entrega` (48.370) chegam
  **parcialmente preenchidos** — colunas obrigatórias, valores não.
- **META** = `.txt` solto, 13 campos, seção única, ISO-8859-1 + CRLF, **ordem alfabética** (≠ ordem
  do arquivo → o header real segue sendo a fonte da ordem).

## ⚠️ Achado que vale para as 6 fatias seguintes: 4 grafias de META em 7 datasets

| dataset | META |
|---|---|
| CGVN / FRE / VLMO | `meta_<ds>_cia_aberta.zip` |
| DFP / ITR | `meta_<ds>_cia_aberta_txt.zip` (**infixo `_txt`**) |
| **FCA** | **`fca_cia_aberta.zip`** (**sem o prefixo `meta_`**) |
| **IPE** | **`meta_ipe_cia_aberta.txt`** (**`.txt` solto**) |

Uma regra "derive o nome da META a partir do dataset" erraria em **3 dos 7** — 404 ou a
especificação do dataset errado, **com os testes verdes**. Confirma a regra padrão do repo: a URL é
constante por dataset, **jamais derivada**. Pinado por teste (`test_meta_url_is_the_loose_txt...`).

## Feito

- [x] `IpeCiaAbertaReader` (`ingestion/cia_aberta/doc/ipe/ipe.py`) + `MetaIpeCiaAbertaReader`
  (**38º**), pasta por dataset (`ipe/{ipe.py,meta.py,__init__.py}`) conforme a convenção.
- [x] Contract `ipe_cia_aberta.py` **gerado do header** (script, não transcrição) + fixture verbatim.
- [x] `META_IPE_CIA_ABERTA` em `contracts/meta.py` (factory compartilhado).
- [x] Registrado nas 4 camadas de `__init__` + `contracts/__init__`; **`__all__` reordenado**
  (a inserção ingênua quebrou a ordem alfabética — corrigido e verificado, `sorted == True`).
- [x] Drift registry (`bin/check_contract_drift.py`): import + `_UNEXPOSED_CONTRACTS` (o reader
  guarda o contract inline, como o `DfinFiiReader`) + `_META_MEMBERS`. Fecha: 183 readers, 38 Meta.
- [x] Docs: página nova `docs/ingestion/ipe_cia_aberta.md`, nav, `docs/api.md` (seção nova + o aviso
  do CAD corrigido), `docs/ingestion/meta.md` (**as 3 contagens 37→38 + linha na tabela**),
  `CLAUDE.md` raiz (catálogo + árvore de layout).
- [x] `tests/unit/test_meta_readers.py`: total 37 → 38.
- [x] 12 testes novos em `test_ipe_cia_aberta_ingestion.py`.

## Verificação

- [x] **Oráculo anti-tautologia provado por MUTAÇÃO** (não só caminho feliz): com uma coluna
  **removida** do contract → falha; com `Especie` → `Espécie` (erro de transcrição realista, com
  acento) → falha; restaurado → passa. É a única asserção do arquivo cujo valor esperado não fomos
  nós que escrevemos.
- [x] **Semântica "ao menos um CNPJ válido" provada** com `find_file_problems` antes de escrever o
  docstring que a afirma — só-placeholders levanta, misto passa.
- [x] `Link_Download` **não seguido**: a lista de URLs capturadas contém **apenas** o ZIP, e a
  asserção verifica explicitamente que nada de `rad.cvm.gov.br` foi requisitado.
- [x] URL **anual**: dois `date_ref` diferentes do mesmo ano resolvem para o mesmo artefato.
- [x] `QUOTE_NONE` conferido contra os bytes reais: **639 campos contêm `"` literal**, mas todos
  **no meio** do campo, então `QUOTE_NONE` e `QUOTE_MINIMAL` dão **valores idênticos** em 2025 (0
  linhas divergentes) e ambos 13 campos. Mantido `QUOTE_NONE` (convenção do repo + robusto a um
  `"` inicial futuro) — **sem alegar que 2025 o provou necessário**.
- [x] ruff check + format limpos, `mypy` **352** arquivos OK, `check_typing`/`check_provenance`/
  `check_dtypes`/`check_docstrings` OK, **1870 unit** (era 1850, +20), 4 integration, codespell
  limpo, `mkdocs build --strict` limpo, `check_backlog_ledger` OK.
- [x] ⚠️ **`ruff check --fix` foi necessário para 4 blocos de import** — a inserção por âncora
  (`str.replace`) coloca o import no lugar do texto ancorado, não na posição alfabética, então o
  `I001` disparou nos 4 arquivos de registro. Corrigido com `--fix` **escopado aos 4 arquivos** e
  conferido por `--numstat`: **só inserções, zero deleções** → nenhum churn em código alheio.
- [x] ⚠️ **2 quebras minhas pegas pelos gates, não pelo olho:** (a) linkei
  `../architecture.md`, **que não existe** neste repo (presumi o nome) → `mkdocs --strict` abortou;
  apontado para `../api.md`, que documenta as colunas de proveniência. (b) codespell pegou o pt-BR
  `longe` → reescrito (mais claro assim), sem crescer a lista de ignore.

## Aberto / próximo

- [ ] PR (`Closes #159`) → aprovação → merge → **release PATCH**.
- [ ] As 6 fatias restantes do `DOC` (VLMO 2 membros → FCA 10 → CGVN → FRE → DFP → ITR) e o
  `EVENTOS/RECOMPRA_ACOES`. **Grounding próprio para cada** — a tabela de membros acima já mostra
  que a forma não se repete; e a META de cada um tem de ser **verificada, nunca derivada**.

## itr-cia-aberta-readers-198_20260802_212401

# ITR CIA_ABERTA — 19 membros, 3,64M linhas — **FECHA O `DOC` (7/7)** — #198

Branch: `feat/198-itr-cia-aberta-readers` · Issue: #198 · Sub-root `CIA_ABERTA/DOC` **completo**;
resta só `EVENTOS/RECOMPRA_ACOES` no root `cia_aberta/`.

## Feito

- [x] Grounding contra os bytes reais (2025) — membros, cols **e** linhas, ragged, valores, e a
      **grafia da META medida** entre 4 candidatas.
- [x] **Comparação header a header contra as fixtures pinadas do DFP** — o achado da fatia.
- [x] 19 fixtures header-only verbatim + 19 contracts **gerados dos headers do ITR** (nunca
      copiados do DFP).
- [x] 19 readers sobre `_base_itr_reader.py` + `MetaItrCiaAbertaReader` (45º).
- [x] Registro nos **3** `__init__` + os 2 contracts em `contracts/__init__.py`; `_META_MEMBERS`.
- [x] **Contagens RE-MEDIDAS:** **279 readers** (era 259), **45 Meta = 17 `.txt` + 28 `.zip`**.
- [x] 107 testes no arquivo do ITR; suíte **2784** unit + 4 integration.
- [x] Docs: página nova + `nav`, seção em `api.md`, roster/contagens em `meta.md`, catálogo +
      layout + contagens no `CLAUDE.md`.

## Medições (2025)

**19 membros, 31,63 MB, 3.640.994 linhas** — 3× o DFP, o maior artefato da biblioteca. Nenhum
ragged. 19 → **6** listas distintas (16 demonstrações em 3), a mesma forma do DFP.

CNPJ_CIA **100% válido** em todos (medido sobre **valores distintos** — ver nota de método), todo
`DT_*` **100% ISO** sem branco. Parcialmente vazias: `COLUNA_DF` (1.767/623.847) e **`TP_RELAT_ESP`
(4.844/7.051)**.

## ⚠️⚠️ O achado — 18/19 idênticos ao DFP, e exatamente 1 não

| | DFP (anual) | ITR (trimestral) |
|---|---|---|
| `parecer`, coluna 5 | `TP_RELAT_AUD` | **`TP_RELAT_ESP`** |

**Mesma largura (8), mesma posição (5ª), 7 de 8 nomes.** O DFP é *auditado*; o ITR passa por
*revisão especial*. Copiar o contract do `parecer` do DFP erraria **uma** coluna e passaria em tudo
menos no header pinado.

⚠️ **É o contraponto exato da lição que o DFP acabou de ensinar.** Lá o achado foi "aqui, ao
contrário de CRA/CRI/FCA/FRE, membros irmãos **são** idênticos". Levar *essa* generalização para o
dataset vizinho é o mesmo erro num casaco novo — **18/19 idênticos é precisamente o que faz alguém
copiar o 19º.** A comparação é pinada **membro a membro, contra as fixtures dos DOIS datasets**.

## Nota de método — medir sobre valores DISTINTOS

O probe original (herdado do DFP) validava CNPJ/ISO **linha a linha**: 3,6M linhas × 15 colunas ≈
**50 milhões** de validações. Ficou inviável (nem chegou a imprimir uma linha em >10 min).

Trocado por varredura sobre **valores distintos** por coluna — `CNPJ_CIA` tem ~700 empresas
distintas, não 3,6M. **Mesma evidência, ordens de grandeza mais barato**, e terminou em segundos.
⚠️ Isso vale porque as perguntas são sobre o **conjunto** de valores ("todo `DT_*` é ISO?", "todo
CNPJ é válido?"); uma pergunta sobre **taxa** (quantas linhas em branco) continua precisando da
contagem por linha, e foi feita assim.

## Controles negativos (todos vermelhos)

Baseline **107 passed**.

- [x] **Copiar o contract do `parecer` do DFP** (a mutação que esta fatia existe para pegar) →
      **3 falhas**, incluindo a cruzada nomeada.
- [x] `DRE_con` lendo o membro do irmão → **1 falha** — a defesa de **identidade do membro**, nascida
      no DFP, funciona aqui de imediato.

## Aberto / próximo

- [ ] **Release PATCH** ao mergear (`feat`, `src/` muda).
- [ ] **`EVENTOS/RECOMPRA_ACOES`** — o **único** pendente do root `cia_aberta/`.
- [ ] #192 (testes dos 3 `bin/check_*` sem cobertura) segue em Ready.

## recompra-acoes-readers-200_20260803_093552

# RECOMPRA_ACOES — 3 membros — **FECHA O ROOT `cia_aberta/`** — #200

Branch: `feat/200-recompra-acoes-readers` · Issue: #200 · **Inaugura o sub-root `eventos/`** e
**completa o maior root do portal** (`CAD` 1/1 + `DOC` 7/7 + `EVENTOS` 1/1).

## Feito

- [x] **Descoberta do artefato pela listagem do portal** — eu não sabia o nome do arquivo; a
      listagem de `DADOS/` deu `cia_aberta_recompra_acoes.zip`, e a de `EVENTOS/` confirmou que
      `RECOMPRA_ACOES` é o **único** dataset do sub-root.
- [x] Grounding contra os bytes reais — membros, cols **e** linhas, ragged, valores (**sobre
      distintos**, aplicando a lição do ITR) e a **META medida de 2 formas independentes**.
- [x] 3 fixtures header-only + 3 contracts **gerados dos headers**.
- [x] 3 readers sobre `_base_recompra_acoes_reader.py` (molde do CROWDFUNDING: snapshot ZIP
      multi-membro, sem `date_ref`) + `MetaRecompraAcoesReader` (46º).
- [x] Registro: **novo sub-root `eventos/`** + `cia_aberta/` + os 2 contracts; `_META_MEMBERS`.
- [x] **Contagens RE-MEDIDAS:** **283 readers** (era 279), **46 Meta = 17 `.txt` + 29 `.zip`**.
- [x] 27 testes no arquivo do RECOMPRA; suíte **2827** unit + 4 integration.
- [x] Docs: página nova + `nav`, seção em `api.md`, roster/contagens em `meta.md`, catálogo +
      layout + contagens no `CLAUDE.md`.
- [x] ⚠️ **Cabeçalho do root corrigido** — dizia que os 7 `DOC` e o `EVENTOS` estavam **pendentes**,
      o que virou falso. É o texto que uma próxima sessão lê primeiro.

## Medições

**ZIP snapshot, 0,09 MB, 3 membros, nenhum ragged**, todos ligados por `ID_Programa` (único no
registro: 1.916 distintos em 1.916 linhas; repete nos satélites).

| membro | cols | linhas | date cols | cnpj cols |
|---|---|---|---|---|
| `cia_aberta_recompra_acoes` | 11 | 1.916 | 2 | `CNPJ_Companhia` (355/355 distintos válidos) |
| `..._intermediarios` | 3 | 4.269 | **0** | `CNPJ_Intermediario` (116/116) |
| `..._quantidades` | 5 | 2.381 | **0** | **nenhuma** |

## ⚠️⚠️ Achado 1 — não segue os vizinhos do `DOC`, em 4 pontos medidos

1. **Snapshot ⇒ sem `date_ref`** (os 7 do `DOC` são `_AAAA.zip`). **Um arquivo cobre de 1997 até
   hoje**, e a CVM sobrescreve no lugar — só `path_raw` guarda o retrato do dia.
2. **Nome INVERTIDO:** `cia_aberta_recompra_acoes.zip` põe o **root primeiro**; `dfp_cia_aberta_AAAA.zip`
   põe o **dataset**. Derivar do padrão do `DOC` erraria.
3. **CamelCase** (`CNPJ_Companhia`/`Data_Deliberacao`), como o CGVN e **não** como DFP/ITR/FCA.
   DFP pinado como **contra-exemplo vivo**.
4. **2 dos 3 membros sem NENHUMA coluna de data.**

## ⚠️⚠️ Achado 2 — `quantidades` não declara CNPJ porque não tem

`tuple_cnpj_cols=()` é **decisão medida**, não esquecimento: o membro identifica só o programa.
Declarar inventaria coluna inexistente (e o contrato falharia toda leitura).

⚠️ **Vazio e esquecido são indistinguíveis num diff**, então o teste afirma os **3 membros juntos** —
o vazio **e** os dois que declaram. Controle negativo: dar CNPJ ao `quantidades` → **7 falhas**.

## Nota de método — um mutante que "passou" e não tinha mutado

A 3ª mutação (trocar `CNPJ_Companhia` por `CNPJ_CIA`) veio como **27 passed**. Não era mutante
sobrevivente: o script assertava `count(...) == 1` e o nome aparece **2 vezes** no arquivo
(`tuple_required` **e** `tuple_cnpj_cols`), então o `assert` explodiu e **nada foi escrito**.

Re-rodada com as 2 ocorrências → **3 falhas**. É exatamente a armadilha já registrada: **um controle
que passa por não ter feito nada é pior que um que falha.** O assert de contagem é o que a expôs —
sem ele, teria virado "a suíte não pega a convenção do DOC".

## Controles negativos (3, todos vermelhos)

Baseline **27 passed**, restore por cópia de snapshot.

- [x] `quantidades` ganha coluna de CNPJ → **7 falhas**.
- [x] Registro lendo o membro do satélite → **6 falhas** (a defesa de identidade do membro,
      nascida no DFP, já vem de série).
- [x] Adotar a convenção do `DOC` (`CNPJ_CIA`) → **3 falhas** (ver nota de método).

## Aberto / próximo

- [ ] **Release PATCH** ao mergear (`feat`, `src/` muda).
- [ ] 🎉 **O root `cia_aberta/` está COMPLETO.** Próximo alvo sai do inventário do **#122** /
      survey do **#41** — decidir com o user qual root atacar.
- [ ] #192 (testes dos 3 `bin/check_*` sem cobertura) segue em Ready.

## vlmo-cia-aberta-readers-164_20260725_195922

# Work ledger — #164 CIA_ABERTA/DOC/VLMO readers (índice + conteúdo)

Branch `feat/164-vlmo-cia-aberta-readers`. Fecha **#164**. **Com release** (`feat`, diff em `src/`)
→ PATCH. **2ª das 7 fatias `DOC`** (`DOC` agora 2/7).

## Forma da fonte (medida, nada presumido)

⚠️ **Os 2 membros NÃO são registro+satélite** — são **índice + conteúdo**:

| membro | cols | linhas | o que é |
|---|---|---|---|
| `vlmo_cia_aberta_2025.csv` | 12 | 5.812 | índice de documentos (molde IPE + `Motivo_Reapresentacao`) |
| `vlmo_cia_aberta_con_2025.csv` | 17 | 63.056 | movimentações de valores mobiliários |

Base privada `_base_vlmo_reader.py` (molde: `_base_inf_mensal_fii_reader` — ZIP anual multi-membro
com `_MEMBER_STEM`). Contracts **gerados dos headers** e pinados a fixtures verbatim.

## ⚠️ O achado principal: as primeiras colunas monetárias do root `cia_aberta/`

`Preco_Unitario` e `Volume` chegam com **10 casas decimais**; `Quantidade` é inteiro. O META
declara `decimal`/`decimal`/`bigint`. **Ficam texto exato.**

**Provado por mutação, não afirmado:** tipando `Volume` como `float64`,
`61961072.9999543100` → `np.float64(61961072.99995431)` — **os 2 últimos dígitos somem em
silêncio**. E **duas defesas independentes dispararam na mesma mutação**:

1. o teste de valor falhou;
2. **`bin/check_dtypes.py` (o gate do #157) acusou o literal `"float64"` → EXIT=1**.

Ou seja: o trabalho do #157, feito duas fatias atrás, **pegou seu primeiro caso real aqui**. Os
dígitos `…99995` são resíduo de aritmética float **na própria CVM** — devolvê-los como publicados é
fidelidade; re-arredondar seria inventar dado.

## Outros achados

- ⚠️ **`Data_Movimentacao` chega ~58% VAZIA** (26.328 de 63.056). É data por contrato; **verificado
  no seam real antes de escrever** que branco vira `NaT` e o `errors="raise"` **não** levanta. O
  índice tem datas 100% preenchidas, então só o membro `con` exercita esse caminho — sem o teste,
  uma leitura real de qualquer ano quebraria.
- ⚠️ **SEM dado pessoal, contra a intuição.** "Informe de insider" sugere CPF; medindo, `Empresa` é a
  **companhia** (`Tipo_Empresa` ∈ Companhia/Controlada/Controladora) e `Tipo_Cargo` é **categoria de
  cargo**. **Zero** CPF/CNPJ dentro de `Empresa`. O indivíduo nunca é nomeado.
- `CNPJ_Companhia` **100% válido nos dois** — sem o placeholder `00.000.000/0000-00` do IPE.
- ⚠️ **META é `.zip` e o `.txt` dá 404 — o INVERSO do IPE** (cujo `.txt` é a única forma). 2 membros,
  `section` **assimétricas** (`meta_vlmo_cia_aberta` + `con`) porque o 1º membro é o stem puro →
  fallback documentado do `_section_of` (molde INTERMED/COORD_OFERTA). **Previsto do checkpoint
  ANTES de escrever**, confirmado no live-verify, pinado por teste.

## Feito

- [x] 2 readers + base privada + `MetaVlmoCiaAbertaReader` (**39º**).
- [x] Contracts gerados dos headers + 2 fixtures verbatim.
- [x] Registrado nas 5 camadas de `__init__` + `contracts/__init__` + `_META_MEMBERS` do drift
  (registry fecha: **186 readers, 39 Meta**). `_UNEXPOSED_CONTRACTS` **não** foi tocado — estes
  readers expõem `_CONTRACT` na classe (ao contrário do IPE, inline).
- [x] Docs: página nova + nav + `api.md` (seção + Meta 39) + `meta.md` (3 contagens + linha) +
  **`CLAUDE.md` raiz (catálogo + árvore + contagem META 38→39)** e `test_meta_readers.py` 38→39.
- [x] 16 testes novos.

## Verificação

- [x] **Oráculo anti-tautologia por mutação**: renomear `Preco_Unitario` no contract → falha;
  restaurado → passa.
- [x] **Teste monetário por mutação**: tipar `Volume` como `float64` → o teste falha **e** o
  `check_dtypes` acusa. Sem essa mutação o teste seria só mais uma tautologia verde.
- [x] Asserção monetária feita sobre a **string**, não sobre número: `float()` compara igual a várias
  strings decimais diferentes, então só o texto prova que nada se perdeu. `Decimal(str)` round-trip
  também pinado.
- [x] Anti-cópia índice×conteúdo pinada (conjuntos de colunas disjuntos nos pontos que importam).
- [x] ⚠️ **Um erro meu pego por olhar os números**: as âncoras de `str.replace` casaram só os blocos
  de **import**, não os `__all__` (que são strings com aspas) — os 3 readers ficaram **importáveis
  mas NÃO exportados**, e as contagens não subiram (189/183/4/2 iguais). Corrigido; agora **192
  nomes públicos, 39 Meta**. *Conferir a contagem depois de registrar, não só rodar os testes* — os
  testes do reader passariam mesmo sem export.
- [x] `check_dtypes` limpo; ruff/format; mypy; suíte completa; mkdocs --strict; codespell.

## Aberto / próximo

- [ ] PR (`Closes #164`) → aprovação → merge → **release PATCH**.
- [ ] `DOC` restante (5): **FCA** (10 membros, o próximo salto de forma) → CGVN → FRE → DFP → ITR,
  depois `EVENTOS/RECOMPRA_ACOES`. **Conferir a URL da META de cada um no portal** — já vimos 4
  grafias, e IPE×VLMO provam que datasets vizinhos se contradizem.
