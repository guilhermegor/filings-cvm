# Work ledger — #400 docstring URL checker off the commit path

Branch: `fix/400-docstring-urls` · Issue: #400 · Started: 2026-11-08

## Done

- [x] `check-urls` moved to `stages: [manual]` in `.pre-commit-config.yaml`.
- [x] `bin/test_urls_docstrings.sh`: failure cache (1 day), cache in the git common dir, scans
      every passed file, `URL_REPORT_FILE` report mode.
- [x] `.github/workflows/docstring-urls.yaml`: weekly job opening/updating one tracking issue.
- [x] Comments removed (budget ratchet) and the explanation moved to `docs/contributing.md`.
- [x] `tests/unit/test_urls_docstrings_script.py` pins the behaviour offline with a fake curl.

## Open

- [ ] PR review and merge (`Closes #400`); `ci` class, so no release.
