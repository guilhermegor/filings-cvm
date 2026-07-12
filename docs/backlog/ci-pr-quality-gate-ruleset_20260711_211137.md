# Work ledger — provision the `pr-quality-gate` ruleset programmatically (issue #68)

Branch: `chore/68-pr-quality-gate-ruleset`. Replaces ~10 manual checkboxes in Settings → Rules with
an idempotent `bin/enable_repo_rules.sh` wired into `make init`.

## The finding that unlocked this

The Copilot auto-review **is** REST-settable — it is its **own rule type**
(`copilot_code_review`, parameters `review_on_push` / `review_draft_pull_requests`), **not** a
parameter of `pull_request`. The earlier `pull_request.parameters.automatic_copilot_code_review_enabled`
spelling returns **HTTP 422 "Unexpected parameter"**, which is what made it look UI-only. Probed with
an `enforcement: disabled` ruleset (created → schema echoed back → deleted), so **nothing in the
ruleset needs a manual click**.

Also captured, from a real PR's check-runs (never guessed): the required status-check contexts are
`Run Automated Tests (ubuntu-latest | macos-latest | windows-latest)` + `build`.

## Done

- [x] `bin/enable_repo_rules.sh` — declares + applies the `pr-quality-gate` ruleset. Idempotent
      (existing ruleset → `PUT` in place; absent → `POST`), non-blocking (no gh / no auth / no admin
      → warn + return 0, `init` still completes). Targets `~DEFAULT_BRANCH` so it survives a rename
      and ports to a scaffolded project with a different branch name.
- [x] Rules applied: `pull_request` (**0 approvals** — GitHub forbids self-approval, so ≥1 would
      lock a solo maintainer out; + `required_review_thread_resolution` so Copilot's comments are
      binding), `required_status_checks` (the 3 OS test jobs + docs `build`), `code_scanning`
      (CodeQL `high_or_higher` / `errors`), `copilot_code_review` (`review_on_push`),
      `non_fast_forward`, `deletion`.
- [x] Deliberately NOT enabled: *Require code quality results* (subjective AI severity on the merge
      path; ruff/mypy/`check_*.py` already own quality) and *Restrict code coverage* (the floor is
      single-sourced in `.coveragerc`; a second threshold would drift).
- [x] `Makefile` + `tasks.sh` parity (target/function + `init` + `case` + `help`), verified by
      diffing `make help` against `bash tasks.sh help`.
- [x] Docs: `docs/contributing.md` section (rule-by-rule table + the automatic-vs-manual boundary +
      the CodeQL default-setup prerequisite) and a README paragraph.
- [x] **Applied live and verified**: ruleset created `active`, all 6 rules echoed back exactly as
      declared; a second run **updated in place** (ruleset count stayed 1 → idempotent).
- [x] Gates: `shellcheck --severity=warning --exclude=SC1091` + `bash -n` clean on the new script
      and `tasks.sh`.

## Open / next

- [ ] User review of PR (approval gate). ⚠️ This PR is the **first** one the new ruleset applies to —
      expect Copilot to auto-review it, and the required checks to gate the merge. That is the live
      end-to-end proof.
- [ ] BlueprintX lesson (`language-common`): the verified ruleset JSON + the automatic/manual
      boundary, so future scaffolds ship the gate instead of rediscovering the 422.

## Notes

- CodeQL default setup was enabled separately (API, on this repo) and is a **prerequisite** for the
  `code_scanning` rule to have a tool to gate on:
  `gh api -X PATCH repos/:o/:r/code-scanning/default-setup -f state=configured`.
- Matrix caveat worth knowing: several matrix jobs collapse to the **same check-run name**
  (`Run Automated Tests (ubuntu-latest)` appears once per Python version). Requiring that context
  works, but if per-version granularity is ever needed, put the version in the job `name:`.
