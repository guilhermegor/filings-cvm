# Work ledger — #108 deterministic work-ledger gate

Branch: `chore/108-backlog-ledger-gate` · Issue: #108 · Started: 2026-07-17

Make the per-branch work-ledger rule (`docs/CLAUDE.md`) structural instead of prose-only —
the analogue of `bin/check_typing.py` / `bin/check_provenance.py`.

## Done

- [x] `bin/check_backlog_ledger.py` — diff-based gate. Reuses `pr_gate.classify_risk`
      **per path** (set-membership, not most-dangerous collapse, so a `tests/` path can't hide a
      `ci`/`src` path). Fails on: src/ci diff with no ledger; bad ledger filename; ledger without a
      `- [ ]`/`- [x]` checkbox. Pure `check(paths, read_text)` core + injected git/IO edges.
- [x] `tests/unit/test_check_backlog_ledger.py` — covers `requires_ledger` (incl. the tests-hides-ci
      case), name regex, checkbox regex, and the four `check()` outcomes.
- [x] Wire `check-backlog-ledger` into `.pre-commit-config.yaml` (`always_run`, `pass_filenames:
      false`).
- [x] Wire the matching CI step into `.github/workflows/tests.yaml` + `fetch-depth: 0` on checkout
      (needs merge-base history). Gate parity honoured (both files, same change).

- [x] Gates green: ruff/ruff-format/codespell/pydocstyle/yamllint clean; 1244 unit tests pass
      (bin/ is ruff-excluded, so the module matches its space-indented peer `check_provenance.py`);
      gate proven end-to-end both ways (exit 0 with ledger staged, exit 1 without).

## Open

- [ ] Open PR (`Closes #108`), wait for review + merge. `ci` class → **no release**.

## Decisions / notes

- **`pyproject.toml` is exempt** (class `deps`, like `poetry.lock`). Reusing `pr_gate`'s path axis
  puts both under `deps`; the issue only named `poetry.lock`. If a hand-edited dependency range
  should demand a ledger, add `deps` to `LEDGER_CLASSES` — one-line change. Left exempt for now.
- The gate is a **no-op off a feature branch** (on `main`/tags the merge-base is `HEAD`, diff empty).
