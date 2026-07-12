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
