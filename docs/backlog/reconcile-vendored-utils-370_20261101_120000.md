# Reconcile the vendored `_internal/utils` modules with the BlueprintX template (#370)

- [x] Build a fresh lib-minimal copy of the template utils and diff it module by module
- [x] Decide taken / kept per module (table in the PR body, deviations in `_internal/utils/CLAUDE.md`)
- [x] Take `RetryPolicy` wait validation (negative / non-finite waits rejected at construction)
- [x] Take column-name whitespace stripping at the `tabular_reader` read boundary
- [x] Take the member listing in `find_member`'s error message
- [x] Keep the repo's own typing engine (no `beartype`); record it as a deliberate deviation
- [ ] Deferred (needs a `bin/quality_baseline.txt` move, which a PR must not make unasked): the `_require_zip` guard dedupe in `zip_extractor` and `_close_handlers` in `logs`
