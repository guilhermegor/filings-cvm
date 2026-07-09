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
