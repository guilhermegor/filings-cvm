# CLAUDE.md — docs/

Guidance for working inside this project's `docs/` directory.

## Published vs non-published

`docs/` is solely for **published documentation**. MkDocs builds every `.md` under it into
the site, so a backlog, spec, plan or internal note dropped here *will* ship to readers and
can mislead them. Working material lives in `.specs/` (see `.specs/CLAUDE.md`):

- `.specs/features/<feature>/{design,plan,tasks}.md` — per-feature specs, plans and trackers.
- `.specs/backlog/<kebab-topic>_YYYYMMDD_HHMMSS.md` — flat trackers for work spanning no single
  feature; the per-branch work ledger required by `bin/check_backlog_ledger.py` for any `src`/`ci`
  change. Never deleted: on completion add a "Completed — kept as a record" note.
- Bot-authored PRs are exempt from the ledger gate, keyed on the PR author read from the event
  payload (never `GITHUB_ACTOR`).

`bin/check_docs_boundary.sh` (hook `docs-boundary` + CI step) fails on `backlog/`, lessons,
`design.md`/`plan.md`, security pages and `.superpowers*` under `docs/`. Files that are git-ignored
or merely unlisted (`exclude_docs` in `mkdocs.yml`) stay out of the site.

## Published pages

Everything else under `docs/` (e.g. `index.md`, `examples.md`, `api/index.md`) is a
published page. Register new published pages in `mkdocs.yml` `nav:` in the same
commit they are created, or MkDocs silently omits them from navigation.

### Pages that enumerate code — update them with the code, not later

Two published pages carry a **roster derived from the package**, and both must be
updated in the same commit as the reader that changes them:

- `docs/api/reference.md` — the per-reader API reference.
- `docs/ingestion/meta.md` — the `Meta*Reader` table **and** its three "N readers"
  claims.

`meta.md` is the one that gets forgotten: adding a reader means touching `api/reference.md`,
`index.md`, the `nav`, and the root `AGENTS.md`, and `meta.md` is not on that
reflex list. It sat at "30 readers" through **seven** consecutive reader PRs while
`api/reference.md` correctly said 37 — nothing looked inconsistent, because no gate compared
either page to the package.

It is now gated: `tests/unit/test_meta_readers.py` derives the roster and the counts
from `filings_cvm.__all__`, so a missing row or a stale number **fails the suite**.
Do not fix such a failure by editing the test — the code is the truth, the page
follows it. (#155)

## The API reference is a directory (#371)

`docs/api/` holds `index.md` (overview) and `reference.md` (the per-symbol roster) — **never a
single `docs/api.md`**. Splitting it later rots every published deep link (`/<version>/api/#anchor`
lives forever once `mike` versions the site). New API entries go in `docs/api/reference.md` (or a
sibling page under `docs/api/`, registered in `nav:` in the same commit). Link to it as
`api/reference.md` / `../api/reference.md`, never `api.md`; `test_docs_skeleton_sync.py` fails if
`docs/api.md` reappears.

Other layout pieces from the BlueprintX template: `docs/examples.md` (task recipes),
`docs/stylesheets/brand.css` (wired through `extra_css`), `docs/assets/logo.png` (`theme.logo` and
`favicon`), and `docs/.docs-skeleton.yaml` (the required-page list; it must equal
`CANONICAL_SLUGS` in `bin/check_docs_sections.py`). The backlog lives in `docs/backlog/`.

## Structure gate and language (#70)

`bin/check_docs_sections.py` (pre-commit `check-docs-sections` + CI step) checks the
skeleton, never the prose: the seven canonical pages (`index, usage, examples,
api/index, faq, contributing, changelog`) exist and are in the `nav:`; every published page is in the
`nav:`; each family (`docs/ingestion/*.md`) carries `Descrição`, `Tipagem`, `Política
de retry`, `Exemplos`. It keys on file **slugs** and configured section labels, never
on nav **titles** (`Início`, `Uso`... are localized presentation).

Pages that predate the section rule sit on `LEGACY_NONCOMPLIANT` in the script. A new
page must comply; a listed page that becomes compliant FAILS until you remove it, so
the list only shrinks. Prose language is single-sourced in `mkdocs.yml`
`theme.language` (`pt-BR`).
