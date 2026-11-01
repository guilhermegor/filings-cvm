# Work ledger: reconcile_merged_prs open-PR base and 422 handling (#275)

- [x] Keep a merged PR's head branch when an open PR uses it as base, and log it
- [x] End the run before any delete when the open-PR read fails
- [x] Count a 422 as gone only when the body says `Reference does not exist`
- [x] Fail the sweep (exit 1) when a reconcile or delete fails
- [x] Unit tests for each guard in `tests/unit/test_reconcile_merged_prs.py`
- [x] Mutation run: removing each guard turns a test red, file restored from snapshot
- [ ] PR merged
