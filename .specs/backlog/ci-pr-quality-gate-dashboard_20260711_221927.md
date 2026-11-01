# Work ledger — PR quality-gate dashboard + path-gated auto-merge (issue #71)

Branch: `feat/71-pr-quality-gate`. A ditto/Danger-style gate for this repo: labels + one sticky
comment + GitHub's **native** auto-merge for low-risk classes, behind an explicit opt-in label.

## Two design decisions that shape everything

1. **Auto-MERGE, not auto-APPROVE.** The `pr-quality-gate` ruleset requires **0 approvals** (a solo
   maintainer cannot approve their own PR), so a bot approval would unblock nothing — decorative.
   Native auto-merge (`enablePullRequestAutoMerge`) is what actually helps, and it **bypasses
   nothing**: GitHub holds the merge until every required check of the ruleset is green. The script
   decides only *eligibility*; the ruleset still decides *whether it passed*.
2. **Risk by PATH, never by diff size.** A small diff is not a safe diff here — the real failure
   mode is semantic (a `FileContract` column grounded wrong, a `date_ref` on the wrong partition).
   A **one-character** change under `_internal/config/contracts/` is tiny *and* catastrophic, and
   **every test still passes**, because the tests assert the contract that was written. Gating on
   size would auto-merge exactly the changes that most need human eyes. So **`src/` is never
   auto-merged, at any size** — locked by a test.

## Done

- [x] `bin/pr_gate.py` — pure classification (`classify_risk`, `size_bucket`, `is_auto_mergeable`,
      `render_comment`, `_axes_from_checks`) + a thin I/O shell (stdlib `urllib`, no new dep, no
      DangerJS/Node toolchain in a Python repo).
- [x] Labels `risk:*` / `size:*` / `gate:*` (the gate replaces only its own labels, leaving others
      untouched); ONE sticky comment (hidden marker → updated in place, never stacked).
- [x] Auto-merge classes: `docs`, `ci`, `deps`. NOT `src`, NOT `tests`, NOT `other` (unknown =
      unsafe). Requires the `automerge` label, refuses `do-not-merge`, refuses `XL`.
- [x] `.github/workflows/pr-gate.yaml` — triggers on `pull_request` (incl. `labeled`/`unlabeled`, so
      adding `automerge` takes effect at once) **and** on `workflow_run` completion of *Run Tests* /
      *Docs - Build Check*, so the sticky comment shows the FINAL per-axis result instead of freezing
      on "em execução". All event data flows through `env:` (no `${{ }}` interpolation into `run:` —
      no injection surface).
- [x] `tests/unit/test_pr_gate.py` — **35 tests**, incl. the core safety rule (`src` + `XS` +
      `automerge` → still False) and the "classification is not consent" rule.
- [x] Docs: `docs/contributing.md` section (label meanings, the risk table, why `src` is never
      auto-merged, why auto-merge and not auto-approve).
- [x] Gates: ruff (check+format), mypy, check_typing, check_provenance, check_docstrings, codespell,
      yamllint — all clean. **820 unit tests pass** (785 + 35).

## First live run — it found a real bug (that is the point)

Ran on its own PR (#72) and labelled it `["risk:tests", "size:XL", "gate:failing"]`:

- `risk:tests` — **correct**, and it corrected me: the PR adds `tests/unit/test_pr_gate.py`, and
  `tests` outranks `ci` in the most-dangerous-first ordering. I had predicted `ci`; the code was
  right.
- `size:XL` — correct (790 insertions).
- [x] `gate:failing` — **WRONG, and fixed**: the checks were still *running*. Pending was being
      reported as failing, which would cry wolf on every freshly-opened PR. Added a pure
      `gate_state()` with **three** states (`passing` / `pending` / `failing`): a red axis beats a
      pending one, a pending one beats green, and `passing` is claimed only once every axis has
      actually finished green. Locked by 5 regression tests.

## Open / next

- [ ] User review of PR (approval gate).
- [ ] Labels are auto-created by the GitHub API on first use (default grey). Recolour them by hand
      once if desired — not worth a script.

## Notes

- 0.21.0 was released before this branch started (the merge of #69), per "release after every merge".
