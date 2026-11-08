## ingestion-fiagro-inf-mensal_20260712_065426

# Work ledger — FIAGRO Informe Mensal readers (#74)

Issue **#74** · branch `feat/ingestion-fiagro-inf-mensal`. Wave 1 of the #41 portal sweep
(FIDC→FII→FIP→**FIAGRO**→FIE). Inaugurates the **`fiagro/` portal root** (sibling of
`fi/`/`fidc/`/`fii/`/`fip/`).

Excluded from the docs site (`backlog/`). Never deleted — on completion tick the last box and add
a "Completed — kept as a record" note, per `docs/CLAUDE.md`.

## Grounding (real `202506` artifact — META + bytes)

- Dataset `FIAGRO/DOC/INF_MENSAL`; dump `inf_mensal_fiagro_AAAAMM.zip`, **monthly-partitioned**
  (`_AAAAMM`), series starts **202505**. META shipped as a zip (`meta_inf_mensal_fiagro.zip`,
  2 `.txt` members).
- **2 members** → 2 readers over a private base (mirrors `fidc/doc/inf_mensal/`):
  - `inf_mensal_fiagro_AAAAMM.csv` — **133 cols**, informe proper. Grain: one row per class ×
    month (`CNPJ_Classe`, `Data_Referencia`) — 18 unique rows in `202506`. Date cols:
    `Data_Referencia`, `Data_Entrega`, `Data_Registro`. → `InfMensalFiagroReader`.
  - `inf_mensal_fiagro_subclasse_AAAAMM.csv` — **6 cols**, long (38 rows, one per subclasse).
    Date col: `Data_Referencia`. → `InfMensalFiagroSubclasseReader`.
- Post-RCVM 175 nomenclature (Classe/Subclasse). CNPJ key col: `CNPJ_Classe`.
- **CVM spellings preserved verbatim**: `Provisoes_Contigencias` (missing *n*) and asymmetric
  `A_Vencer_Acima1080_Dias` (extra `_`) vs `Vencidos_Acima1080Dias` (none). Column tuples
  generated from the real CSV headers, not hand-transcribed (per the FIP lesson).
- CSV member selection is by **exact name** — `inf_mensal_fiagro` is a strict prefix of
  `inf_mensal_fiagro_subclasse`, so exact-name selection is load-bearing (locked by a test).

## Done

- [x] Contract module `_internal/config/contracts/inf_mensal_fiagro.py` (2 `FileContract`, one-per-
  file deviation noted, as `inf_mensal_fidc.py`) + re-exports in `contracts/__init__`.
- [x] Private base `_base_inf_mensal_fiagro_reader.py` — `_DATE_COLS` is **per-subclass** here
  (members differ), unlike FIDC's shared date col. `raw_workspace` + `hash_artifact` +
  `stamp_provenance` + `_RETRY_POLICY` (`_DEFAULT_RETRY_POLICY`, 5-attempt patient default).
- [x] 2 thin readers; new `fiagro/`, `fiagro/doc/`, `fiagro/doc/inf_mensal/` `__init__` chain.
- [x] Public API: `ingestion/__init__` + root `filings_cvm/__init__` (imports + `__all__`).
- [x] Docs: page `docs/ingestion/inf_mensal_fiagro.md`, mkdocs nav, `api.md` section, ingestion
  `index.md` bullet, root `CLAUDE.md` catalog (new FIAGRO root + Layout line).
- [x] Tests `tests/unit/test_inf_mensal_fiagro_ingestion.py` (16). Full suite **849 passed under
  BOTH pandas 3.0.3 and 2.3.3**. ruff/format/check_typing/check_provenance/mypy all clean.
- [x] **Live-verified** end-to-end against the real `202506` bytes (both readers parse, 133/6
  source cols + 6 provenance, dates coerced, PL kept as exact `str`, both typos present).

## Remaining

- [ ] Open PR (`Closes #74`); wait for user approval + merge.
- [ ] After merge: release (minor bump `0.22.0`→`0.23.0`) Test PyPI → verify install → PyPI →
  verify. Then next Wave 1 item: **FIE** (`FIE/DOC/BALANCETE`, `BALANCO`, `FIE/CAD`).

## ingestion-fie-root_20260712_155418

# Work ledger — FIE readers, complete the `fie/` root (#84)

Issue **#84** · branch `feat/ingestion-fie-root`. Wave 1 of #41, **final root** — completes
FIDC→FII→FIP→FIAGRO→**FIE**. Grounded in the real artifacts (META + bytes, 2026-07-12).

Excluded from the docs site (`backlog/`). Never deleted — tick the last box on completion.

## Grounding + two corrections to the #41 plan (verified from the RAW directory listing)

- ❌ **`FIE/CAD` does not exist** — `DADOS/` and `META/` are both genuinely empty (raw listing shows
  only nav links). The plan's "FIE/CAD" was aspirational. Dropped.
- ➕ **`FIE/MEDIDAS` was missing from the plan** — a real, current monthly dataset. Added.
- **`FIE/DOC/BALANCO` is discontinued**: yearly, series 2005–2020, nothing after.
- Reminder in action: the proxy first returned `FIE/CAD/DADOS` as "(empty)"; re-checking with the
  **raw** curl confirmed it is genuinely empty — "(empty)" was UNKNOWN until verified.

## 3 datasets → 3 readers (single-member each, 6 columns each, grain unique on the real file)

| Reader | Artifact | Partition | Key (regime) |
|---|---|---|---|
| `BalanceteFieReader` | `balancete_fie_AAAAMM.zip` (ZIP, 1 member) | monthly, 202401→ | `CNPJ_FUNDO_CLASSE` (post-175) |
| `BalancoFieReader` | `balanco_fie_AAAA.zip` (ZIP, 1 member) | yearly, 2005–2020 (**discontinued**) | `CNPJ_FUNDO` (pre-175) |
| `MedidasMesFieReader` | `medidas_mes_fie_AAAAMM.csv` (flat CSV) | monthly | `CNPJ_FUNDO` |

`FIE/MEDIDAS` is a **sibling of `FIE/DOC`** on the portal → its reader lives at the `fie/` root, not
under `fie/doc/`. No shared base (the FIP precedent — separate readers; the 3 differ in columns +
partition + ZIP-vs-CSV). ⚠️ MEDIDAS' real header order (`VL_PATRIM_LIQ` before `NR_COTST`) differs
from the META's alphabetical listing — column tuples taken from the **file**, not the META.

## Done

- [x] 3 contracts (`balancete_fie.py`, `balanco_fie.py`, `medidas_mes_fie.py`) + re-exports in
  `contracts/__init__`.
- [x] 3 readers: `fie/doc/balancete.py` + `fie/doc/balanco.py` (ZIP via `extract_all`+`find_member`,
  exact-name member selection), `fie/medidas.py` (flat CSV, like FIP). All carry `raw_workspace` +
  `hash_artifact` + `stamp_provenance` + per-module `_RETRY_POLICY`.
- [x] `fie/` + `fie/doc/` `__init__` chain; public API wired (`ingestion/__init__` + root
  `filings_cvm/__init__`, imports + `__all__`).
- [x] Docs: page `docs/ingestion/fie.md`, mkdocs nav, `api.md` section, ingestion `index.md` bullet,
  root `CLAUDE.md` catalog (new FIE root + Layout line) + #41 survey ledger (FIE→shipped, corrections).
- [x] Tests `tests/unit/test_fie_ingestion.py` (24, config-driven across the 3 + ZIP/partition
  specifics). Full suite **903 passed under BOTH pandas 3.0.3 and 2.3.3**. ruff/format/check_typing/
  check_provenance/check_docstrings/mypy all clean.
- [x] **Live-verified** end-to-end against the real bytes (balancete 8532 rows, balanço 48, medidas
  1974; 6 source + 6 provenance cols; dates coerced; money kept as exact `str`; provenance stamped).

## Remaining

- [ ] Open PR (`Closes #84`); wait for user approval + merge. `risk:src` → human review (correct).
- [ ] After merge: **release** — this IS a `feat` in `src/`, so a **PATCH** bump per the new policy.
  Next version must clear the **Test-PyPI floor 0.25.0** → likely **0.25.1** (PyPI is at 0.24.0; the
  release skill must compute against the max of both indices).
- [ ] Wave 1 of #41 is now COMPLETE. Next: Waves 2–5 (SECURIT, CIA_ABERTA, service-provider CADs, …)
  per `portal-survey-41_20260710_204535.md`.

## ingestion-fip_20260711_192917

# Work ledger — FIP ingestion readers (issue #66)

Branch: `feat/66-fip-ingestion`. Inaugurates the `fip/` portal root (Fundos de Investimento em
Participações) with both `FIP/DOC/` datasets — one flat-CSV reader each. One PR for the whole root
(user-chosen scope: the two readers are small and near-identical).

## Key facts (META-first, grounded in the real artifacts)

- **INF_TRIMESTRAL** — `inf_trimestral_fip_AAAA.csv`, 54 cols, keyed `CNPJ_FUNDO`, series 2010–2023
  (pre-RCVM 175 quarterly report).
- **INF_QUADRIMESTRAL** — `inf_quadrimestral_fip_AAAA.csv`, 55 cols, keyed `CNPJ_FUNDO_CLASSE`, from
  2024 (post-175, replaced the quarterly form). Column-identical to the quarterly **except the first
  two**: `TP_FUNDO_CLASSE` + `CNPJ_FUNDO_CLASSE` replace `CNPJ_FUNDO` (RCVM 175 fund/class split).
- Both are **flat year-partitioned CSVs** (not ZIPs), ISO-8859-1, `;`-separated, unquoted. Only
  `DT_COMPTC` is a date; money/quota amounts stay `str`. Structurally like `DfinFiiReader`.

## Done

- [x] Contracts `_internal/config/contracts/inf_trimestral_fip.py` (54 cols) +
      `inf_quadrimestral_fip.py` (55 cols); column tuples generated programmatically from the exact
      CSV headers (no hand-transcription). Wired into `contracts/__init__.py`.
- [x] Readers `ingestion/fip/doc/inf_trimestral.py` (`InfTrimestralFipReader`) +
      `inf_quadrimestral.py` (`InfQuadrimestralFipReader`), mirroring the DFIN flat-CSV template:
      `read_table` + `FileContract` + `raw_workspace(path_raw)` + `hash_artifact` +
      `stamp_provenance` + per-module `_RETRY_POLICY`.
- [x] New `fip/` portal root package (`ingestion/fip/__init__.py`, `ingestion/fip/doc/__init__.py`),
      flat public re-export through `ingestion/__init__.py` + top-level `filings_cvm/__init__.py`.
- [x] Tests `tests/unit/test_inf_trimestral_fip_ingestion.py` (8) +
      `test_inf_quadrimestral_fip_ingestion.py` (9, incl. RCVM-175 class-key assertion). Mock only
      `download_file`; the introspective retry-policy test auto-covers the 2 new readers.
- [x] Docs: combined page `docs/ingestion/inf_fip.md` (regime-transition story), nav entry,
      `api.md` (Veja também + FIP section), `ingestion/index.md` bullet. `mkdocs build --strict`
      green.
- [x] Root `CLAUDE.md` catalog (FIP section, 2/2 complete) + layout tree (`fip/`).
- [x] `#41` survey ledger: FIP row → shipped.
- [x] Gates: ruff check + format, mypy, check_typing, check_provenance, check_docstrings (warnings
      only), codespell — all clean. **785 unit tests pass under BOTH pandas majors (2.3.3 + 3.0.3).**

## Open / next (all require the maintainer, post-merge)

- [ ] User review of PR (approval gate).
- [ ] After merge: release (minor bump 0.20.0) Test PyPI → verify → PyPI → verify → mike docs deploy.
- [ ] Wave 1 continues: **FIAGRO** (INF_MENSAL) → **FIE** (BALANCETE, BALANCO, CAD), then Waves 2–5
      of #41.
