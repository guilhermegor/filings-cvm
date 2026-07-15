# Work ledger — #104 reconcile merged PRs (close linked issue + delete branch)

Branch `fix/pr-reconciler-104`. Fixes the systemic bug where a **bot auto-merged** PR leaves its
linked issue open and its head branch alive, freezing the kanban card in "In review". `ci` — **no
release**.

## The bug (measured, not guessed)

GitHub's native housekeeping — closing a `Closes #N` issue on merge, and `delete_branch_on_merge` —
**silently skips when the merge is done by the `GITHUB_TOKEN` bot**. `bin/pr_gate.py` arms native
auto-merge with `github.token`, so every auto-merged `ci`/`deps`/`docs` PR merges *as the bot*.

Evidence: bot-merge 0/2 (#103→#102, #106→#105), hand-merge 3/3. Confirmed live this session against
the real #103 payload:

```
merged=true headRefName=fix/release-pypi-dist-glob-102 isCrossRepository=false
closingIssuesReferences=[{number:102, state:CLOSED}]  defaultBranchRef=main
```

## The decision that shaped it

Issue #104's proposed option (1) — a `pull_request: types:[closed]` workflow — is **itself subject
to the same `GITHUB_TOKEN` suppression** ("events triggered by the token create no new workflow
runs"), so it may not fire for a bot merge. Option (2) (long-lived PAT) is against repo policy.

**The escape hatch #104 didn't consider:** `schedule` (and `workflow_dispatch`) are **exempt** from
that suppression. So a scheduled reconciler is *guaranteed* to run — and closing an issue / deleting
a branch *via the API* with `GITHUB_TOKEN` works fine (only *triggering runs* is suppressed). No
secret needed. User chose "build the reconciler now" (2026-07-15).

## What shipped

- [x] `bin/reconcile_merged_prs.py` — self-contained stdlib janitor (mirrors `pr_gate.py`'s
      urllib/`_api` style; bin/ is not an importable package). Two modes:
  - **Event path** (`PR_NUMBER` set) — reconcile the PR that just merged. Fast, but may not run for
    a bot merge (that's why the sweep exists).
  - **Sweep path** (no `PR_NUMBER`) — `recently_merged_numbers` over the last `SWEEP_DAYS` (7) of
    closed PRs, reconcile each. The **guaranteed** backstop. Subsumes #104's "retroactive sweep".
  - Pure, unit-tested decision fns: `issues_to_close` (only `OPEN` → idempotent, never re-closes a
    reopened issue), `branch_to_delete` (guards: unmerged / **fork** / **default branch** → never),
    `recently_merged_numbers` (inclusive trailing window).
  - Idempotent: an already-closed issue is skipped; deleting an absent branch (404/422) is a no-op.
    In the sweep, one PR's failure is logged and skipped, never sinks the run.
- [x] `.github/workflows/reconcile-merged-prs.yaml` — triggers `pull_request:[closed]` +
      `schedule` (daily 04:17 UTC) + `workflow_dispatch`; `if:` runs only on merged PRs (or
      schedule/dispatch). Permissions: `contents:write` (delete ref), `issues:write` (close),
      `pull-requests:read` (sweep list). The **why** for the scheduled job is written in the file
      header per `.github/CLAUDE.md`. The one time-triggered job in the repo.
- [x] `tests/unit/test_reconcile_merged_prs.py` — 10 tests on the pure logic (fork/default-branch
      guards, OPEN-only closing, window boundary). All green.

## Gates

- [x] pytest (new test) — 10 passed
- [x] ruff check + `ruff format --check` — clean
- [x] mypy — clean
- [x] codespell — clean
- [x] yamllint (workflow) — clean
- [x] **Live read-only verification** against real PR #103: query shape matches `_PR_QUERY`; pure
      fns give the right decision (at merge time → close #102 + delete branch; now → idempotent
      no-op). No mutation performed.

## Not done here (deliberate)

- No pre-commit mirror / gate-parity change: this is an automation workflow, not a lint/test gate.
- No docs page / mkdocs nav: `ci` internal automation, nothing published.
- **Real proof is the next auto-merged PR**: after merge, the daily sweep (or the next bot merge)
  should close its linked issue and delete its branch with **no manual chore**. Until observed once
  in production, keep the manual chore as a fallback.

## Release

`ci` — **no release**. `git diff --name-only v0.25.4..HEAD -- src/ pyproject.toml` is empty.
