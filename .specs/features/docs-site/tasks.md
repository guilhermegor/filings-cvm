## claude-md-meta-counts-gate_20261029_120000

# Gate the root CLAUDE.md META counts (#161)

- [x] Confirm not already done at `origin/main` (the gate only covered `docs/ingestion/meta.md`)
- [x] Measure the real numbers from the code (48 readers = 19 .txt + 29 .zip, 48 contracts); CLAUDE.md was already right
- [x] Add `test_claude_md_meta_counts_match_the_real_numbers`, every expected value derived from the package
- [x] Prove it bites: mutated `48 readers` and `48 = 19` in CLAUDE.md, test went red; restore verified by sha256
- [x] Update the CLAUDE.md provenance note to say this paragraph is now gated
- [x] Completed — kept as a record.

## docs-meta-reader-count-drift_20260722_203000

# Work ledger — meta.md reader-count drift + anti-drift gate (#155)

Branch `docs/155-meta-md-reader-count-drift`. Fixes a **published** page that claimed 30 Meta
readers while the package exposes 37, and closes the bug class with a test.

**No release** — only `docs/` and `tests/` change; nothing under `src/` (ci/docs/chore get no
release).

## The finding

`docs/ingestion/meta.md` stated **30 readers** in three places and listed a 30-row table. The real
count is **37**. Missing rows: `ADM_FII/CAD`, `CIA_ESTRANG/CAD`, `CIA_INCENT/CAD`,
`COORD_OFERTA/CAD`, `CROWDFUNDING/CAD`, `OFERTA/DISTRIB`, `CIA_ABERTA/CAD`.

⚠️ **It went stale at ADM_FII (0.25.14) and survived seven consecutive reader PRs.** The cause is
structural, not carelessness: the per-PR docs checklist repeated in every work ledger names
`docs/api.md`, `docs/ingestion/index.md`, the mkdocs `nav` and the root `CLAUDE.md` — **but not
`meta.md`**. So the one page that *enumerates* the Meta readers is the one nobody updates. And
because `api.md` said 37 correctly, no two visible numbers ever disagreed.

Found by the `/wrap-up` superseded-rules check (grep tracked docs for a fact this session changed),
after the same session corrected a sibling stale count in the root `CLAUDE.md` (`.txt` 11 / `.zip`
13 = 24 against 36 readers → measured 15/22 of 37).

## Done

- [x] `docs/ingestion/meta.md`: the 3 count claims 30 → 37 ("**N no total**", the `## Os N readers`
      heading, and the `FIE/MEDIDAS` note "o formato que os N compartilham").
- [x] The 7 missing table rows added, in implementation order, each with its real META artifact type
      (read from the code, not transcribed: 4 `.txt`, 3 `.zip` with member counts).
- [x] **Anti-drift gate** in `tests/unit/test_meta_readers.py` — two tests, both deriving truth from
      `filings_cvm.__all__`:
      - `test_docs_meta_roster_lists_every_exported_reader` — the roster table's reader set equals
        the exported set (and has no duplicate rows). Scoped to the `## Os N readers` section, since
        the page carries a second table that also names readers.
      - `test_docs_meta_reader_counts_match_the_real_total` — every "N readers" claim equals the
        real total. Asserts a match was found at all, so a reworded page fails loudly instead of
        silently ceasing to check.
- [x] **Negative control run** (the gate is not tautological): reverted `meta.md` to its stale state
      → both tests FAIL; restored → both PASS.
- [x] Root cause: `docs/CLAUDE.md` now names the two package-derived pages (`api.md`, `meta.md`),
      says `meta.md` is the one that gets forgotten and why, and states the gate exists — with the
      instruction **not** to "fix" a failure by editing the test.

## Remaining

- [ ] Gates: ruff, mypy, full unit suite, `mkdocs --strict`, codespell, pre-commit.
- [ ] Commit → PR `Closes #155` → wait for approval + merge. **No release.**

## docs-mike-versioning_20260711_182514

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

## docs-sections-gate-70_20261030_120000

# Work ledger — #70 gate estrutural de documentação

Branch `ci/docs-sections-gate-70`. Fecha **#70**. Sem release (`ci`, zero diff em `src/`).

## Feito

- [x] `bin/check_docs_sections.py`: páginas canônicas existem e estão no `nav:`; toda página
  publicada está no `nav:`; cada família carrega as seções obrigatórias.
- [x] Allowlist nomeada `LEGACY_NONCOMPLIANT` (47 páginas de `docs/ingestion/`): página nova
  tem de cumprir; página listada que passa a cumprir falha até sair da lista.
- [x] Hook `check-docs-sections` no pre-commit e step equivalente no `tests.yaml`.
- [x] Testes negativos em `tests/unit/test_check_docs_sections.py`.

## Em aberto (follow-up)

- [ ] Reescrever as 47 páginas legadas e esvaziar a allowlist (fora do escopo da #70).

## readme-standard-250_20261029_093801

# Work ledger — #250 padrão de README da casa + gate de estrutura

Branch `docs/readme-standard-250`. Fecha **#250**. Sem release (zero diff em `src/`).

## Feito

- [x] `README.md` reescrito para o arquétipo `library`: H1 simples, logo centralizado por URL
  absoluta `raw.githubusercontent.com` (o PyPI publica o README como descrição), badges na ordem
  canônica (badge de coverage absoluto), marcadores `<!-- slug: ... -->` em todas as seções
  obrigatórias, nenhum emoji em título, rodapé `<sub>` com os agradecimentos e o aviso de que o
  emblema é do regulador. **Todo o conteúdo anterior foi mantido**, em pt-BR, sob as seções novas.
- [x] Gate vendorizado **byte a byte** do blueprintx (`templates/common/bin/`):
  `bin/check_readme_structure.sh` e `bin/lib/md_structure.sh`.
- [x] Paridade de gates: hook `readme-structure` em `.pre-commit-config.yaml` **e** passo
  `Run README Structure Gate` em `.github/workflows/tests.yaml`, no mesmo commit.
  - Desvio do escopo da issue: ela lista `pr-gate.yaml`, mas esse workflow só rotula a PR e arma
    o auto-merge (`bin/pr_gate.py`); os gates de lint vivem em `tests.yaml` (`.github/CLAUDE.md`,
    "Gate parity"). O filings-rfb (referência) também não tem passo de CI para este gate.
- [x] Gate local verde: `[ok] README structure: README.md`.

- [x] Achado: o hook `integration-tests` falhava **só dentro de `git commit` num worktree
  linkado** (`test_precommit_skips_gracefully_off_git_tree`) — o git exporta `GIT_DIR` ao hook, e
  `git rev-parse --is-inside-work-tree` em `bin/precommit.sh` passa a dizer "dentro de uma árvore"
  mesmo num tmp dir. Causa raiz no isolamento do teste, não na asserção: `_run` agora descarta
  `GIT_*` do ambiente herdado (`tests/integration/test_bin_scripts.py`). Asserção intacta.

## Aberto

- [x] Nada pendente nesta branch.

Completed — kept as a record.

## rename-bedrock-fm-178_20261029_120000

# Rename bedrock-fm to marketdata-fm in docs (#178)

The downstream project was renamed from `bedrock-fm` (working name) to `marketdata-fm`
(2026-07-31). Align the tracked docs. Historical backlog records keep their meaning; only
the project name changes.

- [x] Rename 12 lines mentioning the old name (measured from the diff) across 8 files: 6 backlog
  ledgers (9), `docs/ingestion/contract_drift.md` (1), `mkdocs.yml` (2, below)
- [x] `mkdocs.yml` exclude entry renamed to `marketdata-fm-lessons.md` (git-ignored, never published)
- [x] `grep -rni bedrock docs mkdocs.yml README.md` returns zero hits outside this ledger
  (deliberate exception: it describes the rename)
- [x] `mkdocs build --strict` passes
- [x] Completed — kept as a record.

Note: `docs/bedrock-fm-lessons.md` and `docs/blueprintx-lessons.md` named in the issue are
not tracked; the local ignored file, if present, must be renamed by hand to
`docs/marketdata-fm-lessons.md` so the `mkdocs.yml` exclude keeps matching.

## split-agent-docs_20261101_120000

# Split CLAUDE.md into AGENTS.md, PRINCIPLES.md, .claude/CLAUDE.md (#372)

- [x] Root `CLAUDE.md` becomes the template bridge; repo content moves to `AGENTS.md` with no loss
- [x] Add `PRINCIPLES.md`, `.claude/CLAUDE.md` (verbatim) and `.greptile/*` (paths adapted)
- [x] Repoint `test_agents_md_meta_counts_match_the_real_numbers` at `AGENTS.md`; mutated `52 = 22` to `53 = 22`, test went red, reverted
- [x] Repoint comments in `bin/` and `docs/CLAUDE.md`
- [x] Completed — kept as a record.
