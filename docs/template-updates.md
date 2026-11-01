# Template updates

A scaffold is a one-shot copy. A fix that lands in `templates/` afterwards reaches only
projects generated after it. `python bin/check_template_drift.py` is the reporter that closes that gap
(blueprintx#872).

## What it compares

For a project stamped with `tier` and `blueprintx_commit` in `.blueprintx-provenance.yaml`,
three versions of every template-managed file exist:

| Name | Where it comes from |
|---|---|
| base | the template file at the stamped `blueprintx_commit` |
| theirs | the template file in the BlueprintX checkout now |
| ours | the project's file |

The set of template-managed files is never listed by hand. Each tier's scaffold entry
answers `--list-copies` by dry-running its own copy steps (`bin/lib/scaffold_python_templates.sh`
for the service tiers, `bin/scaffold/python_lib_minimal.sh` for lib-minimal) and printing one
`COPY` or `RM` line per copy. The dry run stubs `cp`, `rm`, `mkdir`, `touch`, `chmod`,
`envsubst` and `print_status` through `scaffold_dry_run` in `bin/lib/scaffold_provenance.sh`,
so the output cannot disagree with what the scaffold does.

The dry run takes `--roster true|false` to match the project's review-bot roster choice, and
clears `GITGUARDIAN_API_KEY` so the output never depends on the caller's environment. Files that
are rendered rather than copied (`README.md`, `pyproject.toml`) do not appear. BlueprintX's own CI
scaffolds every tier for real and fails when `--list-copies` and the generated tree disagree.

## What it reports

- Missing: the template ships a path the project does not have.
- Template changed since scaffold: ours equals base and theirs differs.
- Both changed: ours and theirs both differ from base and from each other.

A file the project edited while the template stood still is not drift. Files a scaffold
renders through `envsubst` (`pyproject.toml`, `LICENSE`, `README.md`, `SECURITY.md`) are not
verbatim copies, so they are outside the comparison, as are files copied from `bin/ci/`.
Copies guarded by an answer given at scaffold time (the review-bot roster) are listed exactly
when the dry run is given the matching value, read back from the stamp. Other guarded copies
(a GitGuardian key, publish targets) are not policed yet, and the dry run ignores the
caller's `GITGUARDIAN_API_KEY` so the verdict never depends on the environment. A file absent
at the stamped commit that the project wrote itself is reported as both changed, unless its
content already equals the current template, in which case it is the same.

## Why it self-skips

Without a BlueprintX checkout, a stamp, or a usable `blueprintx_commit` (absent, `unknown`, or
not in the checkout's history), the content section prints `SKIPPED content drift` and says why.
It never prints a clean verdict for a comparison that did not run. The command always exits 0.

## Applying updates: `python bin/template_update.py`

`python bin/template_update.py` reads the same base, ours and theirs data and acts on it. It is a dry run
unless `--apply` is passed. The checkout comes from `--blueprintx-root` or
`BLUEPRINTX_TEMPLATE_ROOT`, as for the reporter, and the reporter's resolution of the managed
paths is reused rather than repeated (`managed_sources` in `bin/check_template_drift.py`).

| Project file | Action |
|---|---|
| missing | add it, with the template's file mode |
| equal to base | fast-forward to theirs |
| equal to theirs, or theirs equal to base | nothing to do |
| edited locally and the template moved too | `git merge-file` base, ours, theirs |

A clean merge is written as is. A conflict is written with `<<<<<<< ours`, `=======` and
`>>>>>>> template` markers and listed in the output. A file git cannot merge (binary content)
is listed as unmergeable and left untouched. A local edit is never overwritten silently, and a
file whose base is unknown (added to the template after the stamped commit) merges against an
empty base, so a differing local copy surfaces as a conflict.

`--apply` first runs `git switch -c chore/template-update-<short-sha>`, where the short sha is
the checkout's HEAD. It never writes to the branch you were on, and it stops before changing
anything when the branch cannot be created (not a git work tree, or the branch exists). It then
writes the files and leaves them uncommitted for review. `blueprintx_commit` in the stamp moves
to the checkout's HEAD only when every file applied cleanly; after a conflict the stamp is
unchanged and the command exits 1, so resolving the markers and running it again continues from
the same base.

Without a usable stamp, checkout or `blueprintx_commit` the command prints `SKIPPED update`
(or the reporter's `SKIPPED`) and exits 0 without touching the project.

### Retrying after a conflict

Run `python bin/template_update.py --apply` again while the update branch is still checked out. The
branch is reused, files already written are not rewritten, and a conflicted or merged file
counts as resolved once it holds no `<<<<<<<` or `>>>>>>>` marker line. Only then does
`blueprintx_commit` move. An unmergeable file keeps blocking until it is dealt with by hand.

`--apply` also refuses a BlueprintX checkout with uncommitted or untracked changes, because
theirs is read from the working tree while the stamped commit comes from history.

## In this repository

filings-cvm carries a stamp (`.blueprintx-provenance.yaml`, tier `lib-minimal`). The poe tasks
`template_drift` and `template_update` arrive with the poe migration; until then run the scripts
directly, pointing them at a BlueprintX checkout with `--blueprintx-root` or the
`BLUEPRINTX_TEMPLATE_ROOT` environment variable:

```bash
python bin/check_template_drift.py --root . --blueprintx-root ~/github/blueprintx
python bin/template_update.py --root . --blueprintx-root ~/github/blueprintx   # dry run
```

`blueprintx_commit` in the stamp is not the commit the repo was literally scaffolded from. It
was chosen by measurement: the BlueprintX commit at which the template files nobody here has
touched still equal the project's copies, so that "template changed" and "both changed" are
classified correctly. Only `tier` and `review_bot_roster` are scaffold-time answers the stamp
records.

### Known limits

- The tools report only files the template still ships. They do not list files the project has
  that the template removed or replaced (`Makefile`, `tasks.sh`, `bin/db.sh`, `docs/api.md`).
- Rendered files (`pyproject.toml`, `README.md`, `mkdocs.yml`, `SECURITY.md`, `LICENSE`) and
  the `bin/ci/` copies are outside the comparison.
- The vendored package tree appears under the tier's placeholder name `src/project/...`, so for
  this repository all of `src/` is reported as missing. Ignore those lines.
- Scaffold-time answers other than the review-bot roster are not recorded in the stamp.
