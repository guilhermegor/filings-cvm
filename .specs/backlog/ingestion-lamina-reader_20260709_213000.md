# Work ledger — #8 Lâmina FIF (fact sheet) ingestion reader

Branch `feat/ingestion-lamina-reader` · issue **#8** · part of the
[kanban sweep](kanban-ready-backlog-sweep_20260708_220638.md).

## Scope

`LaminaReader` reads `lamina_fi_AAAAMM.csv` — the lâmina proper — from `lamina_fi_AAAAMM.zip`,
the **same archive** `LaminaCarteiraReader` (#7) already downloads. One row per fund class,
78 columns: objective, investment policy, fees, redemption terms, five-year performance,
worked cost examples, SAC contacts.

## Findings from the real artifact (`lamina_fi_202504.zip`)

- [x] Header read off the real file: **78 columns**, 1,324 data rows.
- [x] Grain unique on `(TP_FUNDO_CLASSE, CNPJ_FUNDO_CLASSE, ID_SUBCLASSE, DT_COMPTC)` — 0 dupes.
- [x] `DT_COMPTC` holds a single date per file (`2025-04-30`).
- [x] `ID_SUBCLASSE` is populated on **5 of 1,324** rows — unlike the carteira member, where it is
  empty on every row. Subclasses do exist here.
- [x] All four `DT_*` columns parse cleanly; blanks (77 rows for the two `*_DESPESA` columns,
  28 for `DT_INI_ATIV_5ANO`) become `NaT`.
- [x] **`QUOTE_NONE` is load-bearing, not incidental.** Free-text fields (`OBJETIVO`,
  `POLIT_INVEST`, `TAXA_ADM_OBS`) contain stray *unbalanced* `"` characters. Measured on the real
  file:
  - default `QUOTE_MINIMAL` → 1,318 records, histogram `{78: 1316, 142: 1, 79: 1}` → pandas raises
    `ParserError: Expected 78 fields in line 613, saw 142`.
  - `QUOTE_NONE` → all 1,325 lines at exactly 78 fields.

  CVM emits no quoting at all and the delimiter never appears inside a field, so honouring quotes
  is simply wrong for these dumps. This validates the existing repo convention rather than adding
  one.

## Decisions

- [x] **Contract declares all 78 columns as required**, not just the keys. This is a single-layout
  member, so a column CVM drops or renames must fail loudly at read time instead of surfacing as a
  `KeyError` deep in a consumer's transform. Extra columns are still tolerated.
- [x] **Dtype map derived from the contract** (`{c: "str" for c in LAMINA_FIF.tuple_required if c
  not in _DATE_COLS}`) rather than retyped. The 78 names live in exactly one place, and a column
  added to the contract cannot be silently left untyped. A test pins that the two sets partition
  the contract.
- [x] Money, percentage, and day-count columns stay `str` (exact CVM decimal text), per the sweep's
  standing decision.
- [x] **Took the dedup deferred in #7.** `zip_extractor.find_member(list_members, str_name)` now
  serves both Lâmina readers, and `LaminaCarteiraReader` was refactored onto it.
  - Selection is by **exact file name, never a prefix**: `lamina_fi_AAAAMM.csv` is a strict prefix
    of `lamina_fi_carteira_AAAAMM.csv` *and* both `lamina_fi_rentab_*_AAAAMM.csv`. A `startswith`
    match would return whichever member the archive happened to list first. The caller knows the
    reference month, so it can name the member exactly.
  - This *tightened* #7 too: its prefix match was correct only by accident of the longer literal.

## Shipped

- [x] `_internal/config/contracts/lamina_fif.py` — `LAMINA_FIF` (78 required columns)
- [x] `contracts/__init__.py` re-export
- [x] `_internal/utils/zip_extractor.py` — new `find_member`
- [x] `ingestion/lamina.py` — `LaminaReader`
- [x] `ingestion/lamina_carteira.py` — refactored onto `find_member`
- [x] Exported from `ingestion/__init__.py` and the package `__all__`
- [x] `tests/unit/test_lamina_ingestion.py` — 13 tests (incl. the stray-quote regression)
- [x] Docs: `docs/ingestion/lamina.md`, `ingestion/index.md`, `api.md`, `mkdocs.yml` nav
- [x] Root `CLAUDE.md` catalog: Lâmina entry marks the fact-sheet reader ✅

## Verification

- [x] 77 unit tests green under **pandas 3.0.3 and pandas 2.3.3** — the dual-major check that #7's
  CI failure taught. Ruff check + format, `bin/check_typing.py` clean.
- [x] **End-to-end against the live CVM file:** 1,324 × 78, matching an independent raw count;
  `DT_COMPTC` → `date`; 77 null `DT_INI_DESPESA`; 5 populated `ID_SUBCLASSE`; no fabricated
  `"nan"`; `path_raw` kept the `.zip` and all four CSVs.

## Open

- [ ] PR opened; awaiting user review/merge.
- [ ] `lamina_fi_rentab_ano_*` and `lamina_fi_rentab_mes_*` are the two remaining members of this
  archive. Worth their own issue; `find_member` is ready for them.
