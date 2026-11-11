# CLAUDE.md — docs/

Guidance for working inside this project's `docs/` directory.

## Published vs non-published

MkDocs **builds every `.md` under `docs/` into the site**, even files absent from
`nav:` (they are merely unlisted, still reachable by URL). So a backlog, spec, or
internal note dropped at the `docs/` root *will* ship to readers and can mislead
them.

Keep such working documents under a folder that is excluded from the build via
`exclude_docs` in `mkdocs.yml`:

```yaml
exclude_docs: |
  backlog/        # work-to-do backlogs, follow-up notes — never published
```

- `docs/backlog/` — work-to-do backlogs and follow-up notes. **Not** added to
  `nav:`, **not** part of the published site. For any non-trivial branch, keep a
  **per-branch work ledger** here at `docs/backlog/<kebab-topic>_YYYYMMDD_HHMMSS.md`
  (timestamped filename, set at creation, never renamed) recording **what was done**
  and **what remains / is open**, updated as the work proceeds. Track each item as a
  Markdown checkbox (`- [ ]` open, `- [x]` done), not a bare `-` bullet. Tracked in git
  but excluded from the site, so knowledge survives across sessions. Distinct from
  generalizable lessons: the ledger is *this branch's* state. **Keep it on completion —
  never delete:** when every box is `[x]`, tick the last one, add a short "Completed —
  kept as a record" note, and leave the file as the permanent record of what was done.
- ⚠️ **Bot-authored branches are exempt** (`bin/check_backlog_ledger.py`, `is_bot_actor`): when the
  **PR's author** ends in `[bot]` the gate is a no-op. The author arrives as `LEDGER_PR_AUTHOR`
  (`github.event.pull_request.user.login`), **not** `GITHUB_ACTOR` — that one names whoever
  *triggered the run*, so a human re-running or updating a bot's PR would cancel the exemption
  exactly when it is needed (measured on #167; fixed in #176). A ledger records a *human's* reasoning —
  what was done, what is open, why a shortcut was taken — and an automated dependency bump has
  none to record: the diff is the whole message. Without the exemption every Dependabot PR
  touching `.github/workflows/**` (risk class `ci`) is **permanently red and unmergeable**, which
  only teaches people to reach for `--admin` — a worse habit than the gate prevents. This was
  measured, not theorised: PR #167 sat blocked for days (#174).
  **The exemption keys on the author, never on the path** — a *human* branch touching a workflow
  still owes a ledger, and a unit test asserts both directions so the exemption cannot quietly
  become a hole for everyone.
- Any new non-published folder must be added to `exclude_docs` in the same commit.

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
from `opendata_cvm.__all__`, so a missing row or a stale number **fails the suite**.
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
