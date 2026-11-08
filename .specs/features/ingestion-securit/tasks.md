## ingestion-securit-cepac-flat_20260712_210424

# Work ledger — SECURIT DFIN (CRA/CRI) + EMISSOR_CEPAC CAD (#87, Wave 2 PR 1/4)

Issue **#87** · branch `feat/ingestion-securit-cepac-flat-87`. First slice of Wave 2 of #41
(Securitização): the three **flat-CSV** datasets, grouped into one PR (maintainer's chosen
decomposition). Inaugurates the `securit/` **and** `emissor_cepac/` portal roots. Grounded in the
real artifacts (META + bytes, 2026-07-12).

Excluded from the docs site (`backlog/`). Never deleted — tick the last box on completion.

## 3 readers, 2 new roots

| Reader | Dataset | Artifact | Precedent |
|---|---|---|---|
| `DfinCraReader` | `SECURIT/DOC/DFIN_CRA` | `dfin_cra_AAAA.csv` (flat, yearly) | `DfinFiiReader` |
| `DfinCriReader` | `SECURIT/DOC/DFIN_CRI` | `dfin_cri_AAAA.csv` (flat, yearly) | `DfinFiiReader` |
| `CadastroEmissorCepacReader` | `EMISSOR_CEPAC/CAD` | `cad_emissor_cepac.csv` (snapshot, fixed URL) | `CadastroFiReader` |

- **DFIN CRA/CRI** — identical 9-col index of financial statements (one row per document). Year-
  partitioned; `Link_Download` returned as text, **not followed**. Dates `Data_Referencia`,
  `Data_Entrega`; CNPJ `CNPJ_Emissora`; no unique key. Live: 681 / 2300 rows on 2025.
- **cad_emissor_cepac** — 20-col registry snapshot (municipalities; 3 rows), fixed URL → **no
  `date_ref`**. Dates `DT_REG`/`DT_CANCEL`/`DT_INI_SIT`; CNPJ `CNPJ`.

## Done

- [x] 3 contracts (`dfin_cra`, `dfin_cri`, `cad_emissor_cepac`) + re-exports in `contracts/__init__`.
- [x] 3 readers under new `securit/doc/` + `emissor_cepac/cad/` packages; `__init__` chains for both
  roots. All carry `raw_workspace` + `hash_artifact` + `stamp_provenance` + `_RETRY_POLICY`.
- [x] Public API wired: `ingestion/__init__` + root `filings_cvm/__init__` (imports + `__all__`).
- [x] Docs: page `securit_cepac_flat.md`, mkdocs nav, `api.md` section, ingestion `index.md` bullet,
  root `CLAUDE.md` catalog (2 new roots + Layout) + #41 survey ledger (SECURIT 🟡 partial, CEPAC ✅).
- [x] Tests `test_securit_cepac_flat_ingestion.py` (22, config-driven; CEPAC's absent `date_ref`
  handled by a `_build` helper). Full suite **937 pass BOTH pandas majors**; all gates + mypy clean.
- [x] **Live-verified** against real bytes (DFIN 681/2300 rows, CEPAC 3; dates coerced; Link_Download
  kept as `str`, not followed; provenance stamped).
- [x] Kanban: #87 moved to **In progress** (had to fix manually — raw `gh` left it in Backlog; the
  deterministic branch-name-keyed hook is captured in dotfiles `issue-command-drives-kanban-lifecycle`).

## Remaining

- [ ] Open PR (`Closes #87`); wait for approval + merge. `risk:src` → human review.
- [ ] After merge: **release** — `feat` in `src/` → **PATCH** bump. PyPI 0.24.0, Test-PyPI floor
  0.25.1 → next likely **0.25.2** (compute vs max of both indices).
- [ ] Wave 2 PRs 2–4: `INF_MENSAL_OTS` (8 members), `INF_MENSAL_CRA` (8), `INF_MENSAL_CRI` (11) —
  multi-member yearly zips, one reader per member over a private base (FIDC INF_MENSAL template).

## ingestion-securit-inf-mensal-cra_20260715_101500

# Work ledger — #96 SECURIT INF_MENSAL_CRA (8 membros) — Wave 2 PR 3/4

Branch `feat/ingestion-securit-inf-mensal-cra-96`. Fecha **#96**. Release: `feat` em `src/` →
**PATCH** → **0.25.4**.

## O achado que define esta PR

O `INF_MENSAL_CRA` tem **os mesmos 8 nomes de seção** do `INF_MENSAL_OTS` (já embarcado) e a mesma
forma de reader. Parecia trabalho de copiar/colar. **Não era: os 8 diferem.** O CRA é *agro*; o OTS é
o residual genérico.

| membro | OTS | CRA |
|---|---|---|
| todos os 8 | `CNPJ_Securitizadora` | **`CNPJ_Emissora`** |
| `direitos_creditorios` | 43 | **56** (13 baldes agro) |
| `geral` | 36 | 31 (+`Cadeia_Producao`/`Tipo_Segmento`; **sem** bloco de contingências) |
| `derivativos` | `*_Commodities` | `*_Commodities_Agricolas` |
| `classe` | `Codigo_Negociacao_Mercado_Secundario`, `Total_Integralizado` | `Codigo_CETIP`, `Valor_Total_Integralizado` |
| `fluxo_caixa` | `Recebimentos_Creditos` | `Recebimentos_Direitos_Creditorios` |

**Copiar os contracts do OTS embarcaria os 8 errados com a suíte inteira verde** — porque os testes
afirmam o contract que foi escrito. Corolário: a typo `Outras_Contigencias_Relevantes` do OTS **não
tem contrapartida aqui** — quirk é fato de artefato, não de família.

## Feito

- [x] **Grounding nos bytes reais** — `inf_mensal_cra_2025.zip` (1.360.247 bytes) + `meta_*.zip`
  baixados do portal. 8 membros confirmados: geral 31, ativo_passivo 31, classe 23,
  direitos_creditorios 56, desembolso 22, fluxo_caixa 21, derivativos 20, cedente_devedor 7.
- [x] **Contracts gerados do header publicado**, nunca transcritos, e **verificados
  programaticamente** (`tuple_required == header` nos 8 → 0 drift).
- [x] **Fixtures de header pinados** (`tests/fixtures/inf_mensal_cra/*_header.csv`) — os bytes
  verbatim do header da CVM. **Só header, ZERO linhas de dados**: `cedente_devedor` guarda **CPF
  real** e commitar linhas publicaria dado pessoal. O ganho anti-tautologia é o mesmo.
- [x] **`test_contract_matches_the_published_header`** — o único teste do arquivo cujo valor esperado
  **não** veio de nós. **Mutation-testado** (prova de que falha mesmo):
  - `CNPJ_Emissora`→`CNPJ_Securitizadora` em `geral` (**o erro de cópia exato**) → **2 testes falham**;
  - remover 1 coluna (`Cadeia_Producao`) → **falha**;
  - restaurado → 44 passam.
- [x] `test_cra_contracts_are_not_the_ots_contracts` — guarda explícita contra uma cópia futura.
- [x] Base privada `_base_inf_mensal_cra_reader.py` + **8 readers finos** (`_MEMBER_STEM`,
  `_CONTRACT`, `_LABEL`, `_DATE_COLS`, `_RETRY_POLICY`), padrão OTS/FIDC.
- [x] Re-export flat nos 4 níveis (`securit/doc` → `securit` → `ingestion` → `filings_cvm`); 8 nomes
  no `__all__` público.
- [x] **Live-verificado contra os bytes reais**, os 8: 8093/8093/14073/8093/8093/8093/8093/10691
  linhas, contagem de colunas exata, proveniência (6 colunas) em todos.

### Armadilhas auditadas nos valores reais (não presumidas)

- [x] **`classe.Indice_Subordinacao_Data_Base` NÃO é data** — valores `'0.00'`. Fora do `_DATE_COLS`
  (mesma trap do OTS). Teste trava.
- [x] **`cedente_devedor.CNPJ` NÃO é coluna de CNPJ** — campo livre e sujo. Arquivo 2025 inteiro:
  14 díg = 7.090 (CNPJ), **11 díg = 327 (CPF, dado pessoal)**, 1 díg = 2.352 (`'0'`), 0 díg = 103
  (`','`), 15 díg = 72 (malformado), **33 díg = 12 (dois identificadores na mesma célula)**. Só
  `CNPJ_Emissora` em `tuple_cnpj_cols`; teste cobre as 5 formas sujas.
- [x] **`geral` tem 3 colunas `CNPJ_*` 100% vazias** (`CNPJ_Agente_Fiduciario`, `CNPJ_Custodiante`,
  `CNPJ_Agencia_Classificadora`) — entram no contract, **ficam fora** de `tuple_cnpj_cols` (nada a
  validar hoje; declará-las falharia um arquivo válido no dia em que a CVM as preencher com texto
  livre). Teste trava.
- [x] `_DATE_COLS` por membro auditado contra os valores reais: `geral` 4, `classe` 2, os outros 6
  só `Data_Referencia`.

## Gates

- [ ] ruff check + format · mypy · codespell · check_typing · check_provenance · check_docstrings
- [ ] **pytest nos DOIS pandas majors** (3.0.3 e 2.3.3)
- [ ] `mkdocs build --strict`
- [x] 44 testes novos passam; live-verify OK; mutation-test do guard OK

## Docs

- [x] Página `docs/ingestion/inf_mensal_cra.md` + nav no `mkdocs.yml`
- [x] `docs/api.md` (secção `InfMensalCra*Reader`), `docs/ingestion/index.md`
- [x] Catálogo do `CLAUDE.md` raiz (entrada CRA + layout `securit/`)
- [ ] Ledger do #41 (survey) — marcar CRA feito, CRI a seguir

## Aberto / próximo

- [ ] PR → aprovação do usuário → merge → **release PATCH 0.25.4** (Test PyPI → verify → PyPI →
  verify). ⚠️ **Primeiro release depois do #79** (bumps `upload-artifact@v7`/`download-artifact@v8`/
  `gh-release@v3`, que **nenhuma PR exercita** — os workflows de release são `workflow_dispatch`).
  **Não pular o Test PyPI**; conferir `gh run view --json jobs` → `test_pypi: success`, não `skipped`
  (lição do #86).
- [ ] **Depois: #97 (módulo público de META) → #98 (job semanal de drift) → CRI (11 membros,
  META-first).** Sequência escolhida com o usuário: o CRI é o maior alvo de "copiar do irmão" que
  resta, então é o primeiro cliente ideal do seam.
- [x] Lição BlueprintX capturada: `pin-contracts-to-a-source-published-oracle.md` (store global +
  mirror do repo). É a lição-mãe do #97/#98.

## ingestion-securit-inf-mensal-cri_20260718_095454

# Ledger — #114 SECURIT INF_MENSAL_CRI readers (11 members)

Branch: `feat/114-inf-mensal-cri` · Issue: #114 · Class: **src (feat)** → PATCH release (0.25.6)

## Goal

Ingestion readers for `SECURIT/DOC/INF_MENSAL_CRI` (`inf_mensal_cri_AAAA.zip`, 11 members). Wave 2
PR 4/4 — **closes the `securit/` root (4/4)** and ends Wave 2 of #41.

## Work

- [x] 11 verbatim header fixtures generated from the real 2025 zip — `tests/fixtures/inf_mensal_cri/`
      (the pinned oracle; header-only, no PII).
- [x] `contracts/inf_mensal_cri.py` — 11 contracts **generated from the fixtures**, source key
      `inf_mensal_cri_<section>`, cnpj/date cols verified against real 2025 values.
- [x] `_base_inf_mensal_cri_reader.py` + 11 thin subclasses (CRA template; yearly `date_ref`).
- [x] `meta.py` = **23rd Meta reader** `MetaInfMensalCriReader` + `META_INF_MENSAL_CRI` in the
      `contracts/meta.py` factory list. META live-verified (URL, 11 members, `Data_LTV`=varchar,
      `Indice_Subordinacao_Data_Base`=numeric).
- [x] Registered CRI in `bin/check_contract_drift.py` `_META_MEMBERS` (#98 structural test — CI
      would fail otherwise). Registry re-closes: **113 readers, 113 members, 0 gaps**.
- [x] Wired all 5 `__init__` layers (package → securit/doc → securit → ingestion → top
      `filings_cvm`) + `contracts/__init__`. `test_meta_readers.py` 22→23.
- [x] Tests `test_inf_mensal_cri_ingestion.py` (mirrors CRA anti-tautology + traps + a header-only
      regression). Full unit suite green.
- [x] **Live-verified against real 2025 bytes**: geral 26,689×44, creditos ×51, classe 51,914×28,
      cedente_devedor 38,953×7, responsavel 0 rows (header-only reads clean).
- [x] Docs: `docs/ingestion/inf_mensal_cri.md` + mkdocs nav + api.md (+ Meta count 23) + ingestion
      index + root CLAUDE.md catalog (securit COMPLETE 4/4) + #41 survey ledger.

## Findings from the real bytes (honoured, not "fixed")

- [x] CRI is **not** a CRA copy: no `direitos_creditorios` (has `creditos`, 51 cols); +4 members.
- [x] `desembolso` (22) and `cedente_devedor` (7) are **column-identical to CRA** — generic
      structures; the coincidence is the source's, proven by the pinned headers (not a copy error).
      Anti-copy test asserts only the 5 asset-class sections differ.
- [x] `carteira_modificacao` + `responsavel` are **header-only** in 2025 → `tuple_cnpj_cols=()`
      (else a legitimately empty member fails the contract). Caught by live-verify, not unit tests.
- [x] `cedente_devedor.CNPJ` may be CPF (excluded from cnpj cols); `Indice_Subordinacao_Data_Base`
      and `Data_LTV` (varchar per META) are not dates; `Outras_Contigencias_Relevantes` typo kept.

## Remaining before PR

- [ ] codespell (pt-BR words), mkdocs --strict, pre-commit on changed files.
- [ ] pytest under **both** pandas 3.0.3 and 2.3.3.
- [ ] Commit → PR `Closes #114` → wait approval+merge → release PATCH 0.25.6.

## ingestion-securit-inf-mensal-ots_20260712_220156

# Work ledger — SECURIT INF_MENSAL_OTS readers (#89, Wave 2 PR 2/4)

Issue **#89** · branch `feat/ingestion-securit-inf-mensal-ots-89`. Second slice of Wave 2 of #41
(Securitização): the 8-member `INF_MENSAL_OTS` yearly ZIP. Grounded in the real `2025` artifact
(META + bytes, 2026-07-12).

Excluded from the docs site (`backlog/`). Never deleted — tick the last box on completion.

## Shape

⚠️ **Yearly-partitioned ZIP despite a monthly report** (`inf_mensal_ots_AAAA.zip`, members
`inf_mensal_ots_<section>_AAAA.csv`) → `date_ref` selects the **year** (FII pattern, not FIDC). 8
members share the 4-col key prefix (`CNPJ_Securitizadora`, `Codigo_Identificacao_Certificado`,
`Data_Referencia`, `Versao`) → private base + 8 thin subclasses (FIDC INF_MENSAL template).

| Reader | Member | Cols | Rows (2025) |
|---|---|---|---|
| `InfMensalOtsGeralReader` | geral | 36 | 1793 |
| `InfMensalOtsAtivoPassivoReader` | ativo_passivo | 30 | 1793 |
| `InfMensalOtsClasseReader` | classe | 23 | 6821 (long) |
| `InfMensalOtsDireitosCreditoriosReader` | direitos_creditorios | 43 | 1793 |
| `InfMensalOtsDesembolsoReader` | desembolso | 22 | 1793 |
| `InfMensalOtsFluxoCaixaReader` | fluxo_caixa | 21 | 1793 |
| `InfMensalOtsDerivativosReader` | derivativos | 20 | 1793 |
| `InfMensalOtsCedenteDevedorReader` | cedente_devedor | 7 | 1650 (long) |

## Three traps found by grounding + LIVE-verified (all honoured)

1. **`cedente_devedor.CNPJ` holds a CPF on 257/1650 rows** — NOT declared a CNPJ column (would fail
   a valid file — `cad_fi.CPF_CNPJ_GESTOR` trap); only `CNPJ_Securitizadora` is validated. PII →
   verbatim text. Live: all 257 CPF rows parsed without ContractError.
2. **`Indice_Subordinacao_Data_Base` (in `classe`) is NOT a date** despite the name — numeric values.
   Absent from `_DATE_COLS`; stays `str`. Live-confirmed.
3. **CVM typo verbatim:** `Outras_Contigencias_Relevantes` in `geral` (missing *n*) vs correct
   `Contingencias_Principais_Fatos` in the same file. Live-confirmed present.

Date columns are **per-member** (FIAGRO pattern): all have `Data_Referencia`; `geral` +3, `classe`
+`Data_Vencimento`.

## Done

- [x] Contract module `inf_mensal_ots.py` (8 constants, deliberate `inf_mensal_fidc.py` deviation) +
  re-exports. **All 8 tuples programmatically verified equal to the real headers** (0 drift).
- [x] Private base `_base_inf_mensal_ots_reader.py` (yearly `date_ref`, per-member `_DATE_COLS`,
  exact-name member selection) + 8 thin readers; `inf_mensal_ots/` `__init__`.
- [x] Public API wired: `securit/doc` + `securit` + `ingestion/__init__` + root `__init__`.
- [x] Docs: page `inf_mensal_ots.md`, mkdocs nav, `api.md` section, ingestion index bullet, root
  `CLAUDE.md` catalog + Layout; #41 survey ledger.
- [x] Tests `test_inf_mensal_ots_ingestion.py` (41, incl. 3 trap regressions). Full suite **1010
  pass BOTH pandas majors**; ruff/format/typing/provenance/mypy/codespell all clean.
- [x] **Live-verified** all 8 against real 2025 bytes (row counts 1793/6821/1650 etc.; dates coerced;
  money `str`; provenance stamped; 3 traps behave).
- [x] Kanban: #89 → In progress (manual; hook not deployed).

## Remaining

- [ ] Open PR (`Closes #89`); wait for approval + merge. `risk:src` → human review.
- [ ] After merge: release **PATCH** (0.25.2 → **0.25.3**; both indices aligned at 0.25.2).
- [ ] Wave 2 PRs 3–4: `INF_MENSAL_CRA` (8 members), `INF_MENSAL_CRI` (11) — same base+subclass
  template; CRI adds `carteira`, `carteira_modificacao`, `creditos`, `responsavel` vs CRA/OTS.
