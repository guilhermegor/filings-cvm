# Ledger — #117 drift job false positives (subset contracts)

Branch: `fix/117-drift-subset-contracts` · Issue: #117 · Class: **ci** (no `src/` diff → no release)

## Goal

Stop the drift job (#98) crying wolf. Its first live run opened #115 with **123 findings, ~120
false positives** — it treated `tuple_required` ("must contain at least these") as a full column
list, so subset/partial-coverage datasets flagged every column they don't list.

## Root cause (from #115, parsed authoritatively)

- **CDA (110)** — `CdaReader` requires 4 of ~60 columns (a deliberate subset contract).
- **Lâmina (10)** — the dataset META describes `rentab_ano`/`rentab_mes` members not implemented yet.
- **FIDC (2) + FII inf_anual (1)** — genuine residual signal (META-vs-header identity naming:
  `CNPJ_FUNDO` / `Nome_Fundo` / `ID_SUBCLASSE`), NOT bulk noise — kept.

## Work (option 2: mark full-column vs partial)

- [x] `real_header_drift` / `meta_name_drift` gain `bool_report_extra: bool = True`; when `False`,
      the **extra-column** direction is skipped and **required-missing** is always kept.
- [x] `_PARTIAL_DATASETS` (keyed by Meta reader, with a reason each): `MetaCdaReader` (subset) +
      `MetaLaminaReader` (unimplemented rentab members). Grounded in #115.
- [x] `_READER_TO_META` reverse map derived from `_META_MEMBERS` (so the per-member header check
      learns whether its dataset is partial; can't drift from the registry).
- [x] `check_real_header` / `check_meta` pass the flag from those.
- [x] Tests: pure-function suppression (both directions), online-check suppression via fakes +
      monkeypatch, and structural (`_PARTIAL_DATASETS` keys are real Meta readers; `_READER_TO_META`
      is the exact inverse of the registry). 33 drift tests.
- [x] **Live-verified against real CVM**: CDA + Lâmina now report **0** (120 noise gone); FIDC (2)
      + FII (1) residuals **still reported** (signal preserved); CRI **stays clean** (no
      over-suppression). Net: **123 → 3**.
- [x] Docs: `docs/ingestion/contract_drift.md` "Cobertura parcial" section.

## After merge

- [ ] Re-dispatch the drift workflow; confirm #115 drops from 123 to ~3, then **triage the 3
      residuals** (FIDC/FII identity-naming) — likely a small follow-up or a `_PARTIAL_DATASETS`
      addition if they prove to be META-granularity artifacts too.
- [ ] Secondary scope (separate decision): should CDA/Lâmina be upgraded to full-header-pinned
      contracts (the pinned-oracle lesson)? Not in this PR.

## Not done, on purpose

- No gate parity — the drift workflow stays out of pre-commit/CI gates (non-blocking by design).
