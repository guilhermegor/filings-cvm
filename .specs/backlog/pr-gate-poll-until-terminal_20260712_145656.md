# Work ledger — PR gate freeze fix (#76)

Issue **#76** · branch `fix/pr-gate-poll-until-terminal`. The quality gate froze its sticky comment
on "❌ Blocked — Security (CodeQL) failing" for PRs whose CodeQL was, seconds later, entirely green
(seen on #75 and again on #78), and never corrected itself.

Excluded from the docs site (`backlog/`). Never deleted — tick the last box on completion.

## Root cause (two compounding defects, both reproduced live)

1. **The poll loop broke on the first non-pending state.** `main()` stopped when
   `gate_state(...) != "pending"`, but `gate_state` deliberately lets a **red outrank a pending** one
   *for display*. So a single transient ❌ ended the loop **while other axes were still running** —
   the comment froze on "Blocked" and, because the gate only runs on a push, nothing ever re-rendered
   it. Evidence (PR #78, head `966e3e5`): gate printed `gate=failing` at 13:01:00; `Analyze (actions)`
   finished green at 13:01:05 and `Analyze (python)` at 13:01:16. The comment never updated.
2. **The CodeQL axis read the wrong check.** It matched the check literally named `CodeQL` — the
   code-scanning-default-setup **umbrella**, which completes in ~2 seconds (13:00:55→13:00:57) and
   flaps while awaiting a result for a new head SHA — instead of the real `Analyze (…)` analyses that
   run to completion. GitHub's own message said it plainly: *"Code scanning is still expecting 1
   result from CodeQL for …"* — i.e. **pending, not failing**.

**Never a real block:** CodeQL was green with **0 open alerts**; the `code_scanning` ruleset rule
(the actual enforcement) cleared on its own, and the PRs were `MERGEABLE / CLEAN` while the comment
still said Blocked. The comment was advisory and stale.

## Done

- [x] New pure helper `axes_are_terminal(list_axes)` — the **only** condition that may stop the poll
  loop (at least one axis, and none pending). Distinct from `gate_state`, which keeps red-beats-pending
  for *display*. The loop now keeps polling while any axis runs, so a transient red self-corrects.
- [x] `_AXIS_PREFIXES` constant; the CodeQL axis now tracks **`Analyze`**, not the 2-second `CodeQL`
  umbrella check.
- [x] **"Show why" UX** (the maintainer's ask): a failing axis now **names the failing checks**
  (`` `Analyze (python)` failure ``) instead of only counting them; an axis with no check-run yet on
  this head SHA reads **⏳ "awaiting result"** instead of ❌.
- [x] Docstrings on `main()` / `_axes_from_checks` / `axes_are_terminal` record the failure mode so it
  cannot be reintroduced.
- [x] Tests: 6 new (48 in `test_pr_gate.py`, **857 unit tests** total) — the freeze regression (red +
  pending ⇒ `gate_state == "failing"` **but** `axes_are_terminal is False`), the umbrella-vs-Analyze
  regression, "awaiting result" pending, and the failing-check naming. ruff + ruff-format + codespell
  clean.

## Third defect — found by the PR's own CI (2026-07-12)

PR #83's **Quality Gate job itself failed** (red check, 19 others green). Cause was **not** the #76
logic: a transient **GitHub `HTTP 502 Bad Gateway`** on the sticky comment's `PATCH` raised an
unhandled `HTTPError` and killed the job — reddening a PR whose CodeQL, docs and every test passed.

Two real defects it exposed, both fixed here:

- [x] **`_api()` had no retry.** A single transient 5xx/429 decided the gate's fate. Now retries on
  `RETRYABLE_STATUS` (429/500/502/503/504) with capped exponential backoff (4 attempts, 1→2→4 s); a
  real 4xx still raises at once, because retrying a malformed request only buries the bug. Pure
  predicate `is_retryable_status()` so it is unit-tested offline.
- [x] **A reporting failure failed the build.** The gate's contract is *"it reports, the ruleset
  blocks"* (`main()` returns 0 always) — but an unhandled exception bypassed that. The poll body is
  now wrapped: whatever survives the retries is logged and the job **exits 0**. A lost comment is
  cosmetic; a red PR is not.
- [x] 10 more tests (58 in file, **867 total**); ruff/format/codespell clean.

**Note:** #76's fix *increased exposure* to this (polling to completion = more API calls = more
chances to hit a hiccup), so it belongs in this PR rather than a follow-up.

## Remaining

- [ ] Open PR (`Closes #76`). Class = `ci` + touches `tests/` → `risk:tests` → **not auto-merged**
  (human review), which is correct for a guardrail change.
- [ ] **NO RELEASE** — ci/tests only, no `src/` diff (per the new release policy). PyPI stays 0.24.0.
- [ ] Then Wave 1 = **FIE** (`FIE/DOC/BALANCETE`, `BALANCO`, `FIE/CAD`) — a `feat` in `src/`, so a
  **PATCH** bump; note the next version must clear the Test-PyPI floor (0.25.0).
- [ ] Follow-up (docs-only, no release): `docs/backlog/kanban-ready-backlog-sweep_20260708_220638.md`
  still documents the dead "Release gate — minor bump every merge" rule; correct it.

## Lessons captured (dotfiles-dev store + repo mirror)

- `release-only-when-shipped-package-changes.md` — `/release` skill + PreToolUse dispatch guard.
- `no-implementation-without-a-tracked-issue.md` — branch-creation guard + protected-`main` commit guard.
- `prefer-expression-form-over-statement-form.md` — expression over statement; `if cond: break` is E701.
