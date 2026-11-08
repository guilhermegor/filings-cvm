## ato-declr-reader-279_20261030_120000

# Work ledger — AtoDeclrReader (#279)

- [x] Measure `ato_declr.csv` and META (914 rows, ISO-8859-1, `;`, 7 cols, CNPJ_CPF mixed)
- [x] List `ATO_DECLR/` for siblings (only `INTERMED/{DADOS,META}`)
- [x] Contract generated from header + pinned fixture (header-only)
- [x] `AtoDeclrReader` + `MetaAtoDeclrReader`, root `ato_declr/`
- [x] Register contracts, `_META_MEMBERS`, `_IMPLEMENTED_PACKAGES`, `_UNEXPOSED_CONTRACTS`
- [x] Re-measure counts: 23 roots, 292 readers, 49 META readers (20 txt + 29 zip)
- [x] Docs page, nav, api.md, index.md, meta.md, CLAUDE.md
- [x] Unit tests
- [ ] PR merged (orchestrator)

## ingestion-adm-cart-cad_20260720_160310

# ADM_CART/CAD reader — `cad_adm_cart.zip` (5 membros) — issue #137

Branch `feat/137-adm-cart-cad-reader`. Wave 3 slice **6/8** of #41. Inaugurates the portal root
`adm_cart/`. **First 5-member root** — step up from the 2-member mould (AUDITOR #127 → INTERMED
#135).

## Grounding (verified against the real 2026-07-20 artifact)

- Snapshot ZIP, fixed URL, **no `date_ref`**. 5 members:
  | member | cols | rows | date cols | CNPJ |
  |---|---|---|---|---|
  | `pf` | 7 | 6.776 | 3 | no column |
  | `pj` | 24 | 3.033 | 4 | 3032/3033 valid |
  | `diretor` | 3 | 1.718 | **0** | 1718/1718 |
  | `resp` | 3 | 6.637 | **0** | 6636/6637 |
  | `socios` | 2 | 7.942 | **0** | 7942/7942 |
- ⚠️ **NEW SHAPE — 3 of 5 members have no date column at all** (`diretor`/`resp`/`socios`), the
  first in the library → `_DATE_COLS=()`. Proven `apply_dtypes(..., list_date_cols=())` works before
  writing; META confirms those three declare no `date` field.
- `pf` keyed by `ADMIN` (name), **no CNPJ nor CPF** → `tuple_cnpj_cols=()`.
- Satellites carry personal data (`DIRETOR`/`RESP`/`SOCIOS`, `SOCIOS` mixes PF+PJ) but **no CPF
  column** → `tuple_cnpj_cols=("CNPJ",)` (the manager's), fixtures header-only (LGPD).
- ⚠️ **One genuinely malformed source CNPJ**: `00.010.354/1901-72` in `pj` and `resp`, fails mod-11.
  `tuple_cnpj_cols` requires *at least one* valid → contracts pass, value honoured as published
  (pinned by `test_read_tolerates_a_malformed_cnpj_among_valid_ones`).
- `pj` uses `DDD` (like AGENTE_AUTON), not `DDD_TEL`. `CEP`/`TEL` `numeric` in META → kept `str`.
- META URL confirmed `ADM_CART/CAD/META/meta_cad_adm_cart.zip` (5 members, alphabetical). All 5
  members carry the `<stem>_` suffix → section labels **symmetric** (no INTERMED-style asymmetry).

## Done

- [x] Grounded against the real artifact + META (URL probed, types read, CNPJ validity checked)
- [x] Header fixtures pinned verbatim (`tests/fixtures/cad_adm_cart/*_header.csv`, ISO-8859-1/CRLF)
- [x] Contracts generated from + pinned to headers (`_internal/config/contracts/cad_adm_cart.py`)
- [x] `_base_adm_cart_reader.py` + 5 readers (pf/pj/diretor/resp/socios)
- [x] `MetaAdmCartReader` (29th) + `META_CAD_ADM_CART` in contracts/meta.py
- [x] Registered in `bin/check_contract_drift.py` `_META_MEMBERS`
- [x] Wired all `__init__` layers (nested + flat) + `__all__` (163 public names, 29 Meta readers)
- [x] Tests `tests/unit/test_adm_cart_ingestion.py` (incl. dateless-member + malformed-CNPJ +
      no-CPF tests) + `test_meta_readers.py` count 28→29
- [x] Docs: page + mkdocs nav + api.md + ingestion index + meta.md + root CLAUDE.md (catalog + layout)
- [x] #41 survey ledger ticked (ADM_CART ✅ #137)

- [x] Gates: ruff ✅ · mypy (291 files) ✅ · check_typing ✅ · check_provenance ✅ · unit suite
      **1601 green** ✅ · mkdocs --strict ✅ · codespell ✅
- [x] Live-verified: pf 6.776, pj 3.033, diretor 1.718, resp 6.637, socios 7.942; dateless members
      all-text; `CEP` `str`; malformed CNPJ present in `resp`; META 5 symmetric sections; provenance
      stamped

## Remaining

- [ ] All pre-commit hooks (run at commit time)
- [ ] Commit → PR `Closes #137` → wait approval + merge → release PATCH
- [ ] AFTER merge: update sweep checkpoint memory (Wave 3 → 6/8), NEXT = CONSULTOR_VLMOB (5 membros)

## ingestion-adm-fii-cad_20260721_212733

# Work ledger — ADM_FII/CAD ingestion reader (#141)

Branch `feat/141-adm-fii-cad-reader`. Adds `CadastroAdmFiiReader` over `cad_adm_fii.csv`
(`ADM_FII/CAD`), inaugurating the `adm_fii/` portal root. **Eighth and final slice of Wave 3 of
#41 — closes Wave 3 (8/8 service-provider registries).**

The only Wave 3 member that is a **flat CSV** (not a multi-member ZIP): one reader, molded on
`CadastroFiReader` / `CadastroEmissorCepacReader`, not the `_base_*_reader.py` sibling pattern.

## Grounding (real bytes)

- `cad_adm_fii.csv`: ISO-8859-1, CRLF, `;`-delimited, **18 columns**, 135 data rows, fixed URL
  (snapshot — CVM overwrites in place, so **no `date_ref`**).
- Columns: `CNPJ;DENOM_SOCIAL;DENOM_COMERC;DT_REG;DT_CANCEL;MOTIVO_CANCEL;SIT;DT_INI_SIT;TP_ENDER;`
  `LOGRADOURO;COMPL;BAIRRO;MUN;UF;CEP;DDD;TEL;EMAIL`.
- 3 date cols: `DT_REG`, `DT_CANCEL`, `DT_INI_SIT`. ⚠️ `MOTIVO_CANCEL` is **free text**, not a date.
- Keyed by `CNPJ` (masked, institution); **no CPF column** — no personal data.
- `CEP`/`DDD`/`TEL` are `numeric` in META but kept `str` (identifiers). Uses `DDD` (not `DDD_TEL`).
- META `meta_cad_adm_fii.txt` exists (flat `.txt`, 18 fields, alphabetical order — the known
  "META order ≠ file order"). 31st Meta reader.

## Done

- [x] Contract `_internal/config/contracts/cad_adm_fii.py` (`CAD_ADM_FII`, 18 cols, verified vs real
      bytes) + re-export in `contracts/__init__.py`.
- [x] `META_CAD_ADM_FII` in `contracts/meta.py` + re-export.
- [x] Reader `ingestion/adm_fii/cad/cadastro/cadastro.py` (`CadastroAdmFiiReader`).
- [x] `MetaCadAdmFiiReader` (`ingestion/adm_fii/cad/cadastro/meta.py`) — 31st Meta reader.
- [x] 3 nested `__init__.py` (cadastro / cad / adm_fii) + flat re-export in `ingestion/__init__.py`
      and top `filings_cvm/__init__.py` (imports + `__all__`).
- [x] Drift registry `bin/check_contract_drift.py`: `CAD_ADM_FII` import,
      `_UNEXPOSED_CONTRACTS["CadastroAdmFiiReader"]`, `_META_MEMBERS["MetaCadAdmFiiReader"]`.
- [x] Tests: added `CadastroAdmFiiReader` `FlatCase` to `tests/unit/test_securit_cepac_flat_ingestion.py`
      (reuses the flat-CSV harness — 6 parametrized tests); bumped `test_meta_readers.py` 30 → 31.
- [x] Docs: `docs/ingestion/adm_fii.md` + mkdocs nav + `docs/api.md` (new section + Meta list 30→31)
      + `docs/ingestion/index.md` + root `CLAUDE.md` catalog + Layout tree + META count 30→31.
- [x] Gates: ruff format+check, mypy (308 files), check_typing, check_provenance, **full unit suite
      1675 passed**.
- [x] Live-verified vs real CVM bytes: 135 rows, 18 source + 6 provenance cols, `DT_REG`→date,
      `MOTIVO_CANCEL`→str, META 18 fields keyed `meta_cad_adm_fii`.

## Remaining

- [ ] Full pre-commit run on changed files + `mkdocs --strict`.
- [ ] Commit → PR `Closes #141` → wait for approval + merge.
- [ ] After merge: release PATCH; update sweep checkpoint memory (Wave 3 → **8/8 DONE**).

## ingestion-agente-auton-cad_20260720_065232

# Work ledger — AGENTE_AUTON/CAD reader (#131)

Issue **#131**. Branch `feat/131-agente-auton-cad-reader`. Third PR of **Wave 3** of #41
(service-provider CAD snapshots), tracked in #122. Ships the `agente_auton/` portal root.

## Grounding (real 2026 bytes)

- `cad_agente_auton.zip` = **2 members**: `cad_agente_auton_pf.csv` (6 cols, ~49,339 rows),
  `cad_agente_auton_pj.csv` (19 cols, ~4,794 rows). Snapshot at a fixed URL → **no `date_ref`**.
- **pf** = `NOME;DT_REG;DT_CANCEL;MOTIVO_CANCEL;SIT;DT_INI_SIT` — **no CPF**; keyed by `NOME`, which
  **can arrive blank** (no unique key) → `tuple_cnpj_cols=()`.
- **pj** = `CNPJ;DENOM_SOCIAL;DENOM_COMERC;DT_REG;DT_CANCEL;MOTIVO_CANCEL;SIT;DT_INI_SIT;TP_ENDER;LOGRADOURO;COMPL;BAIRRO;MUN;UF;CEP;DDD;TEL;EMAIL;SITE_ADMIN`.
  `CNPJ` **masked** (`49.270.551/0001-64`) → validates; `tuple_cnpj_cols=("CNPJ",)`.
- ⚠️ **NOT a copy of AUDITOR/AGENTE_FIDUC**: adds `MOTIVO_CANCEL`, `DENOM_COMERC`, `EMAIL`,
  `SITE_ADMIN`; uses `DDD` (not `DDD_TEL`). 3 date cols (`DT_REG`, `DT_CANCEL`, `DT_INI_SIT`);
  `MOTIVO_CANCEL` is free text, NOT a date. Contracts generated from the header, pinned to fixtures.
- META = `meta_cad_agente_auton.zip`, 2 members (pf/pj) → one `MetaAgenteAutonReader` (26th).
- Live-verified: pf=49,339, pj=4,794 rows; 3 dates coerce; masked CNPJ validates; META=25 field rows
  (sections pf/pj); provenance stamped.

## Done

- [x] Contracts `_internal/config/contracts/cad_agente_auton.py` (`CAD_AGENTE_AUTON_PF/PJ`),
      generated from + pinned to `tests/fixtures/cad_agente_auton/*_header.csv` (verbatim, header-only).
- [x] `_base_agente_auton_reader.py` + `agente_auton_pf.py`, `agente_auton_pj.py`, `meta.py`
      (`MetaAgenteAutonReader`, the 26th Meta reader).
- [x] `META_CAD_AGENTE_AUTON` in `contracts/meta.py`; `MetaAgenteAutonReader` registered in
      `bin/check_contract_drift.py` `_META_MEMBERS`.
- [x] Wiring: `agente_auton/__init__.py` + `agente_auton/cad/__init__.py`; flat re-exports in
      `ingestion/__init__.py` and top `filings_cvm/__init__.py` (+ `__all__`); `contracts/__init__.py`.
- [x] Tests `tests/unit/test_agente_auton_ingestion.py` (mirrors AGENTE_FIDUC). Bumped
      `test_meta_readers.py` 25→26.
- [x] Docs: `docs/ingestion/agente_auton.md` + mkdocs nav + `api.md` (new section, Meta 25→26) +
      ingestion index + `meta.md` (25→26 + row) + root `CLAUDE.md` catalog & layout.
- [x] Gates: ruff + mypy clean; `check_typing` + `check_provenance` pass; new + meta + drift unit
      tests green (62). Live-verified against real CVM bytes.

## Remaining

- [ ] Full unit suite; codespell; `mkdocs --strict`; all pre-commit hooks.
- [ ] Commit → PR `Closes #131` → CodeQL (empty-commit re-trigger only if it drops) → admin-merge →
      release PATCH (0.25.9).
- [ ] Next Wave 3 roots: INVNR, INTERMED (2-member), then ADM_CART, CONSULTOR_VLMOB (5-member),
      ADM_FII (flat). ⚠️ Check each `pf` for CPF (AUDITOR/AGENTE_FIDUC/AGENTE_AUTON had none, but
      others may) — keep out of `tuple_cnpj_cols`, header-only fixtures.

## ingestion-agente-fiduc-cad_20260719_210855

# Work ledger — AGENTE_FIDUC/CAD reader (#129)

Issue **#129**. Branch `feat/129-agente-fiduc-cad-reader`. Second PR of **Wave 3** of #41
(service-provider CAD snapshots), tracked in #122. Ships the `agente_fiduc/` portal root.

## Grounding (real 2026 bytes)

- `cad_agente_fiduc.zip` = **2 members**: `cad_agente_fiduc_pf.csv` (5 cols, 47 rows),
  `cad_agente_fiduc_pj.csv` (15 cols, 70 rows). Snapshot at a fixed URL → **no `date_ref`**.
- **pf** = `AGENTE_FIDUC;DT_REG;DT_CANCEL;SIT;DT_INI_SIT` — **no CPF, no `CD_CVM`**, identifies a
  person agent by **name alone** → `tuple_cnpj_cols=()`.
- **pj** = `CNPJ;DENOM_SOCIAL;DT_REG;DT_CANCEL;SIT;DT_INI_SIT;LOGRADOURO;COMPL;BAIRRO;MUN;UF;PAIS;CEP;DDD_TEL;TEL`.
  `CNPJ` **masked** (`00.271.457/0001-30`) → validates via `br_identifiers`; `tuple_cnpj_cols=("CNPJ",)`.
- ⚠️ **NOT a copy of AUDITOR**: **3 date cols** (`DT_REG`, `DT_CANCEL`, `DT_INI_SIT`) vs 1; no
  `CD_CVM`; pj adds `PAIS`/`DDD_TEL`/`TEL`. `DT_CANCEL` blank for active records. Contracts generated
  from the header, pinned to fixtures — never derived from the sibling.
- META = `meta_cad_agente_fiduc.zip`, 2 members (pf/pj) → one `MetaAgenteFiducReader` (25th),
  `_MEMBER_STEM="cad_agente_fiduc"`.
- Live-verified: pf=47, pj=70 rows; 3 dates coerce; masked CNPJ validates; META=20 field rows
  (sections pf/pj); provenance stamped.

## Done

- [x] Contracts `_internal/config/contracts/cad_agente_fiduc.py` (`CAD_AGENTE_FIDUC_PF/PJ`),
      generated from + pinned to `tests/fixtures/cad_agente_fiduc/*_header.csv` (verbatim, header-only).
- [x] `_base_agente_fiduc_reader.py` + `agente_fiduc_pf.py`, `agente_fiduc_pj.py`, `meta.py`
      (`MetaAgenteFiducReader`, the 25th Meta reader).
- [x] `META_CAD_AGENTE_FIDUC` in `contracts/meta.py`; `MetaAgenteFiducReader` registered in
      `bin/check_contract_drift.py` `_META_MEMBERS`.
- [x] Wiring: `agente_fiduc/__init__.py` + `agente_fiduc/cad/__init__.py`; flat re-exports in
      `ingestion/__init__.py` and top `filings_cvm/__init__.py` (+ `__all__`); `contracts/__init__.py`.
- [x] Tests `tests/unit/test_agente_fiduc_ingestion.py` (mirrors AUDITOR, incl. the anti-tautology
      header test). Bumped `test_meta_readers.py` 24→25.
- [x] Docs: `docs/ingestion/agente_fiduc.md` + mkdocs nav + `api.md` (new section, Meta 24→25) +
      ingestion index + `meta.md` (24→25 + row) + root `CLAUDE.md` catalog & layout.
- [x] Gates: ruff + mypy clean; `check_typing` + `check_provenance` pass; new + meta + drift unit
      tests green (62). Live-verified against real CVM bytes.

## Remaining

- [ ] Full unit suite; codespell; `mkdocs --strict`; all pre-commit hooks.
- [ ] Commit → PR `Closes #129` → CodeQL (may need the `--allow-empty` push re-trigger — see the
      `codeql-default-setup-drops-a-pr-dispatch` lesson) → admin-merge → release PATCH.
- [ ] Next Wave 3 roots: AGENTE_AUTON, INVNR, INTERMED (2-member), then ADM_CART, CONSULTOR_VLMOB
      (5-member), ADM_FII (flat). ⚠️ Their `pf` members likely DO carry CPF — keep out of
      `tuple_cnpj_cols`, header-only fixtures.

## ingestion-auditor-cad_20260719_144821

# Work ledger — AUDITOR/CAD reader (#127)

Issue **#127**. Branch `feat/127-auditor-cad-reader`. First PR of **Wave 3** of #41 (service-provider
CAD snapshots), tracked in #122. Ships the `auditor/` portal root.

## Grounding (real 2026 bytes)

- `cad_auditor.zip` = **2 members** (not a flat CSV): `cad_auditor_pf.csv` (4 cols), `cad_auditor_pj.csv`
  (12 cols). Snapshot at a fixed URL, so **no `date_ref`** (the `CadastroFiReader` mould).
- **pf has no CPF column** — `CD_CVM;AUDITOR;SIT;DT_INI_SIT`. Identifies a person auditor by code +
  name, so `tuple_cnpj_cols=()`.
- **pj**: `CD_CVM;CNPJ;DENOM_SOCIAL;SIT;DT_INI_SIT;TP_ENDER;LOGRADOURO;COMPL;BAIRRO;MUN;UF;CEP`.
  `CNPJ` is **masked** (`36.348.092/0001-42`) → validates via `br_identifiers`; `tuple_cnpj_cols=("CNPJ",)`.
- Only date column: `DT_INI_SIT` (META type=`date`, confirmed). `CD_CVM`/`CEP` numeric-in-META but
  kept as **text** (leading zeros).
- META = `meta_cad_auditor.zip`, 2 members (`meta_cad_auditor_pf.txt`, `_pj.txt`), ISO-8859-1+CRLF →
  one `MetaAuditorReader`, `_MEMBER_STEM="cad_auditor"`.
- Live-verified: pf=30 rows, pj=491 rows, dates coerce, provenance stamped, META=16 field rows
  (sections `pf`/`pj`).

## Done

- [x] Contracts `_internal/config/contracts/cad_auditor.py` (`CAD_AUDITOR_PF`, `CAD_AUDITOR_PJ`),
      generated from + pinned to `tests/fixtures/cad_auditor/*_header.csv` (verbatim, header-only).
- [x] `_base_auditor_reader.py` (mirrors `_base_cad_fi_hist_reader.py`) + `auditor_pf.py`,
      `auditor_pj.py`, `meta.py` (`MetaAuditorReader`, the 24th Meta reader).
- [x] `META_CAD_AUDITOR` in `contracts/meta.py`; `MetaAuditorReader` registered in
      `bin/check_contract_drift.py` `_META_MEMBERS` (multi-member readers expose `_CONTRACT`, so no
      `_UNEXPOSED` entry needed).
- [x] Wiring: `auditor/__init__.py` + `auditor/cad/__init__.py`; flat re-exports in
      `ingestion/__init__.py` and top `filings_cvm/__init__.py` (+ `__all__`); `contracts/__init__.py`.
- [x] Tests `tests/unit/test_auditor_ingestion.py` (mirrors `test_cad_fi_hist_ingestion.py`) incl. the
      anti-tautology `test_contract_matches_the_published_header`. Bumped `test_meta_readers.py` 23→24.
- [x] Docs: `docs/ingestion/auditor.md` + mkdocs nav + `api.md` (new section, Meta 23→24) + ingestion
      index + root `CLAUDE.md` catalog & layout. **Also fixed pre-existing meta.md drift**: it under-
      counted (22) and was missing the CRI row (the #114 PR omitted it) → now 24 with CRI + AUDITOR
      rows and the stale "CRI ainda não tem readers" note removed.
- [x] Gates: ruff + mypy clean on new files; `check_typing` + `check_provenance` pass; AUDITOR + meta
      + drift unit tests green (62). Live-verified against real CVM bytes.

## Remaining

- [ ] Full unit suite under pandas 3.x **and** 2.x; codespell; `mkdocs --strict`; all pre-commit hooks.
- [ ] Commit → PR `Closes #127` → wait approval+merge → release **PATCH**.
- [ ] Next Wave 3 roots (copy this mould): AGENTE_FIDUC, AGENTE_AUTON, INVNR, INTERMED (2-member),
      then ADM_CART, CONSULTOR_VLMOB (5-member), ADM_FII (flat). Some `pf` members **do** carry CPF —
      keep it out of `tuple_cnpj_cols`, header-only fixtures.

## ingestion-consultor-vlmob-cad_20260720_172626

# CONSULTOR_VLMOB/CAD reader — `cad_consultor_vlmob.zip` (5 membros) — issue #139

Branch `feat/139-consultor-vlmob-cad-reader`. Wave 3 slice **7/8** of #41. Inaugurates the portal
root `consultor_vlmob/`. Same 5-member shape as ADM_CART (#137). **Closes the 5-member roots** —
only ADM_FII (flat CSV) remains to end Wave 3.

## Grounding (verified against the real 2026-07-20 artifact)

- Snapshot ZIP, fixed URL, **no `date_ref`**. 5 members:
  | member | cols | rows | date cols | CNPJ |
  |---|---|---|---|---|
  | `pf` | 7 | 3.743 | 3 | no column |
  | `pj` | 20 | 1.031 | 3 | 1031/1031 valid |
  | `diretor` | 3 | 725 | **0** | 725/725 |
  | `resp` | 3 | 1.557 | **0** | 1557/1557 |
  | `socios` | 2 | 1.862 | **0** | 1862/1862 |
- Same dateless-member shape as ADM_CART (`diretor`/`resp`/`socios` → `_DATE_COLS=()`); META
  confirms those three declare no `date` field.
- ⚠️ **NOT a copy of ADM_CART** — each contract generated from its own header:
  - `pf` keyed by **`NOME`** (not `ADMIN`); 7th column **`SITE_ADMIN`** (not `CATEG_REG`).
  - `pj` has **20 cols** (ADM_CART 24): no `CATEG_REG`/`SUBCATEG_REG`/`VL_PATRIM_LIQ`/
    `DT_PATRIM_LIQ` → **only 3 date cols**, not 4. Pinned by
    `test_pj_has_three_date_columns_not_four`.
- `pf` has **no CNPJ nor CPF** → `tuple_cnpj_cols=()`. Satellites carry personal data but **no CPF**
  → keyed on the consultant's CNPJ. **All CNPJ 100% valid** (no malformed value like ADM_CART's).
- `CEP`/`TEL` `numeric` in META → kept `str`. `pj` uses `DDD` (not `DDD_TEL`).
- META URL confirmed `CONSULTOR_VLMOB/CAD/META/meta_cad_consultor_vlmob.zip` (5 members,
  alphabetical). All members carry the `<stem>_` suffix → section labels **symmetric**.

## Done

- [x] Grounded against the real artifact + META (URL probed, types read, CNPJ validity checked)
- [x] Header fixtures pinned verbatim (`tests/fixtures/cad_consultor_vlmob/*_header.csv`)
- [x] Contracts generated from + pinned to headers (`_internal/config/contracts/cad_consultor_vlmob.py`)
- [x] `_base_consultor_vlmob_reader.py` + 5 readers (pf/pj/diretor/resp/socios)
- [x] `MetaConsultorVlmobReader` (30th) + `META_CAD_CONSULTOR_VLMOB` in contracts/meta.py
- [x] Registered in `bin/check_contract_drift.py` `_META_MEMBERS`
- [x] Wired all `__init__` layers (nested + flat) + `__all__` (169 public names, 30 Meta readers)
- [x] Tests `tests/unit/test_consultor_vlmob_ingestion.py` (incl. dateless-member + pj-3-date-cols
      anti-copy + no-CPF tests) + `test_meta_readers.py` count 29→30
- [x] Docs: page + mkdocs nav + api.md + ingestion index + meta.md + root CLAUDE.md (catalog + layout)
- [x] #41 survey ledger ticked (CONSULTOR_VLMOB ✅ #139)

- [x] Gates: ruff ✅ · ruff format ✅ · mypy (301 files) ✅ · check_typing ✅ · check_provenance ✅ ·
      unit suite **1661 green** ✅ · mkdocs --strict ✅ · codespell ✅
- [x] Live-verified: pf 3.743, pj 1.031 (no `DT_PATRIM_LIQ` column), diretor 725, resp 1.557,
      socios 1.862; dateless members all-text; `CEP` `str`; META 5 symmetric sections; provenance
      stamped

## Remaining

- [ ] All pre-commit hooks (run at commit time)
- [ ] Commit → PR `Closes #139` → wait approval + merge → release PATCH
- [ ] AFTER merge: update sweep checkpoint memory (Wave 3 → 7/8), NEXT = **ADM_FII** (flat CSV,
      18 cols) which **closes Wave 3**

## ingestion-intermed-cad_20260720_122616

# INTERMED/CAD reader — `cad_intermed.zip` (intermed + resp) — issue #135

Branch `feat/135-intermed-cad-reader`. Wave 3 slice **5/8** of #41. Inaugurates the portal root
`intermed/`. Mould: AUDITOR (#127) → AGENTE_FIDUC (#129) → AGENTE_AUTON (#131) → INVNR (#133).

## Grounding (verified against the real 2026-07-20 artifact)

- Snapshot ZIP, fixed URL, **no `date_ref`**.
- ⚠️ **The 2 members are NOT a `pf`/`pj` split** — the first departure from the mould:
  `cad_intermed.csv` (28 cols, 2.352 rows, the registry) + `cad_intermed_resp.csv` (8 cols, 5.545
  rows, responsible officers), **both keyed by the intermediary's `CNPJ`** (masked, 100% filled).
- Date cols: registry **4** (`DT_REG`/`DT_CANCEL`/`DT_INI_SIT`/`DT_PATRIM_LIQ`), resp **2**
  (`DT_REG`/`DT_INI_RESP`). `MOTIVO_CANCEL` is text (`varchar` in META), not a date.
- ⚠️ `resp` carries **personal data** (`RESP` name, `EMAIL_RESP`) but **no CPF column** → both
  members get `tuple_cnpj_cols=("CNPJ",)` (the intermediary's), fixtures header-only (LGPD).
- ⚠️ `CEP`/`TEL`/`FAX`/`DDD_TEL`/`DDD_FAX`/`CD_CVM` declared `numeric`/`char` in META → kept `str`
  (identifiers; `DDD_TEL` already arrives `'051'`, leading zero intact only as text).
- META URL confirmed `INTERMED/CAD/META/meta_cad_intermed.zip` (2 members, alphabetical order).
- `find_member` verified exact-match, so `cad_intermed.csv` cannot collide with the longer
  `cad_intermed_resp.csv` — covered by a test.
- ⚠️ **META `section` labels are asymmetric: `cad_intermed` + `resp`** (not a tidy pair). Surfaced
  on live-verify. `meta_cad_intermed.txt` is the bare `_MEMBER_STEM` with no `<stem>_` suffix to
  strip, so the base's `_section_of` falls back to the whole stem; the sibling reduces to `resp`.
  That fallback is the base's **documented** behaviour and both labels stay distinct — so it is
  honoured and pinned by a test, **not** "fixed" by special-casing the shared base.

## Done

- [x] Grounded against the real artifact + META (URL probed, types read, values sampled)
- [x] Header fixtures pinned verbatim (`tests/fixtures/cad_intermed/*_header.csv`, ISO-8859-1/CRLF)
- [x] Contracts generated from + pinned to headers (`_internal/config/contracts/cad_intermed.py`)
- [x] `_base_intermed_reader.py` + `IntermedReader` + `IntermedRespReader`
- [x] `MetaIntermedReader` (28th) + `META_CAD_INTERMED` in contracts/meta.py
- [x] Registered in `bin/check_contract_drift.py` `_META_MEMBERS`
- [x] Wired all `__init__` layers (nested + flat) + `__all__` (157 public names, 28 Meta readers)
- [x] Tests `tests/unit/test_intermed_ingestion.py` (incl. distinct-columns anti-copy test +
      exact-member-selection test) + `test_meta_readers.py` count 27→28
- [x] Docs: page + mkdocs nav + api.md + ingestion index + meta.md + root CLAUDE.md (catalog + layout)
- [x] #41 survey ledger ticked (INTERMED ✅ #135; also ticked INVNR ✅ #133, whose line was left open)

- [x] Gates: ruff ✅ · mypy (281 files) ✅ · check_typing ✅ · check_provenance ✅ · unit suite
      **1541 green** ✅ · mkdocs --strict ✅ · codespell ✅
- [x] Live-verified against the real bytes: intermed 2.352 rows, resp 5.545; `DDD_TEL` keeps its
      leading zero (`'051'`, `str`); CNPJ masked and identical across both members; no CPF column
      in `resp`; META 2 sections; provenance stamped

## Remaining

- [ ] All pre-commit hooks (run at commit time)
- [ ] Commit → PR `Closes #135` → wait approval + merge → release PATCH
- [ ] AFTER merge: update sweep checkpoint memory (Wave 3 → 5/8), NEXT = ADM_CART (5 membros)

## ingestion-invnr-cad_20260720_101243

# INVNR/CAD reader — `cad_invnr_repres.zip` (pf + pj) — issue #133

Branch `feat/133-invnr-cad-reader`. Wave 3 slice **4/8** of #41. Inaugurates the portal root
`invnr/`. Mould: AUDITOR (#127) → AGENTE_FIDUC (#129) → AGENTE_AUTON (#131).

## Grounding (verified against the real 2026-07-20 artifact)

- Snapshot ZIP, fixed URL, **no `date_ref`**. `pf` = 6 cols / 1.370 rows, `pj` = 23 cols / 887 rows.
- `pf` has **no CPF** (key = `NOME`); `pj.CNPJ` masked (`76.621.457/0001-85`, 887/887 filled).
- `pj` adds `CONTROLE_ACIONARIO`, `DDD_FAX`/`FAX`, `VL_PATRIM_LIQ`, `DT_PATRIM_LIQ` → **4 date cols**
  vs pf's 3. Uses `DDD_TEL` (not AGENTE_AUTON's `DDD`).
- META URL confirmed `INVNR/CAD/META/meta_cad_invnr_repres.zip` (2 members, alphabetical order).
  META declares `CEP`/`TEL`/`FAX` `numeric` → kept `str` (identifiers; `CEP` already arrives with
  leading zero dropped). `MOTIVO_CANCEL` = `varchar` (text, not date); `DT_PATRIM_LIQ` = `date`.

## Done

- [x] Grounded against the real artifact + META (URL probed, types read)
- [x] Header fixtures pinned verbatim (`tests/fixtures/cad_invnr_repres/*_header.csv`, ISO-8859-1/CRLF)
- [x] Contracts generated from + pinned to headers (`_internal/config/contracts/cad_invnr_repres.py`)
- [x] `_base_invnr_repres_reader.py` + `InvnrRepresPfReader` + `InvnrRepresPjReader`
- [x] `MetaInvnrRepresReader` (27th) + `META_CAD_INVNR_REPRES` in contracts/meta.py
- [x] Registered in `bin/check_contract_drift.py` `_META_MEMBERS`
- [x] Wired all `__init__` layers (nested + flat) + `__all__` (154 public names, 27 Meta readers)
- [x] Tests `tests/unit/test_invnr_repres_ingestion.py` + `test_meta_readers.py` count 26→27
- [x] Docs: page + mkdocs nav + api.md + ingestion index + meta.md + root CLAUDE.md (catalog + layout)
- [x] #41 survey ledger ticked (INVNR ✅ #133)

## Remaining

- [ ] Gates: ruff + mypy + check_typing + check_provenance + full unit suite + mkdocs --strict +
      all pre-commit hooks
- [ ] Live-verify readers against the real bytes (download boundary real)
- [ ] Commit → PR `Closes #133` → wait approval + merge → release PATCH
- [ ] AFTER merge: update sweep checkpoint memory (Wave 3 → 4/8), NEXT = INTERMED

## processo-sancionador-reader-289_20261031_120000

# Work ledger — Processo Sancionador reader (#289)

- [x] Measure `processo_sancionador.zip` (2 members, ISO-8859-1, `;`, CRLF, snapshot) and the META zip
- [x] No CNPJ/CPF column in either member; `Nome_Acusado` is PII, so header-only fixtures
- [x] Contracts generated from the real headers and pinned to verbatim fixtures
- [x] Readers `ProcessoSancionadorReader`, `ProcessoSancionadorAcusadoReader`, `MetaProcessoSancionadorReader`; new root `processo/`
- [x] Registered in `ingestion/__init__.py`, contracts `__init__`, `_META_MEMBERS`, `_IMPLEMENTED_PACKAGES` (`processo-sancionador`)
- [x] Re-measured counts from code: 23 roots, 293 readers, 49 META readers (19 txt + 30 zip, 49 contracts)
- [x] Docs page, nav, api.md, index.md, meta.md, CLAUDE.md catalog and layout
- [x] Unit tests; real artifact read end to end with the download mocked to the real bytes (581 + 2070 rows)
- [ ] PR merged (orchestrator); counts conflict with #282/#283/#287/#288 resolved at merge
