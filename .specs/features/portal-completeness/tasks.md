## chore-implemented-packages-204_20260808_090223

# Ledger — #204 registrar as Waves 3 e 4 em `_IMPLEMENTED_PACKAGES`

Branch: `chore/204-registrar-waves-3-4-implemented-packages` · Issue: #204 · Class: **ci**
(zero diff em `src/` → **sem release**)

## O problema, medido

`bin/check_portal_completeness.py` declara em `_IMPLEMENTED_PACKAGES` os slugs CKAN que a
biblioteca ingere. A lista ficou em **21** enquanto as Waves 3 e 4 entregavam **23** datasets
(`auditor-cad` … `cia_aberta-eventos-recompra_acoes`). O job semanal seguiu publicando o resultado
na issue #122: **33 pendentes de 54**, quando a verdade medida é **10 de 54** (44 implementados).

⚠️ **A omissão não tinha como ficar vermelha.** Ela só se manifesta no corpo de uma *issue*, que
nenhum teste lê. Os testes estruturais existentes conferem a **forma** dos slugs declarados, nunca
se algum **faltou** — a asserção `len >= 20` passava com folga em 21.

## Feito

- [x] Registrados os **23** slugs faltantes, em ordem alfabética, cada um com o comentário da
      família de readers no estilo do arquivo: `adm_cart-cad`, `adm_fii-cad`, `agente_auton-cad`,
      `agente_fiduc-cad`, `auditor-cad`, `cia_aberta-cad`, os **7** `cia_aberta-doc-*`,
      `cia_aberta-eventos-recompra_acoes`, `cia_estrang-cad`, `cia_incent-cad`,
      `consultor_vlmob-cad`, `coord_oferta-cad`, `crowdfunding-cad`, `fi-doc-eventual`,
      `intermed-cad`, `invnr-cad`, `oferta-distrib`.
- [x] Comentário de bloco `21 today` → `44 today`, mais a nota de por que a edição é fácil de
      esquecer e o que a defende agora.
- [x] `unregistered_roots(frozenset_roots, frozenset_implemented)` — lógica pura nova no script,
      no molde do `missing_packages`: devolve os roots que **nenhum** slug cobre, comparando o
      primeiro segmento do slug (`cia_aberta-doc-itr` → `cia_aberta`).
- [x] 3 testes em `tests/unit/test_check_portal_completeness.py`: o positivo sobre os roots reais
      (via `iter_root_packages()`, que **levanta** em vez de devolver vazio) e **2** controles da
      lógica pura — um root descoberto, um root coberto por qualquer um dos seus datasets.
- [x] `docs/ingestion/portal_completeness.md` — seção nova sobre a deriva medida e o piso agora
      testado, incluindo o que o gate **não** pega.
- [x] Gate re-rodado: **10 pendentes de 54** (era 33).

## Controle negativo — verificado

Mutação: remover as **9** linhas `cia_aberta-*` de `_IMPLEMENTED_PACKAGES`.

| passo | resultado |
|---|---|
| baseline | 11 passed |
| mutante (9 linhas removidas, contagem assertada no script) | **1 failed**, 10 passed |
| teste que falhou | `test_every_portal_root_is_registered_in_the_implemented_set` |
| restore por cópia de snapshot | `diff` byte-idêntico, 11 passed |

⚠️ O **`1`** é achado, não acaso: existe **exatamente uma** defesa para esse fato. E o restore foi
por **cópia de snapshot** com `diff` conferido, não `git checkout` — a lição
`a-negative-control-needs-a-verified-restore` (#191) aplicada de primeira.

## Escopo deliberadamente NÃO feito

- [ ] **Cobertura por dataset.** O gate é de nível **root**: `fi` está coberto por `fi-doc-cda`, então
      esquecer um segundo dataset do `fi` (foi o caso do `fi-doc-eventual`) **continua invisível**.
      Fechar isso exigiria derivar "implementado?" de nomes de reader — exatamente a derivação que o
      docstring do script rejeita e que o job de deriva de contrato evita (`cad_fi` × `cad_fi_hist`).
      Preferido um piso grosso e honesto a um mapeamento frágil.
- [ ] **Sincronizar a issue #122 agora.** O job semanal a reescreve sozinho no próximo run; forçar à
      mão mascararia se o fix pegou.

## Backlog real depois deste PR — 10 datasets

`fi-doc-perfil_mensal` (próximo alvo, decidido com o user) · `fi-doc-extrato` · `fi-doc-balancete` ·
`fi-doc-compl` · `fi-doc-entrega` · `emissores` · `distrpubl` · `ato_declr-intermed` ·
`processo-sancionador` · `arrecadacao-receita-publica`.

Completed — kept as a record.

## feat-portal-completeness-111_20260719_062823

# Ledger — #111 weekly portal-completeness detector

Branch: `feat/111-portal-completeness` · Issue: #111 · Class: **ci** (no `src/` diff → no release)

## Goal

Weekly, non-blocking job that lists CVM portal datasets we haven't implemented, in one tracking
issue. Automates the manual #41 survey; sibling of the #98 drift job.

## Design decisions (the issue left these open)

- **Enumerate via the CKAN API** (`/api/3/action/package_list`) — deterministic, stable, 54
  packages today. Not HTML scraping.
- **Coverage is declared, not derived** — `_IMPLEMENTED_PACKAGES` (21 slugs). A CKAN slug doesn't
  map cleanly to our readers (`fi-cad` = one package, three reader families; `*-cad` vs `*-doc-*`
  differ in depth), so deriving would repeat the `cad_fi`/`cad_fi_hist` trap.
- **Scope = the full gap** (33 today) = the automated #41 backlog. No skip list yet (YAGNI; add
  `_SKIP_PACKAGES` if a package is ever declared permanently out of scope).
- **Detection only** — no LLM code-gen/auto-PR (a generated reader touches header-pinned contracts;
  `pr_gate` never auto-merges `src/`). Deferred, post-1.0, human-reviewed.

## Work

- [x] `bin/check_portal_completeness.py` — **pure stdlib** (urllib + json, no package import): CKAN
      fetch → `missing_packages` (pure) → issue upsert (label + hidden marker dedupe) → `main()`
      always exits 0; a portal outage is tolerated (no spurious "all missing" issue).
- [x] `.github/workflows/portal-completeness.yaml` — `schedule` + `workflow_dispatch`,
      `issues: write`, no `poetry install` (stdlib only), rationale in-file.
- [x] `tests/unit/test_check_portal_completeness.py` — pure gap, issue body/dedupe, structural
      (slugs well-formed, set non-empty). 8 tests, no network.
- [x] `docs/ingestion/portal_completeness.md` + mkdocs nav.
- [x] `portal-completeness` label created on the repo.
- [x] **Live-verified against real CKAN**: published 54, implemented 21, gap 33, **0 stale
      implemented slugs** (every declared slug exists in the live portal → the set is accurate).

## After merge

- [ ] Dispatch the workflow once to prove it opens the tracking issue (33 items).
- [ ] Keep `_IMPLEMENTED_PACKAGES` in step when new datasets land (add the slug on implement).

## Not done, on purpose

- No gate parity — scheduled non-blocking job, out of pre-commit/CI gates by design.

## portal-survey-41_20260710_204535

# Work ledger — survey the CVM open-data portal roots (#41)

Issue **#41**. Survey every root under <https://dados.cvm.gov.br/dados/> and decide what
else is worth scraping now that the FI ingestion backlog is clear.

## Standing decision (user, 2026-07-10)

> "Scrape everything that is possible. This is a package that must serve users — let them
> decide what they want to use, but provide resources for them to do so."

So #41 is **not** a prioritise-a-subset exercise: the target is an `IngestionReader` for **every
scrapable dataset** across all 24 portal roots. Users pick what they import; the library ships
the full surface. Implementation stays one-PR-at-a-time behind the approval gate, ordered by
value (fund vehicles first — they feed the marketdata-fm fund datalake and reuse the FI reader
patterns already built).

## Method

Crawled the Apache directory index of `/dados/` and each root two–three levels deep to the
`DADOS/` leaves (`rtk proxy curl` + href extraction). Every dataset leaf carries a `META/`
sidecar → the META-first contract rule (#45/#46) applies uniformly across the whole backlog.

## Complete inventory — 24 roots

Legend: ✅ implemented · ⬜ pending · `layout` = target `ingestion/<path>/` (sibling of `fi/`).

### Fundos — investment vehicles (highest value; marketdata-fm datalake core)

| Root | Datasets (under DOC/ unless noted) | Layout | Status |
|---|---|---|---|
| **FI** | INF_DIARIO, CDA, LAMINA(+carteira), CAD/FI, cad_fi_hist (19), registro (fundo/classe/subclasse) | `ingestion/fi/` | ✅ shipped |
| **FIDC** | INF_MENSAL (multi-member zip: several tabelas) | `ingestion/fidc/` | ⬜ |
| **FII** | DFIN, INF_ANUAL, INF_MENSAL, INF_TRIMESTRAL | `ingestion/fii/` | ⬜ |
| **FIP** | INF_TRIMESTRAL (flat CSV), INF_QUADRIMESTRAL | `ingestion/fip/` | ✅ shipped (#66) |
| **FIAGRO** | INF_MENSAL (2 members: informe + subclasse) | `ingestion/fiagro/` | ✅ shipped (#74) |
| **FIE** | DOC/BALANCETE, DOC/BALANCO, MEDIDAS (no CAD) | `ingestion/fie/` | ✅ shipped (#84) |

### Securitização

| Root | Datasets | Layout | Status |
|---|---|---|---|
| **SECURIT** | DOC/{DFIN_CRA ✅, DFIN_CRI ✅, INF_MENSAL_OTS ✅(8), INF_MENSAL_CRA ✅(8), INF_MENSAL_CRI ✅(11)} | `ingestion/securit/` | ✅ COMPLETE (#87, #89, #96, #114) |
| **EMISSOR_CEPAC** | CAD | `ingestion/emissor_cepac/` | ✅ shipped (#87) |

### Companhias / emissores / ofertas (large, separate domain)

| Root | Datasets | Layout | Status |
|---|---|---|---|
| **CIA_ABERTA** | DOC/{CGVN, DFP, FCA, FRE, IPE, ITR, VLMO}, CAD, EVENTOS | `ingestion/cia_aberta/` | ⬜ |
| **CIA_ESTRANG** | CAD | `ingestion/cia_estrang/` | ✅ (#143) |
| **CIA_INCENT** | CAD | `ingestion/cia_incent/` | ✅ (#145) |
| **OFERTA** | DISTRIB | `ingestion/oferta/` | ✅ (#151) |
| **COORD_OFERTA** | CAD | `ingestion/coord_oferta/` | ✅ (#147) |
| **CROWDFUNDING** | CAD | `ingestion/crowdfunding/` | ✅ (#149) |

### Prestadores de serviço / registros (CAD snapshots — cheap, same shape as CAD/FI)

| Root | Dataset | Layout | Status |
|---|---|---|---|
| **ADM_CART** | CAD (administradores de carteira) | `ingestion/adm_cart/` | ✅ (#137) |
| **ADM_FII** | CAD | `ingestion/adm_fii/` | ✅ (#141) |
| **AGENTE_AUTON** | CAD | `ingestion/agente_auton/` | ⬜ |
| **AGENTE_FIDUC** | CAD | `ingestion/agente_fiduc/` | ⬜ |
| **AUDITOR** | CAD | `ingestion/auditor/` | ⬜ |
| **CONSULTOR_VLMOB** | CAD | `ingestion/consultor_vlmob/` | ✅ (#139) |
| **INTERMED** | CAD | `ingestion/intermed/` | ✅ (#135) |

### Investidores / mercado / processos

| Root | Dataset | Layout | Status |
|---|---|---|---|
| **INVNR** | CAD (investidor não residente) | `ingestion/invnr/` | ✅ (#133) |
| **ATO_DECLR** | INTERMED | `ingestion/ato_declr/` | ⬜ |
| **PROCESSO** | SANCIONADOR | `ingestion/processo/` | ⬜ |

## Folder plan

The `fi/` root level (added in #44 follow-up) makes every other root a **sibling**:
`ingestion/{fidc,fii,fip,fiagro,fie,securit,cia_aberta,adm_cart,…}/`, each mirroring
`dados.cvm.gov.br/dados/<ROOT>/`. Multi-file datasets nest a per-dataset sub-package exactly
like `fi/doc/lamina/` and `fi/cad/cad_fi_hist/`. Public API stays flat
(`from filings_cvm.ingestion import XReader`).

## Reader tally

~25 dataset leaves, but **multi-member zips expand to N readers** (as FI's `cad_fi_hist.zip`
became 19). Member counts are resolved at implementation time by inspecting the real artifact
(standing decision: ground the contract in the downloaded bytes, not a guess). Realistic total
is **50–80 readers** — a multi-PR sweep, not one PR.

## Implementation order (proposed)

- [x] **Wave 1 — fund vehicles: COMPLETE** — FIDC → FII → FIP → FIAGRO → FIE all shipped. Two
  corrections found on the FIE ground-truth (verified from the raw directory listing): **`FIE/CAD`
  does not exist** (dropped) and **`FIE/MEDIDAS` was missing from this plan** (added). Reused FI
  patterns throughout (tabular_reader + META contract + raw_workspace + provenance stamp).
- [x] **Wave 2 — securitização:** SECURIT (5 datasets), EMISSOR_CEPAC. **COMPLETE:** PR 1/4
  (#87) shipped the 3 flat CSVs; PR 2/4 (#89) shipped INF_MENSAL_OTS (8 members); PR 3/4 (#96)
  shipped INF_MENSAL_CRA (8 members); **PR 4/4 (#114) shipped INF_MENSAL_CRI (11 members) — closes
  the `securit/` root (4/4).**
  - ⚠️ **Lesson from #96, apply to CRI:** CRA ships the **same 8 section names** as OTS and **not one
    column list matched** (`CNPJ_Securitizadora`→`CNPJ_Emissora` on all 8; `direitos_creditorios` 56
    vs 43). Copying the sibling's contracts would have shipped 8 wrong ones **with every test green**.
    So CRI's contracts must be **generated from its own published headers** and **pinned to header
    fixtures** — never derived from CRA/OTS. Build it **META-first** (#97 → #98 land first, by
    agreement): CRI is the largest remaining copy-risk surface (11 members), so it is the seam's
    ideal first customer.
- [ ] **Wave 3 — service-provider registries:** ADM_CART, ADM_FII, AGENTE_AUTON, AGENTE_FIDUC,
  AUDITOR, CONSULTOR_VLMOB, INTERMED, INVNR. ⚠️ **Correction to the original "cheap, near-identical to
  CadastroFiReader" estimate:** grounding showed 7 of 8 are **multi-member ZIPs** with `pf`/`pj`
  (pessoa física/jurídica) splits — only ADM_FII is a flat CSV. ~21 readers total; person-level
  members carry **CPF** (header-only fixtures, CPF kept as text, never CNPJ-validated). One PR per
  portal root.
  - [x] **AUDITOR** (#127) — `cad_auditor.zip`, 2 members (`pf` 4 cols, `pj` 12 cols). Establishes the
    multi-member CAD mould (private base + `pf`/`pj` + Meta reader, contracts pinned to real headers).
    AUDITOR's `pf` happens to have **no CPF** (identifies by `CD_CVM`+name); later roots' `pf` do.
  - [x] **AGENTE_FIDUC** (#129) — `cad_agente_fiduc.zip`, 2 members (`pf` 5 cols, `pj` 15 cols).
    Copies the AUDITOR mould. ⚠️ NOT a copy: 3 date cols vs 1, no `CD_CVM`, pj adds PAIS/DDD_TEL/TEL;
    `pf` has no CPF (name-only key). Contracts header-pinned.
  - [x] **AGENTE_AUTON** (#131) — `cad_agente_auton.zip`, 2 members (`pf` 6 cols ~49k rows, `pj` 19
    cols). ⚠️ NOT a copy: adds MOTIVO_CANCEL/DENOM_COMERC/EMAIL/SITE_ADMIN, uses DDD; 3 date cols;
    `pf` has no CPF (name-only key, name can be blank). Contracts header-pinned.
  - [x] **INVNR** (#133) — `cad_invnr_repres.zip`, 2 members (`pf` 6 cols 1.370 rows, `pj` 23 cols
    887 rows). ⚠️ NOT a copy: adds CONTROLE_ACIONARIO/DDD_FAX/FAX/VL_PATRIM_LIQ/DT_PATRIM_LIQ
    (4 date cols on `pj` vs 3 on `pf`), uses DDD_TEL; `pf` has no CPF (name-only key).
    CEP/TEL/FAX stay `str` despite `numeric` META. Contracts header-pinned.
  - [x] **INTERMED** (#135) — `cad_intermed.zip`, 2 members. ⚠️ NOT a `pf`/`pj` split: the registry
    (`cad_intermed.csv`, 28 cols, 4 date cols, 2.352 rows) + the responsible-officer table
    (`cad_intermed_resp.csv`, 8 cols, 2 date cols, 5.545 rows), **both keyed by the intermediary's
    CNPJ**. `resp` carries personal data (RESP/EMAIL_RESP) but **no CPF column**.
    CEP/TEL/FAX/CD_CVM stay `str` despite `numeric`/`char` META. Contracts header-pinned.
  - [x] **ADM_CART** (#137) — `cad_adm_cart.zip`, **5 members** (pf 7, pj 24, diretor 3, resp 3,
    socios 2). First 5-member root. ⚠️ 3 members (diretor/resp/socios) have **no date column** →
    `_DATE_COLS=()`, all text. `pf` has no CNPJ nor CPF (name key); satellites carry personal data
    but no CPF → keyed on the manager's CNPJ. One malformed source CNPJ (`00.010.354/1901-72`)
    honoured as published. Contracts header-pinned.
  - [x] **CONSULTOR_VLMOB** (#139) — `cad_consultor_vlmob.zip`, **5 members** (pf 7, pj 20,
    diretor 3, resp 3, socios 2). Same shape as ADM_CART: 3 members have **no date column**.
    ⚠️ NOT a copy: `pf` keyed by `NOME` (not `ADMIN`), 7th col `SITE_ADMIN` (not `CATEG_REG`);
    `pj` has 20 cols (not 24) and only **3 date cols** (no `DT_PATRIM_LIQ`/`VL_PATRIM_LIQ`).
    All CNPJ 100% valid. Contracts header-pinned.
  - [x] **ADM_FII** (#141) — `cad_adm_fii.csv`, the **only flat CSV** in Wave 3 (1 reader, 18 cols,
    no `date_ref`; molde do `CadastroFiReader`/Emissor CEPAC). 3 date cols (`MOTIVO_CANCEL` is text,
    not a date); keyed by `CNPJ` (masked), **no CPF column**. `CEP`/`DDD`/`TEL` stay `str` despite
    `numeric` META. **Closes Wave 3 (8/8).**
- [ ] **Wave 4 — companhias/ofertas:** CIA_ABERTA (big — 7 DOC datasets + CAD + EVENTOS),
  CIA_ESTRANG, CIA_INCENT, OFERTA, COORD_OFERTA, CROWDFUNDING. Grounding dos artefatos reais:
  CIA_ESTRANG/CIA_INCENT são **CSV solto** (`cad_cia_*.csv`), COORD_OFERTA/CROWDFUNDING são **ZIP**
  (`cad_*.zip`), CIA_ABERTA é o multi-dataset grande.
  - [x] **CIA_ESTRANG** (#143) — `cad_cia_estrang.csv`, **CSV solto** (1 reader, **49 cols**, sem
    `date_ref`; molde do `CadastroAdmFiiReader`). Abre a Wave 4. 7 date cols (`MOTIVO_CANCEL` é
    texto); **2 colunas de CNPJ** (`CNPJ` + `CNPJ_AUDITOR`); `RESP` sem CPF. Contract **gerado do
    header** e **pinado** a `tests/fixtures/cad_cia_estrang/*_header.csv` (49 cols = risco de
    transcrição). Harness flat-CSV (`FlatCase`) generalizado: cnpj cols agora derivam de
    `cls_contract.tuple_cnpj_cols` (suporta N colunas de CNPJ).
  - [x] **CIA_INCENT** (#145) — `cad_cia_incent.csv`, **CSV solto** (1 reader, **47 cols**, ~3.570
    linhas, sem `date_ref`). ⚠️ **NÃO é cópia do CIA_ESTRANG** (tem `ST_CIA_INCENT_REG`, sem
    `PAIS_ORIGEM`/`CD_PAIS_*`, usa `MUN`/`UF`). 7 date cols (`DT_INI_CATEG` 100% vazia mas é data por
    contrato); 2 colunas de CNPJ (`CNPJ` + `CNPJ_AUDITOR`); `RESP` sem CPF. Contract **gerado do
    header** e **pinado** a `tests/fixtures/cad_cia_incent/*_header.csv`.
  - [x] **COORD_OFERTA** (#147) — `cad_coord_oferta.zip`, **2 membros** (registro 25 cols/4 dates +
    resp 6 cols/2 dates), **ambos chaveados pelo CNPJ do coordenador** — molde do INTERMED, NÃO um
    split pf/pj. Primeiro ZIP multi-membro da Wave 4. ⚠️ **A META é um `.zip`** (o `.txt` 404) com
    `section` **assimétricas** (`cad_coord_oferta` + `resp`), exatamente como o INTERMED — previsto
    do checkpoint e pinado por teste. `resp` com dado pessoal mas **sem CPF**. Contracts gerados dos
    headers e pinados.
  - [x] **CROWDFUNDING** (#149) — `cad_crowdfunding.zip`, **3 membros**: registro (17 cols, 2 date
    cols) + `adm_resp` + `socios` (2 cols cada), **todos chaveados pelo CNPJ da plataforma**.
    ⚠️ Os 2 satélites **sem nenhuma coluna de data** (`_DATE_COLS=()`, forma do ADM_CART), com dado
    pessoal mas **sem CPF**. ⚠️ O registro é **mais enxuto que os irmãos** (sem `DT_CANCEL`/
    `MOTIVO_CANCEL`/`CD_CVM`; usa `WEBSITE`/`DDD`) → anti-cópia pinada por teste. ⚠️ META é `.zip`
    de 3 membros (o `.txt` 404) com `section` assimétricas. Contracts gerados dos headers e pinados.
  - [x] **OFERTA/DISTRIB** (#151, fecha #14) — `oferta_distribuicao.zip`, **2 membros por regime**:
    registro histórico pré-RCVM 160 (76 cols, 9 date cols, ~48,9k linhas) + requerimentos RCVM 160
    (71 cols, 3 date cols, ~13,9k linhas), de **regimes diferentes** com colunas disjuntas → NÃO é
    registro+satélite; anti-cópia pinada. Monetárias/contagem ficam `str` (→ `Decimal` a jusante);
    3/2 CNPJ cols. ⚠️ `Data_deliberacao_aprovou_oferta` em `DD/MM/YYYY` → `str` (coerção é ISO-only).
    ⚠️ META `.zip` de 2 membros (o `.txt` 404) mas `section` **simétricas** (`_MEMBER_STEM='oferta'`).
    Contracts gerados dos headers e pinados. Inaugura o root `oferta/`.
  - [x] **CIA_ABERTA/CAD** (#153) — `cad_cia_aberta.csv`, **CSV solto** (1 reader, **47 cols**,
    2.677 linhas, sem `date_ref`; molde do `CadastroCiaEstrangReader`). Abre o root `cia_aberta/`.
    ⚠️ **Não é cópia dos irmãos CIA_\***: chave `CNPJ_CIA` (não `CNPJ`) e coluna extra `TP_MERC`
    (mesmo total de 47 cols do CIA_INCENT é coincidência). 7 date cols (`MOTIVO_CANCEL` é texto);
    **2 colunas de CNPJ** (`CNPJ_CIA` + `CNPJ_AUDITOR`); `RESP` sem CPF. ⚠️ META é **`.txt` solto**
    de seção única (37º Meta reader), ao contrário dos `.zip` das 3 fatias anteriores. Contract
    gerado do header e pinado; `FlatCase` reusado.
  - [ ] Restante do **CIA_ABERTA** (8 datasets): `DOC/{CGVN,DFP,FCA,FRE,IPE,ITR,VLMO}` + `EVENTOS`.
    Grounding de CADA sub-dataset separado, um PR por dataset — **encerra a Wave 4**.
- [ ] **Wave 5 — processos:** ATO_DECLR, PROCESSO/SANCIONADOR.

## Open / next actions

- [ ] Per-wave `/issue`s (or one meta-issue with a checklist) so the kanban tracks the sweep.
- [ ] Begin Wave 1 with **FIDC INF_MENSAL** — inspect the zip members, derive contracts from
  `FIDC/DOC/INF_MENSAL/META/`, build one reader per member under `ingestion/fidc/doc/`.
- [ ] Root `CLAUDE.md` catalog: extend beyond the Fundos-FI section to list the new pending
  ingestion roots (done incrementally as each ships, to avoid a stale wishlist).
