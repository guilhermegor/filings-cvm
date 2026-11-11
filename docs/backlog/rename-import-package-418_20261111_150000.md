# Rename import package filings_cvm to opendata_cvm (#418)

- [x] Move `src/filings_cvm` to `src/opendata_cvm` and rewrite every tracked reference
- [x] Keep `old="filings-cvm"` in the release workflows (backfill of historical tags)
- [x] CHANGELOG breaking-change note, no compatibility shim
- [ ] Unit tests, ruff, mypy, `mkdocs build --strict` green
- [ ] Open the PR and answer review threads
