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
- Any new non-published folder must be added to `exclude_docs` in the same commit.

## Published pages

Everything else under `docs/` (e.g. `index.md`, `architecture.md`, `api.md`) is a
published page. Register new published pages in `mkdocs.yml` `nav:` in the same
commit they are created, or MkDocs silently omits them from navigation.
