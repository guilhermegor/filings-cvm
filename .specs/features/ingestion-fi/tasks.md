## compl-fi-reader-284_20261031_100000

# FI Complemento reader (#284) -- work ledger

## Measured (not assumed)

- [x] Series: 16 monthly ZIPs `201801`-`201904` (CKAN resource list); the series is closed.
- [x] Each ZIP has 4 members: `compl_fi`, `compl_fi_inf`, `compl_fi_inf_cotst`, `compl_fi_prest` (`_AAAAMM.csv`).
- [x] `;`, CRLF, ISO-8859-1 (non-UTF-8 in every file), literal `"` in free text (QUOTE_NONE), 0 ragged rows.
- [x] Headers identical in all 16 months, per member: 20 / 6 / 7 / 5 columns. No regime cut.
- [x] Rows over the 16 months: 11,604 / 25,292 / 21,235 / 39,592.
- [x] `CNPJ_FUNDO` 100% well-formed; `CNPJ_AG_RISCO` (main member) valid or empty (188 empty). No CPF column.
- [x] `DT_COMPTC` 100% ISO. `TP_FUNDO`: FI, FAPI, FIIM, FMP-FGTS, FMP-FGTS CL.
- [x] META `meta_compl_fi_txt.zip` has 4 members (`meta_compl_fi*.txt`).

## Implemented

- [x] Contracts `COMPL_FI*`, pinned to 4 verbatim header fixtures; `META_COMPL_FI`.
- [x] `ComplFiReader`, `ComplFiInfReader`, `ComplFiInfCotstReader`, `ComplFiPrestReader`, `MetaComplFiReader`.
- [x] `_META_MEMBERS`, `_IMPLEMENTED_PACKAGES`, registered up to `fi/`.
- [x] META count 50, public surface 297 (re-measured from code after merging main).
- [x] Docs page, nav, api.md, meta.md, CLAUDE.md catalog.

## Open

- [ ] PR review and merge (orchestrator).

## entrega-fi-reader-285_20261031_120000

# FI Entrega reader (#285) -- work ledger

## Measured (not assumed)

- [x] Series: `202501`-`202610` (22 monthly ZIPs downloaded); `202412` and earlier probes answer 404.
- [x] Each ZIP has 2 members: `fi_entrega_documento_AAAAMM.csv` and `fi_entrega_documento_diario_AAAAMM.csv`.
- [x] Same 11-column header in both members in all 22 months: no schema cut, no `Pre*` reader.
- [x] `;`, CRLF, ISO-8859-1, no quotes, 0 ragged rows (202609). CNPJ 14 digits unpunctuated, no PII.
- [x] Dates ISO; `Data_Hora_Entrega` datetime with ms; `ID_Subclasse` mostly empty.

## Implemented

- [x] Contracts `ENTREGA_FI`, `ENTREGA_FI_DIARIO`, pinned to verbatim headers.
- [x] `EntregaFiReader`, `EntregaFiDiarioReader`, `MetaEntregaFiReader`; registered up to `fi/`.
- [x] `_META_MEMBERS`, `_IMPLEMENTED_PACKAGES` (META describes both members: no undescribed entry).
- [x] META counts 51 -> 52 (22 `.txt` + 30 `.zip`), public surface 300 -> 303 (re-measured
  from code after merging main).
- [x] Docs page, nav, api.md, meta.md, CLAUDE.md catalog and layout.
- [x] Unit tests.

## Open

- [ ] PR review and merge (orchestrator); counts reconcile with #282/#283/#284 at merge.

## feat-extrato-fi-209_20260809_020000

# Ledger — #209 FI/DOC/EXTRATO readers (anual pré/pós-2020 + snapshot)

Branch: `feat/209-extrato-fi-readers` · Issue: #209 · Class: **src** (release **PATCH** ao mergear)

## Os dois achados que definiram o desenho

### 1. O dataset publica DOIS artefatos, e o sem-partição é um SNAPSHOT

| artefato | grão |
|---|---|
| `extrato_fi_AAAA.csv` (2015–2026) | **toda** entrega do ano |
| `extrato_fi.csv` (URL fixa) | **o último extrato de cada fundo** |

**38.454 linhas / 38.454 CNPJ distintos** ⇒ 1 linha por fundo. O `DT_COMPTC` cobre 2015–2026 porque
cada fundo traz a data do *seu* último — o que faz o arquivo **parecer** a série acumulada.
Provas: **0** linhas exclusivas do snapshot contra os anuais (2025 e 2026), e o anual de 2025 tem
13.590 linhas contra 8.455 datadas de 2025 no snapshot. **"Mais recente" foi VERIFICADO**: nos
2.469 fundos com >1 entrega em 2025, a data do snapshot é o máximo do ano ou posterior — **zero**
contraexemplos.

⚠️ **É o único artefato do acervo com chave única — DOCUMENTADA, não imposta** (o `read()` não
valida; ver a rodada de review no fim). E ela **não** vale para o anual.

### 2. Corte de schema em 2019→2020 — e NÃO é RCVM 175

`CNPJ_FUNDO` (116 cols) → `TP_FUNDO_CLASSE` + `CNPJ_FUNDO_CLASSE` (117). **Mesma troca do
PERFIL_MENSAL, data diferente**: lá `202312`, aqui `2020`. A **RCVM 175 é de dezembro de 2022**,
logo não pode ser a causa aqui.

⚠️ **Consequência de nomenclatura:** o reader é `ExtratoFiPre2020Reader`, **não** `Pre175`. Copiar o
nome do dataset vizinho afirmaria uma causa que as datas desmentem. As outras **115 colunas são
idênticas**, posição por posição.

## Feito

- [x] **3 readers + 2 bases privadas** — `ExtratoFiReader` (117c, 2020+), `ExtratoFiPre2020Reader`
      (116c, 2015–2019), `ExtratoFiSnapshotReader` (**sem `date_ref`**). Duas bases porque os dois
      tipos de artefato diferem em exatamente uma coisa: se um período seleciona o arquivo.
- [x] **3 contracts** gerados dos bytes reais e **pinados** a `tests/fixtures/extrato_fi/`.
      O snapshot tem contract e `source_key` próprios **apesar de colunas idênticas** ao anual — são
      artefatos diferentes, e proveniência/deriva identificam fonte pelo `source_key`.
- [x] `MetaExtratoFiReader` (**48º**). Registros: `contracts/__init__.py` (**295**), os 3 `__init__`
      do caminho, `_META_MEMBERS` + `_UNEXPOSED_CONTRACTS` + `_META_UNDESCRIBED_READERS` do drift
      job, `_IMPLEMENTED_PACKAGES` (45 → **46**; gate agora reporta **8** de 54).
- [x] **26 testes**; suíte **2908** (era 2866). Docs: página nova + nav, `api.md`, `meta.md`
      (47→**48**), `CLAUDE.md` raiz (catálogo + layout + META **re-medida**: `48 = 19 .txt + 29 .zip`).
- [x] Tipagem: **só `DT_COMPTC`** é data (1 de 117 na META). `PRAZO` é `varchar` com `DD/MM/YYYY` e
      fica texto. 74 `numeric` + 4 `decimal` + 4 `int` viram texto exato (até **12 casas**).
      `QUOTE_NONE` conferido: aspas existem, ficam literais, **zero linhas ragged** nos 3 artefatos.

## Controles negativos — 5, todos vermelhos, restore verificado

| mutação | falhas |
|---|---|
| derivar o contrato pré-2020 do bloco-chave atual (a armadilha de cópia) | **4** |
| coagir `PRAZO` como data (a armadilha do `DD/MM/YYYY`) | **1** |
| dar ao snapshot o `source_key` do anual (colapsar 2 artefatos em 1) | **2** |
| renomear o reader legado para `Pre175` | **31 erros** (ver nota) |
| alargar a janela 2020+ para engolir o regime legado | **2** |

⚠️ **NOTA — o M4 não provou o que eu queria, e refiz.** Ele deu **31 erros de coleta**, não uma
asserção falhando: renomear a classe quebra a cadeia de imports em 4 módulos, então nada chegou a
assertar. O meu teste de nome era **tautológico** (`Cls.__name__ == "Cls"` só roda se o import já
funcionou). Reescrito para varrer o `__all__` do pacote, e **isolado com uma mutação que troca só a
entrada do `__all__`, deixando todos os imports intactos** → **exatamente 1 falha, a certa**. Agora
é defesa, não decoração.

⚠️ **O M5 expôs de novo a armadilha do restore:** `git checkout --` num arquivo **untracked** é
no-op silencioso. O script detecta e refaz por re-edição, com `diff` conferido.

Restore por **cópia de snapshot** com `diff` nas 3 vias a cada rodada; baseline re-medido entre as
mutações (2908 antes e depois). Cada mutação **assertou a própria precondição e imprimiu o que
mudou**.

## Aberto

- [ ] Release **PATCH** ao mergear (há diff em `src/`).

Completed — kept as a record.

## Rodada de review (CodeRabbit, PR #210) — 3 aceitas, 1 declinada

- [x] ⚠️ **Bug real meu:** `ExtratoFiPre2020Reader(2014)` mandava "use `ExtratoFiReader`" — conselho
      **errado**, esse cobre 2020+ e também não tem 2014; a CVM não publica antes de **2015**. A
      guarda agora separa "o outro regime tem" de "ninguém tem" (`_SERIES_FIRST_YEAR`), e o teste
      que **pinava a mensagem errada** foi substituído por um que exige a mensagem certa **e** que o
      irmão **não** seja citado.
      → ⚠️ **O mesmo bug existia no `PERFIL_MENSAL`** (`PerfilMensalPre175Reader(2018)` apontava o
      irmão). Corrigido junto, com teste — deixar um erro conhecido no módulo vizinho por "estar
      fora do escopo" seria pior que o diff maior.
- [x] **Exagero meu no texto:** eu escrevera que o snapshot "**afirma** chave única". Nada afirma —
      é propriedade **medida da fonte**, documentada, e o `read()` não valida. Reescrito nos 3
      lugares (contract, reader, `api.md` + página). Declinei a parte "enforce": exigiria maquinaria
      nova no `FileContract`, engordaria o reader, e uma duplicata futura é mudança **na CVM** —
      trabalho do job de deriva.
- [x] **Imprecisão real:** `api.md` dizia "uma linha por **fundo**" enquanto o resto diz
      "fundo/classe" (a chave é `CNPJ_FUNDO_CLASSE`). Uniformizado.
- [ ] **Declinada — "o PR deixa `42` em dois documentos de META".** ❌ **Falso.** Medido: o único
      `42` nesses arquivos é `139.342 · 189.402`, contagem de linhas numa tabela do ITR. Nenhum doc
      afirma 42 Meta readers, e o gate `test_meta_readers` (que cobre `meta.md` e `api.md`) passa
      com o valor real, **48**.

## feat-perfil-mensal-206_20260808_090223

# Ledger — #206 FI/DOC/PERFIL_MENSAL readers (2 regimes)

Branch: `feat/206-perfil-mensal-readers` · Issue: #206 · Class: **src** (release **PATCH** ao mergear)

## Por que este dataset

Era o **único padrão regulatório com writer de submission e sem reader**:
`submission/perfil_mensal.py` (`PerfilMensal`, V4) existe desde o início. Está no inventário do #122
e foi o alvo escolhido com o user depois do fechamento do root `cia_aberta/`.

## Grounding — tudo medido na fonte

`perfil_mensal_fi_AAAAMM.csv`, **CSV solto** (não ZIP), **particionado por MÊS**, série
`201901`…`202607` (91 arquivos, listagem do portal). `202506` = **13,19 MB / 107 cols / 24.832
linhas**, zero ragged, ISO-8859-1, `;`.

### ⚠️⚠️ O achado principal — um padrão de nome, DOIS schemas

Busca binária sobre os headers publicados:

| regime | meses | cols | bloco-chave |
|---|---|---|---|
| pré-RCVM 175 | `201901`–**`202311`** | **106** | `CNPJ_FUNDO` |
| pós-RCVM 175 | **`202312`**–`202607` | **107** | `TP_FUNDO_CLASSE` + `CNPJ_FUNDO_CLASSE` |

**As outras 105 colunas são idênticas** — `pré[1:] == pós[2:]`, posição por posição, medido. É a
armadilha de cópia mais apertada do acervo: derivar um contrato do outro "arrumando a primeira
coluna" acerta **105 de 106** nomes e passa em tudo menos no header pinado. O corte é **medido**,
não deduzido da data da norma.

## Feito

- [x] **2 readers + base privada** — `PerfilMensalReader` (107c, `202312`+) ·
      `PerfilMensalPre175Reader` (106c, `201901`–`202311`) · `_base_perfil_mensal_reader.py`.
- [x] **2 contracts** em `_internal/config/contracts/perfil_mensal_fi.py`, **gerados dos bytes reais**
      (script, nunca transcritos) e **pinados** a `tests/fixtures/perfil_mensal_fi/*_header.csv`
      (**header-only** — as linhas de dados carregam CPF).
- [x] `MetaPerfilMensalFiReader` — o **47º** Meta reader.
- [x] **Guarda de janela**: pedir a um reader um mês do outro regime levanta `ValueError`
      **nomeando o irmão**, antes de baixar 13 MB.
- [x] Registros: `contracts/__init__.py` (291 exportados), `fi/doc/perfil_mensal/__init__.py` →
      `fi/doc/__init__.py` → `fi/__init__.py` (3 níveis), `_META_MEMBERS` + o mapa de contracts do
      `check_contract_drift.py`, `_IMPLEMENTED_PACKAGES` do `check_portal_completeness.py`.
- [x] **22 testes** novos; suíte **2866** (era 2830).
- [x] Docs: página nova `docs/ingestion/perfil_mensal_fi.md` + nav, `docs/api.md`,
      `docs/ingestion/meta.md` (46→**47**), `CLAUDE.md` raiz (catálogo + layout + contagens META).

## Duas decisões de design que a medição forçou

- [x] **O `date_ref` padrão de um regime ENCERRADO é o último mês que ele cobre, não hoje.**
      Descoberto porque `test_reader_retry_policy` instancia **todo** reader sem argumentos:
      `PerfilMensalPre175Reader()` caía em `hoje` (2026-08) e a própria janela rejeitava. A saída
      errada seria isentar o gate — um gate que ganha exceções apodrece. Um reader cujo único
      comportamento sem argumentos é levantar não é construtível por chamador genérico nenhum.
- [x] **`_META_UNDESCRIBED_READERS` novo em `check_contract_drift.py`.** A META lista **só** o
      header pós-175 (107 campos, sem `CNPJ_FUNDO`), então o job reportou
      `contract column 'CNPJ_FUNDO' is not in META` — verdadeiro, explicado e **permanente**.
      `_PARTIAL_DATASETS` não servia: ele suprime a direção **oposta** (campo da META fora do
      contrato) e mantém esta de propósito. O reader pré-175 sai da comparação com a META; o
      oráculo do **header real** continua rodando para ele, que é o que pode de fato atestá-lo.
      Sem isso o job repetiria a mesma linha toda semana — e achado conhecido-falso recorrente é
      como um relatório deixa de ser lido (a lição que este mesmo dia rendeu no #204).

## Armadilhas honradas

- [x] **6 colunas `CPF_CNPJ_*`** (`COMITENTE_1..3`, `EMISSOR_1..3`) **fora de `tuple_cnpj_cols`** —
      a irmã `PF_PJ_*` (domínio `PF`/`PJ`) é que tipa, e o `PF` **ocorre na fonte**. Declarar
      passaria num mês todo-PJ e levantaria no primeiro mês com pessoa física, no ambiente do
      consumidor. Só `CNPJ_FUNDO_CLASSE`/`CNPJ_FUNDO` é coluna de CNPJ.
- [x] **As 5 `CENARIO_FPR_*` parecem numéricas e não são** — `-0,0004` com **vírgula** decimal
      misturado a texto livre (`pessimista`, `-`), `varchar(150)` na META.
- [x] **`NR_DIA_CEM_PERC`/`NR_DIA_CINQU_PERC` são `numeric(14,4)`** apesar do prefixo `NR_`, que em
      toda vizinha (`NR_COTST_*`) marca contagem. **O prefixo não é o tipo.**
- [x] **53 `numeric` + 17 `int` ficam texto exato**; 2 date cols; **6 colunas 100% vazias** em
      `202506` e `DT_COTA_TAXA_PERFM` ~84% vazia, com sentinelas `1900-01-01`/`1901-01-01`
      devolvidas como publicadas.
- [x] **META = `meta_perfil_mensal_fi.txt`**, `.txt` solto e **único arquivo do `META/`** (medido
      pela listagem); as outras 3 grafias dão **404**.

## Controles negativos — 4, todos vermelhos, restore verificado

| mutação | falhas |
|---|---|
| declarar `CPF_CNPJ_COMITENTE_1` como coluna de CNPJ | **2** |
| derivar o contrato pré-175 do bloco-chave pós-175 (a armadilha de cópia) | **4** |
| tirar `DT_COTA_TAXA_PERFM` das date cols | **2** |
| alargar a janela pós-175 para engolir o regime pré-175 | **1** |

Restore por **cópia de snapshot** com `diff` conferido nas 3 vias a cada rodada; baseline
re-medido entre as mutações (2866 antes e depois). Cada mutação **assertou a própria precondição e
imprimiu o que mudou** — uma mutação aplicada a 0 ocorrências é indistinguível de um sobrevivente.

## Erros meus, pegos por medição

- [x] **Afirmei que a META vinha em LF, não CRLF.** Falso — o probe testava a string literal
      `\r\n` (backslash duplo dentro de f-string), não CR-LF. Refeito contra o parser real: 107
      registros, CRLF como as outras 46. **Quase virou "achado" documentado.**
- [x] **Escrevi "série a partir de 202001" no `CLAUDE.md`** quando o medido é **201901**. Corrigido
      antes do commit.
- [x] **Assertei `is_datetime64_any_dtype` nas date cols** e o teste ficou vermelho: este repo coage
      para `datetime.date` **puro**, então a coluna populada é `object` — mesmo dtype do texto. O
      invariante que de fato distingue é o **valor ser um `datetime.date`**, que texto nunca produz.
      ⚠️ O teste de coluna vazia **passava** com a asserção errada: uma coluna toda em branco vira
      `datetime64`/NaT de qualquer jeito. Reescrito com **uma linha vazia e uma preenchida**.

## Aberto

- [ ] Release **PATCH** ao mergear (há diff em `src/`).

Completed — kept as a record.

## fi-balancete-reader-281_20261030_215717

# FI Balancete reader (#281) -- work ledger

## Measured (not assumed)

- [x] Series: 141 monthly ZIPs `201501`-`202609` in the directory; CKAN lists only the last 12.
- [x] Each ZIP has 1 member `balancete_fi_AAAAMM.csv`; `;`, CRLF, no quotes, pure ASCII, 0 ragged rows.
- [x] Headers: 5 cols `CNPJ_FUNDO` through `202310`; 6 cols `TP_FUNDO_CLASSE`+`CNPJ_FUNDO_CLASSE` from `202311` (every month 202302-202312 checked). Not the RCVM 175 / Perfil Mensal `202312` cut.
- [x] `VL_SALDO_BALCTE`: always 2 decimals, negatives present, no comma/sci; `CD_CONTA_BALCTE` 8 chars; dates ISO; CNPJ 100% pontuado/valid.
- [x] 201501 has 22 rows with empty account code and balance; later months sampled have none.

## Implemented

- [x] Contracts `BALANCETE_FI`, `BALANCETE_FI_PRE202311`, pinned to verbatim headers.
- [x] `BalanceteFiReader`, `BalanceteFiPre202311Reader`, `MetaBalanceteFiReader`; registered up to `fi/`.
- [x] `_META_MEMBERS`, `_META_UNDESCRIBED_READERS`, `_IMPLEMENTED_PACKAGES`.
- [x] META counts 48 -> 49, public surface 290 -> 293.
- [x] Docs page, nav, api.md, CLAUDE.md catalog and layout.
- [x] Unit tests; full unit+integration suite green.

## Open

- [ ] PR review and merge (orchestrator).

## fi-doc-eventual-reader-193_20260802_144422

# FI/DOC/EVENTUAL — índice dos documentos eventuais — #193

Branch: `feat/193-fi-doc-eventual-reader` · Issue: #193 · Fecha o item `fi-doc-eventual` do
inventário do #122.

Primeiro dataset novo sob o portal root `fi/` desde a lâmina. **Não** é root novo.

## Feito

- [x] Grounding contra os bytes reais (2025) — cols, linhas, ragged, e classificação de **toda**
      coluna por valor. META consultada como **oráculo de tipo**.
- [x] Fixture header-only verbatim + contract **gerado do header** (nunca transcrito).
- [x] `EventualFiReader` + `MetaEventualFiReader` (43º) sobre a infraestrutura existente — zero
      infraestrutura nova (molde `DfinFiiReader`: CSV solto anual + índice de documentos).
- [x] Registro nos **3** `__init__` da cadeia (`fi/doc/eventual/` → `fi/doc/` → `fi/`) + os **2**
      contracts em `contracts/__init__.py` (o de dados e o de META).
- [x] `bin/check_contract_drift.py`: entrada em `_META_MEMBERS` **e** em `_UNEXPOSED_CONTRACTS`
      (o reader declara o contract inline, como o `DfinFiiReader`).
- [x] **Contagens conferidas, não incrementadas:** **239 readers** (era 237), **43 Meta readers =
      17 `.txt` + 26 `.zip`**, 244 contracts exportados, 22 roots.
- [x] 14 testes novos; suíte **2411** unit (+18) + 4 integration.
- [x] Docs: página nova `docs/ingestion/eventual_fi.md` + `nav`, `docs/api.md`,
      `docs/ingestion/meta.md`, `CLAUDE.md` raiz.

## Medições (2025, bytes reais)

**CSV solto** (não ZIP), **particionado por ano**, série ao menos **2020–2026** (todos 200).
**11 colunas, 186.453 linhas, 50,91 MB**, nenhuma linha ragged.

1 coluna de CNPJ (`CNPJ_FUNDO_CLASSE`, **100% válido**), 2 de data (`DT_COMPTC`, `DT_RECEB`, 100%
ISO). Nomenclatura **pós-RCVM 175**.

## ⚠️ O achado principal — 7 colunas iguais, 0 nomes iguais

`eventual_fi_AAAA.csv` e `dfin_fii_AAAA.csv` são **o mesmo tipo de artefato**: índice anual, CSV
solto, dos documentos que um fundo entregou. Sete colunas significam exatamente a mesma coisa e
**nenhuma se chama igual**:

| significado | EVENTUAL | DFIN FII |
|---|---|---|
| tipo do fundo/classe | `TP_FUNDO_CLASSE` | `Tipo_Fundo_Classe` |
| CNPJ | `CNPJ_FUNDO_CLASSE` | `CNPJ_Fundo_Classe` |
| denominação | `DENOM_SOCIAL` | `Nome_Fundo_Classe` |
| data de referência | `DT_COMPTC` | `Data_Referencia` |
| data de entrega | `DT_RECEB` | `Data_Entrega` |
| link | `LINK_ARQ` | `Link_Download` |
| parecer | `RESULTADO_AUDITORIA` | `Parecer_Auditor` |

Escrever o contrato **por analogia** erraria **as 11 colunas** parecendo perfeitamente razoável.
Anti-cópia pinada nas 2 direções.

## Outras armadilhas honradas

- **`ID_DOC` é `int` na META e fica `str`** — identificador não é quantidade; um numérico apaga
  zero à esquerda em silêncio (precedente `Codigo_CVM` do CGVN, publicado `001023`).
- **4 colunas parcialmente vazias** (`ID_SUBCLASSE` 96,8%, `RESULTADO_AUDITORIA` 83,5%, `ID_DOC`
  75,6%, `NM_ARQ` 24,4%) — dependem do tipo de documento. Vazio volta vazio, sem placeholder.
- **META é `.txt` solto**; as outras 3 grafias do portal dão **404**. E os 11 campos vêm em **ordem
  alfabética**, que não é a do arquivo — header é a fonte da ordem, META a do tipo.
- **`LINK_ARQ` aponta para o *fundosweb***, host **diferente** do RAD usado pelo IPE/CGVN.

## Controles negativos (3 mutações, todas vermelhas)

Baseline **14 passed**, re-medido entre as mutações. **Restore por cópia de snapshot, nunca
`git checkout`** — os arquivos novos são untracked e o `git checkout` abortaria inteiro, deixando
as mutações acumuladas (a armadilha medida no #190).

- [x] Renomear as 4 colunas paralelas para a grafia do irmão DFIN → **11 falhas**.
- [x] Tirar `DT_RECEB` de `_DATE_COLS` → **1 falha**.
- [x] Honrar o `int` da META para `ID_DOC` → **1 falha**.

As duas contagens `1` são **achado, não fraqueza**: cada um desses fatos tem **exatamente uma**
defesa, então nenhum outro teste os cobre por acidente.

## ⚠️ Deriva de contagem encontrada de passagem

O `CLAUDE.md` raiz **discordava de si mesmo**: o texto dizia "42 readers" e o parêntese dos
"números MEDIDOS" logo abaixo dizia `38 = 16 .txt + 22 .zip`. **Re-medi do código** em vez de
incrementar (`43 = 17 + 26`, 44 nomes `META_*` = 43 contracts + `META_COLUMNS`) e corrigi os dois,
acrescentando a instrução de re-medir. Esse arquivo continua **fora** do gate de docs (#161).

## Aberto / próximo

- [ ] **Release PATCH** ao mergear (`feat`, `src/` muda).
- [ ] Depois: **DFP** (12,12 MiB) → **ITR** (30,14) → `EVENTOS/RECOMPRA_ACOES`.
- [ ] #192 (backfill dos testes dos 3 `bin/check_*` sem cobertura) segue em Ready.

## fix-perfil-mensal-4dp-245_20261029_120000

# Perfil Mensal Q13-15 com quatro casas decimais (#245)

Branch: `fix/perfil-mensal-4dp-245` · Issue: #245

## Por que existe

O padrao CVM Perfil V4 define `VAR_DIAR_PERC_PATRIM_FDO_VAR_N_TAXA_ANUAL`,
`VAR_DIAR_PERC_PATRIM_FDO_VAR_N_TAXA_CAMBIO` e `VAR_PATRIM_FDO_N_PRECO_ACOES` como "Numerico com
quatro casas decimais" (confirmado na pagina `PadraoXMLPerfilV4.asp`). O schema os declarava como
`TwoDecimalField` e o writer os renderizava com 2 casas, truncando valores em silencio.

## Feito

- [x] Reproduzido em `origin/main` (schema linhas 310-312 e writer com escala `2`).
- [x] `FourDecimalField` (4 casas, `ROUND_DOWN`, sem teto de digitos inteiros nem restricao de sinal) ao
  lado de `TwoDecimalField`. `VarPercentPlField` nao serve: carrega `max_digits=14`, teto
  especifico de `VAR_PERC_PL`.
- [x] Os 3 campos usam `FourDecimalField`; as 3 tags renderizam com 4 casas.
- [x] Testes: truncamento (positivo e negativo) e XML renderizado, por campo; Q12 segue com 2 casas.
- [x] Mutacao: revertendo a fonte, 18 dos testes novos falham; restaurada e verificada por sha256.
- [x] `docs/submission/perfil_mensal.md` atualizado.
- [x] Gates de pre-commit.

## Fora do escopo (achado)

`VAL_PERCENT_OUTROS` (`VarOutros.val_percent_outros`) tambem e "quatro casas decimais" na pagina
da CVM e segue como `TwoDecimalField`. Nao listado na #245; fica para issue propria.

Completed — kept as a record.

## fix-perfil-mensal-outros-4dp-256_20261029_130000

# Perfil Mensal VAL_PERCENT_OUTROS com quatro casas decimais (#256)

Branch: `fix/perfil-mensal-outros-4dp-256` · Issue: #256 · Sequel de #245 / PR #255

## Por que existe

A pagina `PadraoXMLPerfilV4.asp` descreve `VAL_PERCENT_OUTROS` como "Numerico com quatro casas
decimais". O schema o declarava `TwoDecimalField` e o writer renderizava com 2 casas, truncando
valores em silencio.

## Feito

- [x] Reproduzido em `origin/main` (schema `VarOutros.val_percent_outros`, writer com escala `2`).
- [x] Pagina da CVM lida (ISO-8859-1): quatro casas confirmadas.
- [x] `val_percent_outros` usa `FourDecimalField`; a tag renderiza com 4 casas.
- [x] Testes: truncamento (positivo, negativo, `0.99999`) e XML renderizado (`2` -> `2,0000`).
- [x] Mutacao: revertendo a fonte, os testes novos falham; restaurada e verificada por sha256.
- [x] `docs/submission/perfil_mensal.md` atualizado.
- [x] Gates de pre-commit.

Completed — kept as a record.

## ingestion-cad-fi-hist_20260710_030000

# Work ledger — CAD/FI histórico readers (19 change-logs)

Branch `feat/ingestion-cad-fi-hist-reader` · **user-prioritised follow-up** · part of the
[kanban sweep](kanban-ready-backlog-sweep_20260708_220638.md).

## Scope

`cad_fi_hist.zip` ships **19 members**, one per mutable attribute of the legacy CAD/FI registry —
each a per-attribute **change-log** (`CNPJ_FUNDO`, `DT_REG`, value column(s), `DT_INI_*`/`DT_FIM_*`).
Where `CadastroFiReader` gives the current snapshot, these give the history.

## Design decisions (user-approved)

- **19 separate reader classes** (user chose "19 separate readers" over a parameterized reader or a
  curated subset), one public class per file per repo convention → 19 `CadastroFiHist*Reader`.
- **Private shared base `_base_cad_fi_hist_reader.py`** holds the download → unzip → find_member →
  read_table logic once (DRY); each public reader is a ~10-line subclass setting `_MEMBER`,
  `_CONTRACT`, `_DATE_COLS`, `_LABEL`. This is the first reader in the repo to use a shared base —
  justified because 19 near-identical readers would otherwise duplicate the same body 19×.
- **Contracts consolidated into ONE module** `_internal/config/contracts/cad_fi_hist.py` (19
  `FileContract` constants). **Deliberate deviation** from the "one contract per file" convention:
  the 19 are members of a *single* input artifact (one ZIP, one dataset page) and a uniform family;
  19 one-constant modules would be sprawl. Noted in the module docstring. **Flag for review** — the
  registro readers used one file per member (3 files); this diverges because 19 ≫ 3 and they are
  attributes of one entity, not distinct entities.
- Snapshot (no `AAAAMM`) → **no `date_ref`**; a change-log has many rows per fund → **no grain**.

## Findings from the real artifact

- [x] 19 members, all fixed-width under `QUOTE_NONE` (safe, not load-bearing here).
- [x] Uniform prefix `CNPJ_FUNDO; DT_REG; …`; every `DT_*` column parses; `CNPJ_FUNDO` never null.
- [x] Row counts range from 42,984 (`publico_alvo`) to 489,195 (`exerc_social`).
- [x] `taxa_adm` / `taxa_perfm` have an opening date but **no** `DT_FIM_*`; `exerc_social` has no
  non-date value column beyond the keys. Contracts capture these per-member shapes exactly.
- [x] `gestor.CPF_CNPJ_GESTOR` holds a CPF for PF managers → excluded from CNPJ validation.

## Shipped

- [x] `_internal/config/contracts/cad_fi_hist.py` — 19 `FileContract`s; re-exported from `__init__`
- [x] `ingestion/_base_cad_fi_hist_reader.py` — private base
- [x] 19 `ingestion/cad_fi_hist_*.py` readers; exported from `ingestion/__init__` + package `__all__`
- [x] `tests/unit/test_cad_fi_hist_ingestion.py` — one parameterized module, 81 tests over all 19
- [x] Docs: combined `docs/ingestion/cad_fi_hist.md`, `ingestion/index.md`, `api.md`, `mkdocs.yml`
- [x] Root `CLAUDE.md` catalog: `cad_fi_hist.zip` marked ✅

## Verification

- [x] 204 unit tests green under **pandas 3.0.3 and 2.3.3**. Ruff check + format,
  `bin/check_typing.py` clean.
- [x] **End-to-end against the live archive:** `sit` 143,392×5, `gestor` 98,567×7 (CPF present),
  `taxa_adm` 87,757×5 (str), `exerc_social` 489,195×4; dates coerced; a single `path_raw` kept the
  ZIP + all 19 CSVs.

## Open

- [x] **PR #43** opened; awaiting user review/merge + release.
- [ ] **Next to-do is #42** (provenance `url` + `updated_at` on every reader) — will retrofit these
  19 too.

## ingestion-cadastro-fi-reader_20260710_001500

# Work ledger — #9 Cadastro de Fundos (CAD/FI) ingestion reader

Branch `feat/ingestion-cadastro-fi-reader` · issue **#9** · part of the
[kanban sweep](kanban-ready-backlog-sweep_20260708_220638.md).

## Scope

`CadastroFiReader` reads `cad_fi.csv` — the CVM fund registry — into a typed, contract-validated
DataFrame. 46,809 rows × 41 columns.

Issue #9 points at stpstone's `CvmFIFCADFI`. Per the "class names lie, read the URL" rule its URL
was checked first: `https://dados.cvm.gov.br/dados/FI/CAD/DADOS/cad_fi.csv` — matching the issue.

## Findings from the real artifact

- [x] **Not a ZIP, not month-partitioned.** A bare 18 MB `.csv` at a fixed URL. CVM overwrites it
  in place. → the reader takes **no `date_ref`**, the first in this library not to.
- [x] Header read off the real file: **41 columns**, 46,809 data rows.
- [x] **No unique key, at any combination tried:**

  | Key | Duplicated rows |
  |---|---|
  | `CNPJ_FUNDO` | 10,947 |
  | `(CNPJ_FUNDO, TP_FUNDO)` | 1,027 |
  | `(CNPJ_FUNDO, CD_CVM)` | 843 |
  | `(CNPJ_FUNDO, TP_FUNDO, DT_REG)` | 851 |
  | `CD_CVM` | 18,535 |

  Cause: a fund **keeps its CNPJ** across regulatory-regime migrations and is re-registered under a
  new `TP_FUNDO` with a fresh `CD_CVM`. Confirmed on `00.000.432/0001-00`: a `FIF` registered
  2003-04-30 and an `FI` registered 2005-03-31, both `CANCELADA`. 46,809 rows ↔ 41,106 distinct
  CNPJs.
- [x] **99.5% historical.** `SIT == "CANCELADA"` on 46,569 rows; 46,570 carry a `DT_CANCEL`; only
  22 are `EM FUNCIONAMENTO NORMAL`. `TP_FUNDO` is full of legacy types (`FACFIF`, `FITVM`, `FIF`).
  Sanity-checked against a raw row to rule out a column-misalignment misparse — it is real. The
  live funds live in `registro_fundo_classe.zip` (post-RCVM 175).
- [x] `CPF_CNPJ_GESTOR` holds a **CPF** on the 47 rows where `PF_PJ_GESTOR == "PF"`.
- [x] All nine `DT_*` columns parse cleanly; blanks (20,282 for `DT_INI_ATIV`) become `NaT`.
- [x] `QUOTE_MINIMAL` and `QUOTE_NONE` agree here (both 41 fields on all 46,810 lines) — unlike
  `lamina_fi_*.csv`. `QUOTE_NONE` is kept for consistency with the sibling readers, but it is not
  load-bearing on this file.

## Decisions

- [x] **No `date_ref` in the constructor**, and a test asserts passing one raises `TypeError`
  rather than being silently ignored — a caller who thinks they are selecting a month would
  otherwise get today's registry and never know.
- [x] **Assert no grain, do not de-duplicate.** Choosing the "current" row per CNPJ (latest
  `DT_REG`? `SIT != "CANCELADA"`?) is a domain decision for the consumer. A reader's job is to
  return what CVM published. Documented loudly, because `set_index("CNPJ_FUNDO")` or a merge on
  that column alone silently fans out rows.
- [x] **`CPF_CNPJ_GESTOR` is not declared a CNPJ column.** A CNPJ check would reject a valid
  registry. The counterparty columns (`CNPJ_ADMIN`, `CNPJ_AUDITOR`, …) are likewise excluded:
  validating them would conflate a defect in *this* file with a defect in a counterparty's
  registration.
- [x] Contract declares all 41 columns required; dtype map derived from it, so the names live in
  one place.
- [x] Default `int_timeout_s=60` (vs 30 for the monthly readers) — the file is ~18 MB, unzipped.
- [x] Scope held to `cad_fi.csv`. `cad_fi_hist.zip` and `registro_fundo_classe.zip` filed as
  follow-ups, as #6 did with `cda_fie`.

## Shipped

- [x] `_internal/config/contracts/cad_fi.py` — `CAD_FI` (41 required columns)
- [x] `contracts/__init__.py` re-export
- [x] `ingestion/cadastro_fi.py` — `CadastroFiReader`
- [x] Exported from `ingestion/__init__.py` and the package `__all__`
- [x] `tests/unit/test_cadastro_fi_ingestion.py` — 12 tests
- [x] Docs: `docs/ingestion/cadastro_fi.md`, `ingestion/index.md`, `api.md`, `mkdocs.yml` nav
- [x] Root `CLAUDE.md` catalog: new CAD/FI entry (open-data only, no submission XML standard)

## Verification

- [x] 89 unit tests green under **pandas 3.0.3 and pandas 2.3.3**. Ruff check + format,
  `bin/check_typing.py` clean.
- [x] **End-to-end against the live CVM file:** 46,809 × 41 and 41,106 distinct CNPJs, both
  matching independent raw counts; `DT_REG` → `date`; 20,282 null `DT_INI_ATIV`; no fabricated
  `"nan"`; `path_raw` kept `cad_fi.csv`.

## Open

- [ ] PR opened; awaiting user review/merge.
- [ ] `registro_fundo_classe.zip` is likely the artifact consumers actually want for live funds —
  worth raising with the user as a priority follow-up, not just a backlog line.

## ingestion-cda-reader_20260708_155557

# Work ledger — ingestion: CDA FIF reader (issue #6)

Branch: `feat/ingestion-cda-reader`. Excluded from the docs site (`backlog/`).
Part of the sweep tracked in `kanban-ready-backlog-sweep_20260708_220638.md`.

## Done

- [x] **CDA reader** — `ingestion/cda.py` (`CdaReader`): downloads the monthly CVM open-data dump
  (`cda_fi_AAAAMM`), reads the eight asset blocks (`BLC_1`…`BLC_8`) through `read_table`
  (text-first, shared contract, `DT_COMPTC`→date), tags each with a `BLOCO` column, concatenates
  them (`sort=False`, union of columns), then **left-joins** `PL`'s `VL_PATRIM_LIQ` on
  `(TP_FUNDO_CLASSE, CNPJ_FUNDO_CLASSE, DT_COMPTC)` with `validate="many_to_one"`. Money/quantity
  columns kept as `str` (lossless).
- [x] **Grain decision (revised mid-branch).** The original plan — stack all ten members, union of
  columns — was **rejected** after inspecting the real `cda_fi_202504.zip`: `BLC_*` is one row per
  *asset*, `PL` is one row per *fund*. Stacking them yields a mixed-grain frame that passes any
  column contract yet double-counts under `groupby().sum()`. Joining PL on as a column keeps one
  grain and makes `VL_MERC_POS_FINAL / VL_PATRIM_LIQ` (the *diversificação* half) computable.
- [x] **`cda_fie` excluded.** The archive ships a tenth member with a distinct FIE layout (its own
  `ID_DOC`, inline `VL_PATRIM_LIQ`, exterior-asset columns). Skipped, not forced into the frame.
  Follow-up issue noted in the sweep ledger.
- [x] **Contract** — `_internal/config/contracts/cda_fif.py` (`CDA_FIF`): the columns every member
  shares. Verified against the real dump — the draft was missing `DENOM_SOCIAL`. CNPJ arrives
  masked (`00.071.477/0001-68`); `unmask_cnpj` handles it. Re-exported from `contracts/__init__.py`.
- [x] **Unmatched-PL policy: warn, don't raise.** A holdings row whose fund is absent from `PL`
  gets a null `VL_PATRIM_LIQ` — contract-valid, correctly typed, and silently `NaN` in every
  ratio. `_check_pl_coverage` logs one `warning` naming up to 5 CNPJs and returns the frame, so a
  single bad fund does not cost the caller the month's other ~25k good rows. Empirically the join
  was total for 2025-04 (all 25,281 holdings keys matched), so a warning means a malformed dump or
  a CVM layout change — and the message names concrete funds for a log-sniffing routine to act on.
- [x] **Raw-artifact seam** — `_internal/utils/raw_workspace.py`: shared context manager giving
  every reader an optional `path_raw`. `None` → temp dir, discarded; a path → created (parents
  included) and the untouched `.zip` + extracted CSVs **kept**, before any parsing. Retrofitted
  onto `InformeDiarioReader` (#5) in the same commit, and documented on the `IngestionReader` port.
  Generalised as the BlueprintX python-common lesson `ingestion-reader-persists-raw-artifact.md`.
- [x] **Public API** — export `CdaReader` from `ingestion/__init__.py` and `filings_cvm/__init__.py`.
- [x] **Tests** — `tests/unit/test_cda_ingestion.py` (16) + `tests/unit/test_raw_workspace.py` (4)
  + 2 new persistence tests on the Informe Diário reader. Boundary-mocked download of a fixture ZIP
  with two *differently-shaped* blocks, so the column union is genuinely exercised; PL join,
  coverage warning, `MergeError` guard, `fie` exclusion, and raw persistence all covered.
- [x] **Docs** — new `docs/ingestion/cda.md`; updated `ingestion/index.md` (incl. a `path_raw`
  section), `ingestion/informe_diario.md`, `api.md`, `mkdocs.yml` nav, root `CLAUDE.md` catalog.

## Also on this branch (doc-convention fixes surfaced mid-#6)

- [x] Fix the #5 backlog ledger to checkbox format and mark it "Completed — kept as a record"
  (per lesson `branch-work-ledger-in-docs-backlog`, which this repo's `docs/CLAUDE.md` had not
  yet adopted — the template flip never reached this already-scaffolded repo).
- [x] Update `docs/CLAUDE.md`: checkbox format + keep-on-completion (was "delete once done").

## Gates

- [x] `ruff check` / `ruff format --check` clean (three `ERA001` prose false-flags reworded — see
  the known lesson `ruff-era001-prose-noise`).
- [x] `mypy src` clean · `bin/check_typing.py` clean.
- [x] 45 unit + 4 integration tests pass.

## Open / follow-up

- [ ] Open PR closing #6, then continue the sweep from #7.
- [ ] `cda_fie` reader — its own issue (see the sweep ledger).

**Completed — kept as a record.**

## ingestion-informe-diario-reader_20260708_145022

# Work ledger — ingestion: Informe Diário FIF reader (issue #5)

Branch: `feat/ingestion-informe-diario-reader` (merged as PR #34). Excluded from the docs site
(`backlog/`). **Completed — kept as a record.**

## Done

- [x] **First ingestion reader** — `ingestion/informe_diario.py` (`InformeDiarioReader`): downloads
  the monthly CVM open-data dump (`inf_diario_fi_AAAAMM`), extracts the CSV, validates the
  contract, returns a typed `DataFrame`. Built on this repo's own seams (`download_file`,
  `zip_extractor`, `read_table`, `LogEmitter`), not stpstone's framework. Money kept as `str`
  (exact), `NR_COTST` as `Int64`, `DT_COMPTC` as `date`.
- [x] **Contract** — `_internal/config/contracts/informe_diario_fif.py` (`INFORME_DIARIO_FIF`),
  re-exported from `contracts/__init__.py`.
- [x] **Macro-section ports** (user request) — `_internal/ports/` (renamed from `interfaces/` per
  user; hexagonal ports-and-adapters): `SubmissionWriter[TDoc]` (abstract `export`) and
  `IngestionReader` (abstract `read`). Both private ABCs (`ABCTypeCheckerMeta`), not in any public
  `__all__`.
- [x] **Submission generalised** (user request) — `to_xml` → `export` on `InformeDiario` /
  `PerfilMensal`; both now inherit `SubmissionWriter[...]` and drop the explicit
  `metaclass=TypeChecker` (inherited). Existing submission tests updated.
- [x] **Root-cause seam fix** — `tabular_reader.read_table` now reads files as text (`dtype=str`)
  and lets `apply_dtypes` do all coercion, instead of inferring-then-casting (which lost
  zero-padding and decimal precision). Regression test in `tests/unit/test_tabular_reader.py`.
- [x] **Tests** — `tests/unit/test_informe_diario_ingestion.py` (boundary-mocked download; contract
  + typing exercised for real), `tests/unit/test_tabular_reader.py`. 23 unit tests pass; ruff,
  ruff-format, and `bin/check_typing.py` clean.
- [x] **Docs** — `docs/ingestion/informe_diario.md` (new page) + `ingestion/index.md`, `usage.md`,
  `api.md`, `README.md`, `mkdocs.yml` nav, and `CLAUDE.md` (catalog + layout + ports note)
  updated. `to_xml`→`export` across all docs.
- [x] **BlueprintX lessons** captured (global store + this repo's `docs/blueprintx-lessons.md`):
  `tabular-reader-read-as-text-not-infer`, `ports-package-for-section-interfaces`.

## Open / follow-up

- [ ] **BlueprintX template backport** (guarded — not done here): apply both lessons to
  `~/github/blueprintx/templates/` in their own dotfiles/blueprintx PRs — the `read_table`
  read-as-text fix and the `_internal/ports/` package + `example_port.py`.
- [ ] Remaining kanban "Ready" ingestion readers #6–#14, one PR each. (#6 CDA in progress.)

## ingestion-lamina-carteira-reader_20260709_194646

# Work ledger — #7 Lâmina carteira FIF ingestion reader

Branch `feat/ingestion-carteira-reader` · issue **#7** · part of the
[kanban sweep](kanban-ready-backlog-sweep_20260708_220638.md).

## What the issue asked vs. what the artifact is

Issue #7 is titled "Carteira / Portfolio composition reader" and points at stpstone's
`CvmFIFPortfolio`. Reading that class showed its URL is **not** CDA — it downloads
`lamina_fi_AAAAMM.zip` and reads the `lamina_fi_carteira_AAAAMM.csv` member. So #7 is the
**Lâmina's allocation-by-asset-type table**, not a second CDA reader, and it is *not* a
duplicate of the already-merged #6.

Named `LaminaCarteiraReader` (module `ingestion/lamina_carteira.py`) rather than
`CarteiraReader`, per user decision: "carteira" alone is ambiguous — CDA is also a carteira,
and #8's `LaminaReader` will read a sibling member of this very ZIP.

## Findings from the real artifact (`lamina_fi_202504.zip`)

- [x] Header read off the real file, never from memory: seven columns —
  `TP_FUNDO_CLASSE;CNPJ_FUNDO_CLASSE;ID_SUBCLASSE;DENOM_SOCIAL;DT_COMPTC;TP_ATIVO;PR_PL_ATIVO`.
- [x] Grain is unique on (fund, subclasse, date, `TP_ATIVO`) — 0 duplicates across 4,474 rows.
- [x] `DT_COMPTC` holds a single date per file (`2025-04-30`).
- [x] `ID_SUBCLASSE` is **empty on all 4,474 rows**. Declared in the contract anyway, so its
  eventual arrival is a value change rather than a schema break.
- [x] **`PR_PL_ATIVO` does not sum to 100.** Per-fund totals ran -37.08 → 1123.00 (median
  100.03) across 1,246 funds — leverage and short exposure. A "shares total 100%" validation
  would have rejected valid funds; **deliberately not asserted.** This is why the contract was
  grounded in the artifact instead of in intuition.
- [x] 141 rows carry a negative share; kept verbatim.

## Decisions

- [x] `PR_PL_ATIVO` stays `str` (exact CVM decimal text), like every money/quantity column in
  the library. A percentage feeding a weighted aggregate drifts under float just like a price.
- [x] Member matched on the prefix `lamina_fi_carteira_`, not `lamina_fi_` — the latter also
  prefixes `lamina_fi_202504.csv` and both `lamina_fi_rentab_*` members. A test pins this.
- [x] `path_raw` persists the ZIP **and every extracted CSV**, not just the member read, so
  #8's reader can replay the same bytes.
- [x] No shared "pick a member from the archive" helper extracted yet. Three readers now have a
  small selection loop each; the right time to factor it out is #8, when two readers share one
  archive. (YAGNI.)

## Shipped

- [x] `_internal/config/contracts/lamina_carteira_fif.py` — `LAMINA_CARTEIRA_FIF`
- [x] `contracts/__init__.py` re-export
- [x] `ingestion/lamina_carteira.py` — `LaminaCarteiraReader`
- [x] Exported from `ingestion/__init__.py` and the package `__all__`
- [x] `tests/unit/test_lamina_carteira_ingestion.py` — 13 tests
- [x] Docs: `docs/ingestion/lamina_carteira.md`, `ingestion/index.md`, `api.md`, `mkdocs.yml` nav
- [x] Root `CLAUDE.md` catalog: Lâmina entry now marks the ingestion carteira reader ✅

## Verification

- [x] 58 unit tests green (13 new); `ruff check` + `ruff format` clean; `bin/check_typing.py` clean.
- [x] **End-to-end against the live CVM file**, not only mocks: 4,474 rows, contract validated,
  dtypes as declared, `DT_COMPTC` coerced to `date`, 141 negative shares preserved, and
  `path_raw` kept the `.zip` plus all four CSVs.

## Bug found by CI, fixed at the root (not in the test)

- [x] CI failed on all three OSes: `test_read_tolerates_an_empty_id_subclasse` saw the literal
  string `"nan"` where a missing value belonged. **Not a flake, and not a test bug.**
- [x] Root cause in the shared seam `_internal/utils/dtypes.py`: `astype("str")` stringifies NA
  into the three-character text `"nan"` on **pandas < 3**. pandas 3 added a real `str` dtype that
  preserves NA. `poetry.lock` legitimately carries **both** (2.3.3 and 3.0.3, keyed by Python
  marker), so the same declaration produced different *data* per interpreter. Local pandas 3.0.3
  masked it entirely.
- [x] Fix: `apply_dtypes` normalises a `"str"` declaration to pandas' nullable `"string"` dtype,
  which behaves identically on 2 and 3; elements stay ordinary `str`. One guard in the function
  every reader routes through — `InformeDiarioReader.ID_SUBCLASSE` had the same latent corruption.
- [x] New `tests/unit/test_dtypes.py` (6 tests) pins it; the seam had no test of its own before.
- [x] Verified on **both** majors: 64 unit tests green under pandas 3.0.3 *and* under a
  pandas 2.3.3 venv. Reproduced the old behaviour explicitly first
  (`Series([nan]).astype("str") -> ['nan']`, `isna() -> False`).

Lesson (generalizable → BlueprintX store): a green suite on one pandas major proves nothing about
the other when the lock ships two.

## Open

- [ ] PR opened; awaiting user review/merge.
- [ ] #8 will read `lamina_fi_AAAAMM.csv` from this same archive — revisit the member-selection
  duplication then.

## ingestion-lamina-reader_20260709_213000

# Work ledger — #8 Lâmina FIF (fact sheet) ingestion reader

Branch `feat/ingestion-lamina-reader` · issue **#8** · part of the
[kanban sweep](kanban-ready-backlog-sweep_20260708_220638.md).

## Scope

`LaminaReader` reads `lamina_fi_AAAAMM.csv` — the lâmina proper — from `lamina_fi_AAAAMM.zip`,
the **same archive** `LaminaCarteiraReader` (#7) already downloads. One row per fund class,
78 columns: objective, investment policy, fees, redemption terms, five-year performance,
worked cost examples, SAC contacts.

## Findings from the real artifact (`lamina_fi_202504.zip`)

- [x] Header read off the real file: **78 columns**, 1,324 data rows.
- [x] Grain unique on `(TP_FUNDO_CLASSE, CNPJ_FUNDO_CLASSE, ID_SUBCLASSE, DT_COMPTC)` — 0 dupes.
- [x] `DT_COMPTC` holds a single date per file (`2025-04-30`).
- [x] `ID_SUBCLASSE` is populated on **5 of 1,324** rows — unlike the carteira member, where it is
  empty on every row. Subclasses do exist here.
- [x] All four `DT_*` columns parse cleanly; blanks (77 rows for the two `*_DESPESA` columns,
  28 for `DT_INI_ATIV_5ANO`) become `NaT`.
- [x] **`QUOTE_NONE` is load-bearing, not incidental.** Free-text fields (`OBJETIVO`,
  `POLIT_INVEST`, `TAXA_ADM_OBS`) contain stray *unbalanced* `"` characters. Measured on the real
  file:
  - default `QUOTE_MINIMAL` → 1,318 records, histogram `{78: 1316, 142: 1, 79: 1}` → pandas raises
    `ParserError: Expected 78 fields in line 613, saw 142`.
  - `QUOTE_NONE` → all 1,325 lines at exactly 78 fields.

  CVM emits no quoting at all and the delimiter never appears inside a field, so honouring quotes
  is simply wrong for these dumps. This validates the existing repo convention rather than adding
  one.

## Decisions

- [x] **Contract declares all 78 columns as required**, not just the keys. This is a single-layout
  member, so a column CVM drops or renames must fail loudly at read time instead of surfacing as a
  `KeyError` deep in a consumer's transform. Extra columns are still tolerated.
- [x] **Dtype map derived from the contract** (`{c: "str" for c in LAMINA_FIF.tuple_required if c
  not in _DATE_COLS}`) rather than retyped. The 78 names live in exactly one place, and a column
  added to the contract cannot be silently left untyped. A test pins that the two sets partition
  the contract.
- [x] Money, percentage, and day-count columns stay `str` (exact CVM decimal text), per the sweep's
  standing decision.
- [x] **Took the dedup deferred in #7.** `zip_extractor.find_member(list_members, str_name)` now
  serves both Lâmina readers, and `LaminaCarteiraReader` was refactored onto it.
  - Selection is by **exact file name, never a prefix**: `lamina_fi_AAAAMM.csv` is a strict prefix
    of `lamina_fi_carteira_AAAAMM.csv` *and* both `lamina_fi_rentab_*_AAAAMM.csv`. A `startswith`
    match would return whichever member the archive happened to list first. The caller knows the
    reference month, so it can name the member exactly.
  - This *tightened* #7 too: its prefix match was correct only by accident of the longer literal.

## Shipped

- [x] `_internal/config/contracts/lamina_fif.py` — `LAMINA_FIF` (78 required columns)
- [x] `contracts/__init__.py` re-export
- [x] `_internal/utils/zip_extractor.py` — new `find_member`
- [x] `ingestion/lamina.py` — `LaminaReader`
- [x] `ingestion/lamina_carteira.py` — refactored onto `find_member`
- [x] Exported from `ingestion/__init__.py` and the package `__all__`
- [x] `tests/unit/test_lamina_ingestion.py` — 13 tests (incl. the stray-quote regression)
- [x] Docs: `docs/ingestion/lamina.md`, `ingestion/index.md`, `api.md`, `mkdocs.yml` nav
- [x] Root `CLAUDE.md` catalog: Lâmina entry marks the fact-sheet reader ✅

## Verification

- [x] 77 unit tests green under **pandas 3.0.3 and pandas 2.3.3** — the dual-major check that #7's
  CI failure taught. Ruff check + format, `bin/check_typing.py` clean.
- [x] **End-to-end against the live CVM file:** 1,324 × 78, matching an independent raw count;
  `DT_COMPTC` → `date`; 77 null `DT_INI_DESPESA`; 5 populated `ID_SUBCLASSE`; no fabricated
  `"nan"`; `path_raw` kept the `.zip` and all four CSVs.

## Open

- [ ] PR opened; awaiting user review/merge.
- [ ] `lamina_fi_rentab_ano_*` and `lamina_fi_rentab_mes_*` are the two remaining members of this
  archive. Worth their own issue; `find_member` is ready for them.

## ingestion-registro-fundo-classe_20260710_020000

# Work ledger — Registro RCVM 175 readers (fundo / classe / subclasse)

Branch `feat/ingestion-registro-fundo-classe-reader` · **user-prioritised follow-up** (not a
numbered backlog issue) · part of the [kanban sweep](kanban-ready-backlog-sweep_20260708_220638.md).

## Scope

Three readers for the three members of `registro_fundo_classe.zip`, the post-**Resolução CVM 175**
fund → class → subclass registry. Raised as a #9 follow-up and pulled forward by the user because
it is where the **live** funds are (`cad_fi.csv` is ~99.5% cancelled).

- `RegistroFundoReader` — `registro_fundo.csv` (21 cols), key `ID_Registro_Fundo`.
- `RegistroClasseReader` — `registro_classe.csv` (30 cols), FK `ID_Registro_Fundo`.
- `RegistroSubclasseReader` — `registro_subclasse.csv` (14 cols), FK `ID_Registro_Classe`.

## Design decisions (user-approved)

- **Three separate readers, one per member** (user chose "all three now" over "fundo first"). One
  public class per file, per repo convention.
- **Not joined into one frame.** The hierarchy is one-to-many, so a join fans the fund's rows out —
  the CDA grain-mixing trap. Consumers join on the surrogate keys themselves; documented with an
  example. FK integrity is 100% on the real file, so the join is safe when the consumer chooses the
  grain.
- **No shared base class.** The four existing readers all repeat the download→extract→read_table
  pattern inline; introducing a base just for these three would break that consistency. Each reader
  is self-contained (reuses `find_member` + `raw_workspace`, already shared seams).
- **Single combined doc page** (`docs/ingestion/registro.md`) rather than three near-duplicate
  pages — the trio shares one archive and one hierarchy, explained once.

## Findings from the real artifact

- [x] Three members, fixed field counts under both quotings (`QUOTE_NONE` safe, not load-bearing).
- [x] Columns are **Title_Case** (`Denominacao_Social`), not the UPPER_SNAKE of `cad_fi.csv`.
- [x] CNPJs are **bare digits** (`00016999000167`), not masked like `cad_fi.csv`.
- [x] **34,176 funds `Em Funcionamento Normal`** (vs 22 in `cad_fi.csv`) — confirms this is the
  live registry.
- [x] `ID_Registro_Fundo` not strictly unique (1,121 dup); `ID_Registro_Classe` 3 dup;
  `ID_Subclasse` 0 dup. FK class→fund and subclass→class both resolve **100%**. No grain asserted.
- [x] `CPF_CNPJ_Gestor` holds a CPF on `Tipo_Pessoa_Gestor == "PF"` rows → excluded from CNPJ check.
  `registro_subclasse` has **no CNPJ column** → empty `tuple_cnpj_cols` (a test pins this path).
- [x] Snapshot (fixed URL, no `AAAAMM`) → readers take **no `date_ref`**; a test asserts passing
  one raises.

## Sat on the reorg (PR #39)

Implementation was written, then **stashed** while PR #39 (move ports/schemas under `config/`)
landed. Resumed on the reorged `main`: the three readers' `_internal.ports` imports were rewritten
to `_internal.config.ports`. Per the user, this work **rides PR #39's release** — a single `0.8.0`,
not a release each.

## Shipped

- [x] 3 contracts `_internal/config/contracts/registro_{fundo,classe,subclasse}.py`
- [x] 3 readers `ingestion/registro_{fundo,classe,subclasse}.py`
- [x] Exports (`ingestion/__init__`, package `__all__`, `contracts/__init__`)
- [x] 3 test files — 34 tests
- [x] Docs: combined `docs/ingestion/registro.md`, `ingestion/index.md`, `api.md`, `mkdocs.yml` nav
- [x] Root `CLAUDE.md` catalog: `registro_fundo_classe.zip` marked ✅

## Verification

- [x] 123 unit tests green under **pandas 3.0.3 and 2.3.3**. Ruff check + format,
  `bin/check_typing.py` clean.
- [x] **End-to-end against the live archive:** fundo 89,139 × 21 (34,176 active), classe
  36,398 × 30 (FK→fundo 100%), subclasse 8,865 × 14 (FK→classe 100%); dates coerced; `path_raw`
  kept the ZIP and all three CSVs from a single download.

## Open

- [x] **PR #40** opened; awaiting user review/merge, then the single `0.8.0` release.
- [ ] `cad_fi_hist.zip` (CAD/FI change log) remains the last unread member of the CAD directory.
