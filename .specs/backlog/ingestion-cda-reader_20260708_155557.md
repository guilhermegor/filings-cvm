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
