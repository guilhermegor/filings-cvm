# `.github/` — CI and recurrent automation

Guidance for Claude Code and contributors working in this project's `.github/`.

## What ships by default

The scaffold ships **event-driven** CI only — workflows triggered by `push` and
`pull_request`. Nothing here runs on a clock. That is deliberate: a scheduled
job runs whether or not anyone needs it, costs runner minutes, and can fail
silently long after the person who added it has moved on.

**Add a time-triggered job only when the project genuinely needs one, and write
down *why* in the workflow file.**

## Gate parity — every check lives in BOTH pre-commit and CI

Every lint, static-analysis, and test gate must be wired into **both** the local
`.pre-commit-config.yaml` **and** the CI workflow (`.github/workflows/tests.yaml`).
They must stay in sync — the same discipline as the Makefile ↔ `tasks.sh` parity
rule. When you add, rename, or remove a gate in one place, make the identical
change in the other **in the same commit**.

**Why both, never one:**

- **Pre-commit only** → a contributor who commits with `--no-verify` (or whose
  hooks aren't installed) bypasses the gate, and branch-protection CI — which runs
  the workflow, not local hooks — never catches it. This is exactly how
  `check_typing.py` shipped enforced locally but invisible to CI.
- **CI only** → the failure surfaces minutes later on a pushed branch instead of
  failing fast on the developer's machine, and can't be run offline.

CI runs its gates as **explicit steps** (it does *not* invoke `pre-commit run`), so
adding a hook to `.pre-commit-config.yaml` does **not** automatically cover CI — you
must add the matching step to `tests.yaml` yourself. The canonical set to keep
mirrored: codespell, `check_docstrings.py`, `check_typing.py`, `check_provenance.py`,
ruff check + format, mypy, the shell/sql/yaml lint gates, unit + integration tests, and
the coverage `fail-under` threshold. After changing a gate, confirm both files list it.

The coverage floor is single-sourced in `.coveragerc` (`[report] fail_under`), so the
pre-commit `coverage-check` hook and the CI coverage gate share one value — never pass a
duplicate `--cov-fail-under` literal in either place.

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

## The staging rehearsal only rehearses the steps it SHARES

`release-test-pypi.yaml` is the dress rehearsal for `release-pypi.yaml`, and the two-step
(Test PyPI → verify by install → PyPI) is mandatory. But it proves **only the steps the two
workflows have in common**. **A step that exists only in `release-pypi.yaml` has its first run in
production, every single time.**

Today that delta is the **`Create GitHub Release` step** (`softprops/action-gh-release`): Test PyPI
publishes a package but cuts no GitHub Release, so nothing rehearses it.

This is not theoretical. When Dependabot bumped six actions at once (#79), the shared
`upload-artifact` ↔ `download-artifact` pair *was* genuinely validated by the Test PyPI run — while
`action-gh-release@v1→v3`, living only in the production workflow, debuted on the real 0.25.4 release
and **failed** (#102).

So, when changing anything on the release path:

- **Diff the two workflows first — the delta is the size of the hole.**
- Either mirror the step into the rehearsal, or **consciously accept that it debuts in production**
  and say so. What you may not do is claim the rehearsal covers it.
- **Verify the artifact and the tag, never the run's colour.** `pypi: success` coexisted with a
  broken release: `action-gh-release@v3` creates the release as a **draft**, uploads assets, and only
  then promotes it — so a mid-upload failure leaves `draft=true`, and **GitHub creates no tag for a
  draft**. The wheel shipped to PyPI with **no `vX.Y.Z` tag**, which silently breaks
  `poetry-dynamic-versioning` (it derives the version *from the tag*) and the release gate
  (`git diff v<LAST>..HEAD -- src/`). Recovery: `gh release edit vX.Y.Z --draft=false` (promoting
  creates the tag). Same family as #86: **a green run is not a shipped artifact.**

### Never glob a build directory into release assets

Publish the artifacts **by name** (`dist/*.whl`, `dist/*.tar.gz`) — never `dist/*`. A build directory
holds build scaffolding by construction: this repo tracks a **0-byte `dist/.keep`** (see
`.gitignore`: `dist/*` + `!dist/.keep`) so the directory exists in git, it rides along in the
artifact, and **GitHub's API rejects a 0-byte release asset** (`size must be greater than or equal to
1`). `@v1` ignored it; `@v3` fails hard. The `.keep` is deliberate — the glob was the bug.
