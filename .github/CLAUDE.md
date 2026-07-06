# `.github/` — CI and recurrent automation

Guidance for Claude Code and contributors working in this project's `.github/`.

## What ships by default

The scaffold ships **event-driven** CI only — workflows triggered by `push` and
`pull_request`. Nothing here runs on a clock. That is deliberate: a scheduled
job runs whether or not anyone needs it, costs runner minutes, and can fail
silently long after the person who added it has moved on.

**Add a time-triggered job only when the project genuinely needs one, and write
down *why* in the workflow file.**

## Recurrent (scheduled) workflows

To run a workflow on a schedule, add an `on.schedule` trigger with a cron
expression:

```yaml
on:
  schedule:
    - cron: '0 3 * * 1'   # 03:00 UTC every Monday
  workflow_dispatch: {}    # also allow a manual run from the Actions tab
```

Gotchas that bite people:

- **Cron is UTC**, always — not your local timezone. Convert deliberately.
- **Minimum granularity is 5 minutes**; anything finer is rejected.
- **Runs can be delayed** (sometimes by many minutes) when GitHub's runner pool
  is busy — never rely on exact timing.
- **Scheduled workflows auto-disable after ~60 days of repository inactivity**
  (no pushes). They resume only when someone pushes or re-enables them.
- Always pair `schedule` with `workflow_dispatch` so you can trigger a run
  on demand without waiting for the next tick.

Common legitimate uses: nightly end-to-end tests, a scheduled CodeQL / security
scan, a stale-issue/PR bot, cache warming, scheduled data refresh.

## Dependency updates (Dependabot)

Dependabot version updates are a worked example of "recurrent automation". They
live in `.github/dependabot.yml`, and the `schedule.interval` key is
**mandatory** — there is no manual-only cadence. Pick one:

- `daily` — fast-moving app with active maintainers watching the PR queue.
- `weekly` — the typical default.
- `monthly` — low-churn project or a stable library.

```yaml
version: 2
updates:
  - package-ecosystem: "npm"          # "pip" for Python projects; also "docker", "gomod", …
    directory: "/"
    schedule:
      interval: "weekly"              # daily | weekly | monthly — choose per project
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

### Want updates with no cadence?

Enable **Dependabot security updates** instead — they are *event-driven* (a PR
opens only when a CVE advisory matches a dependency), need **no**
`dependabot.yml`, and run on no schedule at all. Turn them on in
*Settings → Code security → Dependabot*, or via the API:

```bash
gh api -X PUT repos/{owner}/{repo}/vulnerability-alerts
gh api -X PUT repos/{owner}/{repo}/automated-security-fixes
```

## Publishing packages — prefer OIDC / trusted publishing over stored tokens

When a release workflow publishes a package to a registry, default to the registry's **OIDC /
trusted-publishing** flow — **never** a stored long-lived API token committed as a secret. The
principle is registry-agnostic; only the concrete action differs:

| Ecosystem | OIDC / trusted publishing |
|-----------|---------------------------|
| Python (PyPI / Test PyPI) | `pypa/gh-action-pypi-publish@release/v1`, no `password:` |
| npm | trusted publishing (2025) + `--provenance` |
| Rust (crates.io), RubyGems | trusted publishing (OIDC) |
| Go | no token at all — publishing is a signed VCS tag |

Rules:

- Set `permissions: id-token: write` on the publish job and bind it to a **GitHub Environment**
  (per-index, self-documenting: `release_pypi`, `release_test_pypi`, `release_npm`, …).
- **Never commit a long-lived token.** Fall back to a short-lived scoped token **only** where the
  registry/CI lacks OIDC (trade-off: OIDC works only from CI — keep a token if you must publish
  from a laptop).
- The trusted publisher's claims (owner, repo, **exact workflow filename**, environment) and its
  registered project name must match the running workflow, or the upload fails with an opaque
  `invalid-publisher`. Register a *pending publisher* before the first release.

Why: no long-lived secret to store, leak, or rotate; the upload token is short-lived and bound to
this repo/workflow/environment. This is each registry's own recommended path.
