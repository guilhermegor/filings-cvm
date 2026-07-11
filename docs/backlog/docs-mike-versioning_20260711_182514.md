# Work ledger — version the MkDocs site with mike (issue #64)

Branch: `docs/64-mike-versioning`. Adds a version dropdown to the published docs so each release
has its own navigable version, `latest` alias tracking the newest.

## Key design decisions (user-confirmed)

- **Trigger model: release-only + PR build-check.** Versioned docs deploy ONLY from the release
  workflow after the PyPI publish; `docs.yaml` becomes a strict build-check (no deploy).
- **Granularity: minor (`X.Y`)** — the project bumps minor per release; a patch inherits its slot.
- **Pages source switch via a bin helper in `make init`** (not the Settings UI).
- **OIDC:** N/A here. release-pypi is *already* OIDC trusted-publishing (no token); the mike push
  uses the built-in `GITHUB_TOKEN` (`contents: write`), a same-repo branch write — no external
  credential, nothing OIDC would improve.
- **No 404 window:** `enable_pages` only flips the source to `gh-pages` once that branch exists.

## Done

- [x] `mike` added to the `docs` dependency group (`poetry add --group docs`; lock updated). The
      release build job excludes `--without docs`, so mike doesn't bloat the wheel build.
- [x] `mkdocs.yml`: `extra.version.provider: mike` (renders the dropdown).
- [x] `bin/enable_pages.sh` **repurposed** from "Actions source" → point Pages at the `gh-pages`
      branch. Idempotent + non-blocking; **guarded** to skip the switch until `gh-pages` exists
      (no 404); create-or-update via `gh api` with a JSON body. shellcheck + `bash -n` clean.
- [x] `.github/workflows/docs.yaml` → **build-check only** (`mkdocs build --strict` on push+PR, no
      deploy, no pages/id-token permissions).
- [x] Deploy extracted into a **dedicated reusable workflow** `.github/workflows/deploy-docs.yaml`
      (`on: workflow_call` with a `version` input, + `on: workflow_dispatch` for a manual
      seed/re-deploy from the Actions tab). Holds the mike steps: build docs, awk-sanitized minor,
      `mike deploy --push X.Y latest` + `mike set-default --push latest`, `contents: write`,
      `fetch-depth: 0`. `release-pypi.yaml` now just **calls** it (`uses:
      ./.github/workflows/deploy-docs.yaml`, `needs: [details, pypi]`, `if: suffix == ''` so
      `latest` only moves for stable, `with.version = new_version`). A reusable workflow — not a
      composite action — because the deploy is a full job needing its own runner + checkout /
      Python / Poetry, which a composite (running inside the caller's job) can't encapsulate.
- [x] `Makefile` + `tasks.sh` comments & help text updated (parity), `docs/contributing.md`
      rewritten: mike model, the one-time `enable_pages`, and an optional seed of the current
      version.
- [x] Verified: shellcheck clean, `mkdocs build --strict` green with the mike provider,
      `poetry check --lock` consistent, both workflows parse, ruff clean, 760 unit tests pass.

## Open / next (all require the maintainer, post-merge)

- [ ] User review of PR (approval gate).
- [ ] After merge, **seed gh-pages once** (optional, to publish 0.18 immediately) OR let the next
      release create it, then run `make enable_pages` to flip the Pages source.
- [ ] Confirm the dropdown renders on the live site and the bare URL lands on `latest`.

## Notes

- Chicken-and-egg the helper handles: Pages can't point at `gh-pages` before it exists → helper
  no-ops until the first `mike deploy`. The live site stays on the current source until then.
- BlueprintX lesson already captured (`scaffold-mike-doc-versioning-in-python-common`) so future
  scaffolds inherit this by default.
