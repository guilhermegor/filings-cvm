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
