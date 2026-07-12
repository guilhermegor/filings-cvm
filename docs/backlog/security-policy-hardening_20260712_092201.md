# Work ledger — SECURITY.md + GitHub security hardening (#77)

Issue **#77** · branch `chore/security-policy-hardening`. Add a security policy and turn on the
remaining free GitHub security features, **scripted** (sibling of `bin/enable_repo_rules.sh`).

Excluded from the docs site (`backlog/`). Never deleted — tick the last box on completion.

## Done

- [x] `SECURITY.md` (repo root) — supported-versions table (latest `0.x` only), private-reporting
  instructions (Security tab → Report a vulnerability), 7-day best-effort SLA, scope (in: parser
  flaws on untrusted CVM artifacts — zip-bomb, unbounded CSV, path traversal, ReDoS, dep CVEs;
  out: consumer's own deployment, CVM's servers). English (researcher/contributor surface).
  GitHub auto-detects it → flips "Security policy" to Enabled once merged to the default branch.
- [x] `bin/enable_security.sh` — mirrors `enable_repo_rules.sh`: idempotent + non-blocking, WARN +
  return 0 on missing gh/auth/admin. Three `PUT`s (204): `private-vulnerability-reporting`,
  `vulnerability-alerts` (Dependabot alerts), `automated-security-fixes` (security updates, PUT
  last since it depends on alerts). shellcheck + `bash -n` clean.
- [x] `.github/dependabot.yml` — weekly version bumps: `pip` (Poetry) + `github-actions` (keeps CI
  off deprecated Node runtimes). Labels `deps` / `ci`; commit prefixes `chore(deps)` / `chore(ci)`.
- [x] Wiring with **Makefile↔tasks.sh parity**: `enable_security` target/function, added to `init`
  chain, case dispatch, and both help texts. Verified `make help` and `tasks.sh help` agree.
- [x] **Ran it live** — all three toggles flipped and **GET-confirmed**: Dependabot alerts ENABLED,
  `automated-security-fixes {'enabled': True, 'paused': False}`, `private-vulnerability-reporting
  {'enabled': True}`.
- [x] BlueprintX **language-common** lesson captured (global store + README index + repo mirror):
  `scaffold-security-policy-and-github-security-toggles.md`.

## Testing note

Admin-gated `enable_*.sh` ship with the **shellcheck + `bash -n`** gate only — matching the
untested siblings `enable_repo_rules.sh` / `enable_pages.sh` (they need live `gh` auth + repo-admin,
so they're not unit-testable offline). Logic live-verified by running the script + GET-confirming
the three toggles.

## Remaining

- [ ] Open PR (`Closes #77`); wait for user approval + merge. `risk:ci` — not auto-merged (bin/ +
  .github/ paths), needs human review.
- [ ] After merge: release (minor bump `0.23.0`→`0.24.0`) Test PyPI → verify → PyPI → verify.
- [ ] Then **#76** (PR-gate freeze fix), per the user's sequencing, before resuming Wave 1 (FIE).
