# Work ledger — meta.md reader-count drift + anti-drift gate (#155)

Branch `docs/155-meta-md-reader-count-drift`. Fixes a **published** page that claimed 30 Meta
readers while the package exposes 37, and closes the bug class with a test.

**No release** — only `docs/` and `tests/` change; nothing under `src/` (ci/docs/chore get no
release).

## The finding

`docs/ingestion/meta.md` stated **30 readers** in three places and listed a 30-row table. The real
count is **37**. Missing rows: `ADM_FII/CAD`, `CIA_ESTRANG/CAD`, `CIA_INCENT/CAD`,
`COORD_OFERTA/CAD`, `CROWDFUNDING/CAD`, `OFERTA/DISTRIB`, `CIA_ABERTA/CAD`.

⚠️ **It went stale at ADM_FII (0.25.14) and survived seven consecutive reader PRs.** The cause is
structural, not carelessness: the per-PR docs checklist repeated in every work ledger names
`docs/api.md`, `docs/ingestion/index.md`, the mkdocs `nav` and the root `CLAUDE.md` — **but not
`meta.md`**. So the one page that *enumerates* the Meta readers is the one nobody updates. And
because `api.md` said 37 correctly, no two visible numbers ever disagreed.

Found by the `/wrap-up` superseded-rules check (grep tracked docs for a fact this session changed),
after the same session corrected a sibling stale count in the root `CLAUDE.md` (`.txt` 11 / `.zip`
13 = 24 against 36 readers → measured 15/22 of 37).

## Done

- [x] `docs/ingestion/meta.md`: the 3 count claims 30 → 37 ("**N no total**", the `## Os N readers`
      heading, and the `FIE/MEDIDAS` note "o formato que os N compartilham").
- [x] The 7 missing table rows added, in implementation order, each with its real META artifact type
      (read from the code, not transcribed: 4 `.txt`, 3 `.zip` with member counts).
- [x] **Anti-drift gate** in `tests/unit/test_meta_readers.py` — two tests, both deriving truth from
      `filings_cvm.__all__`:
      - `test_docs_meta_roster_lists_every_exported_reader` — the roster table's reader set equals
        the exported set (and has no duplicate rows). Scoped to the `## Os N readers` section, since
        the page carries a second table that also names readers.
      - `test_docs_meta_reader_counts_match_the_real_total` — every "N readers" claim equals the
        real total. Asserts a match was found at all, so a reworded page fails loudly instead of
        silently ceasing to check.
- [x] **Negative control run** (the gate is not tautological): reverted `meta.md` to its stale state
      → both tests FAIL; restored → both PASS.
- [x] Root cause: `docs/CLAUDE.md` now names the two package-derived pages (`api.md`, `meta.md`),
      says `meta.md` is the one that gets forgotten and why, and states the gate exists — with the
      instruction **not** to "fix" a failure by editing the test.

## Remaining

- [ ] Gates: ruff, mypy, full unit suite, `mkdocs --strict`, codespell, pre-commit.
- [ ] Commit → PR `Closes #155` → wait for approval + merge. **No release.**
