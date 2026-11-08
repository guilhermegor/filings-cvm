# Work ledger — #293 comment budget and comment-language guards

Branch `chore/293-comment-budget-guards`. Closes **#293** (child C of #292).

## Done

- [x] Confirmed at `origin/main` that none of `check_comment_budget.py`,
  `comment_budget_allowlist.txt`, `comment_budget_baseline.txt` or `check_comment_language.py`
  exists.
- [x] Vendored VERBATIM from `~/github/blueprintx/templates/python-common/`:
  `bin/check_comment_budget.py`, `bin/comment_budget_allowlist.txt`,
  `bin/check_comment_language.py`, and their tests `test_comment_budget_gate.py` /
  `test_comment_language_gate.py` (only whitespace changed: tab indentation, per `ruff.toml`
  for `tests/`; `bin/` stays space-indented because `ruff.toml` excludes it).
- [x] Hooks `check-comment-language` and `check-comment-budget` in `.pre-commit-config.yaml`, and
  the steps `Run Documentation-Language Boundary Enforcement` / `Run Comment Budget Ratchet` in
  `.github/workflows/tests.yaml` (gate parity).
- [x] Language gate: 31 hits on the tree, all CVM's official Portuguese names written unquoted
  in docstrings. The gate has no baseline, so each was fixed at the site: the official name is
  backticked (the gate redacts backticked spans) or, where it was prose, translated.
- [x] Comment budget: the 38 decorative banners (`# ----`/title/`# ----`) in `Makefile`,
  `tasks.sh`, `bin/lib/common.sh`, two `bin/check_*.py` and `tests/integration/test_bin_scripts.py`
  were deleted — the banner and essay checks are not covered by the ratchet.
- [x] Ratchet seeded from the tree with `--write-baseline` (`comment_budget_baseline.txt`).

## Remaining

- [ ] Lower the baseline by moving explanatory comments into docs (see the PR body for the count).
