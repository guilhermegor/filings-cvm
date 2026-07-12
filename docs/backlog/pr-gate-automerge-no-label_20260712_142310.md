# Work ledger — no-label auto-merge for safe classes (#81)

Issue **#81** · branch `feat/pr-gate-automerge-no-label`. Flip the PR gate's consent model from
opt-in (`automerge` label required) to **opt-out**, so every `ci`/`deps`/`docs` PR that passes the
gate auto-merges + deletes its branch with no label — Dependabot's weekly PRs included.

Excluded from the docs site (`backlog/`). Never deleted — tick the last box on completion.

## Root cause found (auto-merge was inert)

`allow_auto_merge` was **`False`** repo-wide, so the gate's `enablePullRequestAutoMerge` mutation had
been failing silently since #72 — no PR could ever self-merge, label or not. Every "auto-merge" PR to
date was hand-merged. Fixed **live** on 2026-07-12: `allow_auto_merge: true` +
`delete_branch_on_merge: true` (GET-confirmed); `automerge` + `do-not-merge` labels created (never
existed). **#78 auto-merged end-to-end** as the dogfood (merged + branch auto-deleted).

## Done

- [x] `bin/pr_gate.py` — `is_auto_mergeable()` drops the opt-in: safe class + not XL + not
  `do-not-merge` → auto-merge (returns `BLOCK_LABEL not in list_labels`). Removed `OPT_IN_LABEL`.
  `render_comment()` rewritten for 4 states: enabled / human-review(src·tests·other) /
  human-review(XL) / held(do-not-merge). Module docstring + `pr-gate.yaml` header updated.
- [x] `bin/enable_repo_rules.sh` — new `enable_merge_policy()`: PATCHes `allow_auto_merge` +
  `delete_branch_on_merge`, ensures the `do-not-merge` label (idempotent, non-blocking). Wired into
  `enable_repo_rules()`. **Ran it live** — ruleset updated, merge policy set, label present.
- [x] `Makefile` + `tasks.sh` — descriptions updated (parity verified: `make help` == `tasks.sh
  help`).
- [x] `tests/unit/test_pr_gate.py` — rewrote the auto-merge tests for opt-out (safe class merges with
  `[]`; `do-not-merge` opts out; src/tests never; XL never; 3 new render-message tests). **851 unit
  tests pass**; ruff + ruff-format + shellcheck + bash -n + codespell clean.
- [x] BlueprintX lesson `scaffold-pr-gate-automerge-by-path-not-size.md` updated (opt-in→opt-out +
  the `allow_auto_merge`-inert finding) in the global store, README unchanged (same file), and repo
  mirror `docs/blueprintx-lessons.md`.

## Residual risk (accepted, documented)

A `deps` bump green in CI still merges even though CI tests only the *locked* version, not every
in-range version a consumer might resolve (floor-vs-lock gap). Mitigations: `do-not-merge`,
held-majors in `dependabot.yml`, and a future min-version (floor) CI matrix (separate follow-up).

## Remaining

- [ ] Open PR (`Closes #81`). **Guardrail change → present for explicit review; do NOT auto-merge
  this one** (even though it's `ci`-class and would now qualify).
- [ ] After merge: release (minor bump `0.24.0`→`0.25.0`) Test PyPI → verify → PyPI → verify.
- [ ] Then **#76** (gate freeze fix), then Wave 1 = FIE.
- [ ] Post-merge cleanup: the `automerge` repo label is now vestigial (code no longer reads it) —
  optionally delete it to avoid confusion.
