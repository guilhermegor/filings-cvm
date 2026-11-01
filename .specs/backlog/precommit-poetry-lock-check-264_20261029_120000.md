# Work ledger — #264 pre-commit poetry-lock check

Branch `ci/precommit-lock-check-264`. Closes **#264**. No release (zero diff in `src/`).

## Done

- [x] Confirmed at `origin/main`: no `poetry check --lock` hook exists in
  `.pre-commit-config.yaml`; the check is CI-only.
- [x] Added local hook `poetry-lock-check` (`bash bin/poetry_exec.sh check --lock`,
  `files: ^(pyproject\.toml|poetry\.lock)$`, `pass_filenames: false`), the same
  command as the CI step, routed through the repo's poetry wrapper.
- [x] Proved in a scratch copy: clean passes; a dependency added to `pyproject.toml`
  without re-locking fails ("pyproject.toml changed significantly since
  poetry.lock was last generated"); reverting passes again.
- [x] `.github/CLAUDE.md` gate list checked: it does not enumerate this check, so
  no edit. `tests.yaml` untouched (held by #258).
- [x] Ledger ticked — Completed — kept as a record.
