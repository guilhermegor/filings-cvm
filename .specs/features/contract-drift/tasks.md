## closed-series-probes-321_20261031_120000

# Probe every closed series in the contract-drift job (#321)

- [x] Measured on origin/main: `PerfilMensalPre175Reader` and `ExtratoFiPre2020Reader` refuse every rolling probe date with `ValueError`
- [x] Both added to `_CLOSED_SERIES_PROBES` (202311 and 2019), pinned by `test_closed_series_readers_are_probed_at_their_last_published_month`
- [x] Sweep test over every public reader: the first date the drift job passes must construct it
- [x] Mutation-proved: removing either entry fails both tests (snapshot restore verified with `cmp`)
- [x] Report-only drift run: both headers are now actually read (116 cols @ 2019, 106 cols @ 202311), no drift
- [x] `pytest tests/unit`: 3460 passed, 3 skipped
- [ ] Open, not in scope: `PerfilMensalReader` (series from 202312) refuses the oldest rolling date (`today - 1095 d` = 202311 until early Dec 2026). It only bites if the six newer periods all 404, then the job logs "errored" instead of "skipped"

## contract-drift-115_20261031_125457

# Triage the 135 contract-drift lines of #115

Issue #115 is bot-owned; the next weekly run proves the fix, so this branch never closes it.

## Classification of the 135 lines in the issue body

Measured 2026-10-31 against the live FRE/FII/FIDC META readers and the real archives
`fre_cia_aberta_2025.zip`, `inf_anual_fii_2025.zip`, `inf_mensal_fidc_202509.zip`,
`dfp_cia_aberta_2025.zip` and `dfp_cia_aberta_2026.zip`.

| Bucket | Lines | What |
|---|---|---|
| (a) checker bug | 0 | No line came from a wrong `_META_MEMBERS` mapping. Compared per member, all 28 FRE members that have a META section reconcile cleanly. |
| (b) known source fact | 129 | 118 from FRE META sections with no CSV in the archive (22 sections), 10 from FRE members with no META section (8 readers), 1 from FII anual `representante_cotista_fundo` (a META section with no CSV). |
| (c) real drift | 0 | All 36 FRE real headers equal their contracts exactly. `fre_cia_aberta.py` is unchanged. |
| outside the buckets | 6 | See below. They stay reported because they are real signal. |

- [x] Fetch the FRE META: 50 sections, 36 data members
- [x] Compare every FRE contract with its real 2025 header: 36/36 identical
- [x] (b) Add `_META_ONLY_SECTIONS` so a META section with no CSV in the archive adds no fields (FRE 22, FII anual 1)
- [x] (b) Add the 8 FRE members missing from the META to `_META_UNDESCRIBED_READERS`
- [x] Tests that fail before the fix: section exclusion, a new field in a described section still flagged, registry and stem guards, and the FRE undescribed set
- [x] Re-run the sweep in report-only mode and record before/after (below)

## Still open, outside this branch's claimed files

- [ ] **DFP `DFC_MD_con` / `DFC_MD_ind` (2 lines): real reader bug, not column drift.** In
  `dfp_cia_aberta_2026.zip` both members contain only the header (0 rows). The header is still
  the same 15 columns. The contract declares `tuple_cnpj_cols=("CNPJ_CIA",)`, so a read of a
  legitimately empty partition raises `ContractError`. This is the CRI header-only failure
  class. The fix belongs in `dfp_cia_aberta.py` (and probably `itr_cia_aberta.py`), which needs
  its own issue.
- [ ] **FIDC `tab_VIII` (its sequence and `VALOR` fields: 2 lines): an unimplemented member,
  real signal.** `inf_mensal_fidc_tab_VIII_AAAAMM.csv` exists in the archive (42,431 rows in
  202509; 6 columns, the 4 key columns plus a sequence number and `VALOR`), but no reader
  covers it. Needs a reader, which needs its own issue.
- [ ] **FIDC META lags the real header (`CNPJ_FUNDO` and `ID_SUBCLASSE`: 2 lines).** The META
  still lists `CNPJ_FUNDO` in `tab_X_1..X_6`. The real headers carry `CNPJ_FUNDO_CLASSE`, and
  `tab_X_1` carries `ID_SUBCLASSE`, which the META lacks. The contracts follow the real header,
  which is the authoritative oracle. This is left reported: a per-field tolerance would be a new
  mechanism for 2 lines.

## Note: a latent masking risk, not fixed

`check_meta` still reconciles META fields against the union of all members' contract columns.
A field CVM adds to section X is hidden if any other member happens to have a column with that
name. Comparing per section would need an explicit reader-to-section map for every dataset.
FRE's `_MEMBER_STEM` equals its section name, but the other datasets' naming is asymmetric.
Add the map if this ever masks a real change.

- [ ] **Complemento FI (1 line, new since the issue was posted).** `ComplFiReader`, which landed
  in #287, failed its contract at the closed-series probe date (2019-04): column `CNPJ_AG_RISCO`
  holds no valid CNPJ. That column should probably come out of `tuple_cnpj_cols`. Outside this
  branch's claimed files, so it needs its own issue.

## Before / after

Both runs used a report-only sweep (`collect_drift()`, no GitHub upsert) against this branch's
`src/` on 2026-10-31. The before run used the checker from `origin/main`, the after run the
checker from this branch.

- [x] Before: **136** (the 135 lines in the issue, plus the new Complemento FI line)
- [x] After: **7** (2 DFP, 1 Complemento FI, 4 FIDC; every one is real signal, listed above)

Completed — kept as a record. The open boxes above are follow-ups for separate issues.

## contract-drift-job-98_20260717_233826

# Ledger — #98 weekly non-blocking contract-drift job

Branch: `feat/98-contract-drift` · Issue: #98 · Class: **ci** (no `src/` diff → no release)

## Goal

Weekly, non-blocking job that fetches both oracles CVM publishes (each dataset's META and the real
artifact header), compares them to every `FileContract`, and opens/updates ONE tracking issue on
drift. Never gates a PR or a release. First internal consumer of the #97 META seam.

## Work

- [x] `bin/check_contract_drift.py` — two pure oracles (`real_header_drift`, `meta_name_drift`,
      truncation-aware on 50 chars) + online orchestration (`check_real_header` with date probing,
      `check_meta` dataset-level union) + issue upsert (label + hidden marker dedupe) + `main()`
      that always exits 0 on detected drift.
- [x] Explicit registry — `_META_MEMBERS` (22 datasets → 102 members) + `_UNEXPOSED_CONTRACTS`
      (17 single readers). Generated + validated (0 dups, 0 missing) against `ingestion.__all__`;
      the `cad_fi`/`cad_fi_hist`/`registro`/`lamina` prefix traps are explicit overrides.
- [x] `.github/workflows/contract-drift.yaml` — `schedule` (weekly) + `workflow_dispatch`, the
      "why a scheduled job" rationale written in-file, `issues: write`, exits-0 non-blocking.
- [x] `tests/unit/test_check_contract_drift.py` — 24 tests: both oracles, contract resolution,
      frame stripping, online checks (fakes, no network), issue dedupe, and the **structural
      registry-completeness** net (every reader covered exactly once; every name resolves).
- [x] `docs/ingestion/contract_drift.md` + mkdocs nav.
- [x] Gates: ruff/format/mypy clean; full unit suite green (1268); codespell clean.
- [x] `contract-drift` label created on the repo (the workflow labels its tracking issue).

## Deferred (tracked here, not in this PR)

- [ ] **Download dedupe** — one read per member re-downloads each shared archive once per member
      (documented ceiling in `collect_drift`). If the weekly job gets slow, fetch each archive once
      and read headers only. File a follow-up issue if it bites.

## Not done, on purpose

- **No gate parity** — this is a scheduled non-blocking job, deliberately NOT in `.pre-commit`
  or `tests.yaml` (a red drift check must never gate a PR/release; issue #98 + #86).

## drift-refused-date_20261031_070000

# Treat a refused probe date like a 404 in the drift check

- [x] Reproduced: `PerfilMensalReader` refuses 202311 (before its series start) with `ValueError`, and `check_real_header` let it escape, so the sweep reported "header check errored" for a reader that was fine
- [x] `check_real_header` now skips a refused date and tries the next; it re-raises only when every date was refused and none was merely unpublished
- [x] Regression tests: one refused date among 404s is "no artifact found"; every date refused still reports

Completed — kept as a record.

## fix-drift-fast-probe-113_20260718_162856

# Ledger — #113 drift job slowness (fail-fast probe)

Branch: `fix/113-drift-fast-probe` · Issue: #113 · Class: **ci** (no `src/` diff → no release)

## Goal

Make the weekly drift job (#98) fast. Its first live run took **~43 min** — dominated not by
download volume but by **retry backoff on expected 404s**: probing an unpublished period burned the
patient production policy (~24 s of backoff) on every probe, across ~110 readers × several dates.

## Work (lever 1 — the measured fix)

- [x] `_DRIFT_RETRY_POLICY = RetryPolicy(int_max_attempts=1)` — a best-effort weekly probe fails
      fast; a 404 (or a real blip) skips the dataset this week, next week catches anything transient.
- [x] `check_real_header` and `check_meta` construct every reader (and the META reader) with it.
- [x] Tests: the policy is single-attempt; both checks build their reader with it (fakes record the
      `retry_policy` they were constructed with). 36 drift tests.
- [x] **Measured on real CVM**: FIAGRO (monthly, current-month 404) dropped from ~50–96 s of backoff
      to **0.5 s** — every 404 in the probe chain now fails in one request.
- [x] Docs: `docs/ingestion/contract_drift.md` fail-fast note.

## Lever 2 (download dedup) — evaluated, DEFERRED

Reading each member re-downloads its shared archive once per member. Deduping would mean fetching
each archive once and reading raw headers — bypassing `read()` and re-coupling the drift job to
zip/member internals (the coupling the "reuse read()" design deliberately avoids). With backoff
gone, redundant small-zip downloads are seconds, not the bottleneck. Not worth the complexity for a
weekly non-blocking job; file a fresh issue only if a future run proves still slow.

## Not done, on purpose

- No gate parity — the drift workflow stays out of pre-commit/CI gates (non-blocking by design).

Completed — kept as a record.

## fix-drift-subset-contracts-117_20260718_154934

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

## provenance-drift-tools_20261101_120000

# Provenance stamp and template drift tools (#364)

- [x] Add `.blueprintx-provenance.yaml` (commit chosen by sweeping BlueprintX commits)
- [x] Copy `bin/check_template_drift.py`, `bin/template_update.py` and their unit tests
- [x] Document usage and known limits in `docs/template-updates.md` and `CONTRIBUTING.md`
- [ ] Poe tasks `template_drift` / `template_update` (come with the poe migration issue)
