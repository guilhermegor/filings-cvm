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
