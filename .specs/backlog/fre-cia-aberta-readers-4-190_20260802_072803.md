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
