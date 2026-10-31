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
`check_schemas.py`, `check_dtypes.py`, `check_docs_sections.py`, ruff check + format, mypy, the shell/sql/yaml/**actions** lint gates,
unit + integration tests, and the coverage `fail-under` threshold. After changing a gate,
confirm both files list it.

### ⚠️ `yamllint` does not lint the workflows in this directory — `actionlint` does

They answer different questions, and only one of them is about *this* folder:

| tool | question | verdict on the #217 defect |
|---|---|---|
| `yamllint` | is this well-formed YAML, styled consistently? | ✅ **passed** |
| `actionlint` | is this a workflow GitHub will actually run? | ❌ `unknown Webhook event` |

`pull_request_review_thread` is a real **webhook** event and **not** a workflow trigger.
Putting it in `on:` made GitHub reject the file whole — *"This run likely failed because of
a workflow file issue"* — so **no run happened at all**: the PR got no labels and no gate
comment, which reads like a slow gate rather than a dead one. Every local hook was green.

So `bin/lint_actions.sh` (hook `lint-actions` + the CI step) is the gate for anything under
`.github/workflows/`. Two things about it are deliberate:

- **It is not a Poetry dev-dep.** `actionlint-py` is **sdist-only** and downloads the Go
  binary at build time, which would put a network fetch inside every `poetry install` on all
  three matrices (`shellcheck-py`/`shfmt-py` ship real wheels — that difference is the whole
  argument). CI installs a pinned binary from the release page and **fails if it is missing**,
  rather than falling through to the wrapper's graceful skip.
- **It pins `SHELLCHECK_OPTS=--severity=warning`.** `actionlint` shells out to shellcheck for
  every `run:` block; without the pin, inline workflow snippets would be held to a *stricter*
  bar than `bin/*.sh` (`bin/CLAUDE.md`: warning-and-above). Schema errors are unaffected.

The coverage floor is single-sourced in `.coveragerc` (`[report] fail_under`), so the
pre-commit `coverage-check` hook and the CI coverage gate share one value — never pass a
duplicate `--cov-fail-under` literal in either place.

## Review automation — one workflow per job, never two

| workflow | job |
|---|---|
| `pr-gate.yaml` (`bin/pr_gate.py`) | labels, the sticky status comment, native auto-merge hand-off |
| `coderabbit_trigger.yaml` | posts `@coderabbitai review` on opened / reopened / ready_for_review |
| `review_threads.yaml` (`bin/check_review_threads.py`) | fails a PR with an unanswered or unresolved thread, or with no roster review of HEAD |
| `review_retry.yaml` (`bin/retry_rate_limited_review.py`) | every 10 min, re-asks a reviewer that answered "rate limited" |
| `reconcile-merged-prs.yaml` (`bin/reconcile_merged_prs.py`) | closes linked issues + deletes the branch of a bot-merged PR |

- **`coderabbit_trigger` exists because `auto_review` does nothing here.** CodeRabbit declines
  automatic reviews on a repository with fewer than 10 stars (refusal notice on #291), and
  `.coderabbit.yaml` cannot change that. It posts with the **`GH_PAT_REVIEW_TRIGGER`** user PAT,
  never `GITHUB_TOKEN`: CodeRabbit ignores bot-authored comments. If the secret is missing, the
  job **fails** rather than skipping, because a skip would hide the missing review. It is not a
  pre-commit-mirrored gate: it needs a live PR and a secret, so there is no local hook to pair it
  with.
- **The scaffold's `pr-reconcile.yaml` / `bin/pr_reconcile.sh` were NOT imported** (#296). They
  duplicate `reconcile-merged-prs.yaml` (same triggers), and two reconcilers would race on the
  same issues and branches.
- **The reviewer roster is data in `.review-bots.yaml`** (`coderabbitai[bot]`,
  `guilhermegor-review-ladder[bot]`). A thread counts as answered only with a comment from a
  login outside the roster. A bot resolving its own thread is not an answer. To add a reviewer,
  add a row there. ⚠️ A row alone is not the whole job: which review BODIES may declare
  findings is still pinned in code (`_SET_HEADER_AUTHORS`, `_SET_LADDER_AUTHORS` in
  `bin/check_review_threads.py`), and the gate's remedy text names `@coderabbitai full review`.
  A new reviewer that reports findings in its review body needs those updated too.
- **`Review threads answered` is NOT a required check.** Whether to make it one is the owner's
  call (ruleset). As measured on #287 and #291, it reports a review of superseded code wherever
  the last push was never re-reviewed. Resolving a thread fires no workflow event, so after
  resolving the last one, re-run the check.
- **No pre-commit hook pairs with it**: the verdict needs a PR number and the GitHub API, and
  neither exists at commit time. Its unit tests (`tests/unit/test_check_review_threads.py`) run in
  both places through the existing unit-test hook and CI step.
- **These workflows install a pinned `pyyaml` with plain `setup-python`, not Poetry.** That is
  the same choice as `pr-gate.yaml`: they need only `pyyaml` and `gh`, and `review_threads` runs
  on every review comment.
- `review_retry` is a scheduled job because nothing fires when a rate limit clears. It only
  ever posts a review request, and it exits 0 even when it cannot act.

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
