## ci-pr-quality-gate-dashboard_20260711_221927

# Work ledger — PR quality-gate dashboard + path-gated auto-merge (issue #71)

Branch: `feat/71-pr-quality-gate`. A ditto/Danger-style gate for this repo: labels + one sticky
comment + GitHub's **native** auto-merge for low-risk classes, behind an explicit opt-in label.

## Two design decisions that shape everything

1. **Auto-MERGE, not auto-APPROVE.** The `pr-quality-gate` ruleset requires **0 approvals** (a solo
   maintainer cannot approve their own PR), so a bot approval would unblock nothing — decorative.
   Native auto-merge (`enablePullRequestAutoMerge`) is what actually helps, and it **bypasses
   nothing**: GitHub holds the merge until every required check of the ruleset is green. The script
   decides only *eligibility*; the ruleset still decides *whether it passed*.
2. **Risk by PATH, never by diff size.** A small diff is not a safe diff here — the real failure
   mode is semantic (a `FileContract` column grounded wrong, a `date_ref` on the wrong partition).
   A **one-character** change under `_internal/config/contracts/` is tiny *and* catastrophic, and
   **every test still passes**, because the tests assert the contract that was written. Gating on
   size would auto-merge exactly the changes that most need human eyes. So **`src/` is never
   auto-merged, at any size** — locked by a test.

## Done

- [x] `bin/pr_gate.py` — pure classification (`classify_risk`, `size_bucket`, `is_auto_mergeable`,
      `render_comment`, `_axes_from_checks`) + a thin I/O shell (stdlib `urllib`, no new dep, no
      DangerJS/Node toolchain in a Python repo).
- [x] Labels `risk:*` / `size:*` / `gate:*` (the gate replaces only its own labels, leaving others
      untouched); ONE sticky comment (hidden marker → updated in place, never stacked).
- [x] Auto-merge classes: `docs`, `ci`, `deps`. NOT `src`, NOT `tests`, NOT `other` (unknown =
      unsafe). Requires the `automerge` label, refuses `do-not-merge`, refuses `XL`.
- [x] `.github/workflows/pr-gate.yaml` — triggers on `pull_request` (incl. `labeled`/`unlabeled`, so
      adding `automerge` takes effect at once) **and** on `workflow_run` completion of *Run Tests* /
      *Docs - Build Check*, so the sticky comment shows the FINAL per-axis result instead of freezing
      on "em execução". All event data flows through `env:` (no `${{ }}` interpolation into `run:` —
      no injection surface).
- [x] `tests/unit/test_pr_gate.py` — **35 tests**, incl. the core safety rule (`src` + `XS` +
      `automerge` → still False) and the "classification is not consent" rule.
- [x] Docs: `docs/contributing.md` section (label meanings, the risk table, why `src` is never
      auto-merged, why auto-merge and not auto-approve).
- [x] Gates: ruff (check+format), mypy, check_typing, check_provenance, check_docstrings, codespell,
      yamllint — all clean. **820 unit tests pass** (785 + 35).

## First live run — it found a real bug (that is the point)

Ran on its own PR (#72) and labelled it `["risk:tests", "size:XL", "gate:failing"]`:

- `risk:tests` — **correct**, and it corrected me: the PR adds `tests/unit/test_pr_gate.py`, and
  `tests` outranks `ci` in the most-dangerous-first ordering. I had predicted `ci`; the code was
  right.
- `size:XL` — correct (790 insertions).
- [x] `gate:failing` — **WRONG, and fixed**: the checks were still *running*. Pending was being
      reported as failing, which would cry wolf on every freshly-opened PR. Added a pure
      `gate_state()` with **three** states (`passing` / `pending` / `failing`): a red axis beats a
      pending one, a pending one beats green, and `passing` is claimed only once every axis has
      actually finished green. Locked by 5 regression tests.

## Open / next

- [ ] User review of PR (approval gate).
- [ ] Labels are auto-created by the GitHub API on first use (default grey). Recolour them by hand
      once if desired — not worth a script.

## Notes

- 0.21.0 was released before this branch started (the merge of #69), per "release after every merge".

## ci-pr-quality-gate-ruleset_20260711_211137

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

## The automatic/manual boundary — repo config vs account PLAN

Verified live on PR #69: CI + CodeQL gate the merge (`mergeStateStatus: CLEAN` only because all
checks passed), force-push/deletion blocked — **but no Copilot review appeared**. The cause is *not*
the ruleset (`copilot_code_review` is active in the JSON) and *not* a missing activation: the account
**already has Copilot Free**. The rule only fires "if the author has access to Copilot code review",
and **code review is not included in Copilot Free** — GitHub's plan page lists "*AI reviews*" as an
**upgrade** feature, and the Free feature list has no code-review entry. So the rule is correctly
configured and **inert: no review, no error** — the silence is the trap.

- **Repository config** (all 6 rules + CodeQL default setup) → **scripted**, zero clicks. ✅
- **Account plan** (Copilot *code review*) → needs Pro / Pro+ / Business. Copilot **Pro is free** for
  verified students / teachers / popular-OSS maintainers; otherwise a free-tier LLM (e.g. Gemini
  Flash) in a `pull_request` workflow is the genuinely-free reviewer.
- ⚠️ Do **not** diagnose this from `gh api user/copilot_billing` → 404 (I did, and it was wrong):
  that endpoint is org/enterprise seat management and 404s for a personal account **even with Copilot
  Free active**. Read the plan page.
- **Every other rule works regardless of any Copilot plan** — the gate is worth having as-is.

Folded into `bin/enable_repo_rules.sh` (header), `docs/contributing.md`, and the BlueprintX lessons.

## Notes

- CodeQL default setup was enabled separately (API, on this repo) and is a **prerequisite** for the
  `code_scanning` rule to have a tool to gate on:
  `gh api -X PATCH repos/:o/:r/code-scanning/default-setup -f state=configured`.
- Matrix caveat worth knowing: several matrix jobs collapse to the **same check-run name**
  (`Run Automated Tests (ubuntu-latest)` appears once per Python version). Requiring that context
  works, but if per-version granularity is ever needed, put the version in the job `name:`.

## enable-repo-rules-copilot-comment-215_20261029_120000

# Work ledger — #215 comentário falso sobre o Copilot em enable_repo_rules.sh

Branch `fix/enable-repo-rules-copilot-comment-215`. Fecha **#215**. Sem release (`ci`, zero diff em `src/`).

## O que estava em jogo

`bin/enable_repo_rules.sh` dizia que `required_review_thread_resolution` torna vinculantes os
comentários do Copilot. Falso: a regra vale para todo thread inline (hoje, os do CodeRabbit) e o
`copilot_code_review` é inerte nesta conta (restrição do plano). O PR #214 corrigiu só a documentação.

## Feito

- [x] Comentário reescrito descrevendo a regra pelo que ela faz, sem atribuí-la a uma ferramenta,
  e apontando que o `copilot_code_review` é inerte.
- [x] O script não foi executado (ele altera as regras do repositório no GitHub).
- [x] Hooks de pre-commit verdes.

Completed — kept as a record.

## pr-gate-automerge-no-label_20260712_142310

# Work ledger — no-label auto-merge for safe classes (#81)

Issue **#81** · branch `feat/pr-gate-automerge-no-label`. Flip the PR gate's consent model from
opt-in (`automerge` label required) to **opt-out**, so every `ci`/`deps`/`docs` PR that passes the
gate auto-merges + deletes its branch with no label — Dependabot's weekly PRs included.

Excluded from the docs site (`backlog/`). Never deleted — tick the last box on completion.

## Root cause found (auto-merge was inert)

`allow_auto_merge` was **`False`** repo-wide, so the gate's `enablePullRequestAutoMerge` mutation had
been failing silently since #72 — no PR could ever self-merge, label or not. Every "auto-merge" PR to
date was hand-merged. Fixed **live** on 2026-07-12: `allow_auto_merge: true` +
`delete_branch_on_merge: true` (GET-confirmed); `automerge` + `do-not-merge` labels created (never
existed). **#78 auto-merged end-to-end** as the dogfood (merged + branch auto-deleted).

## Done

- [x] `bin/pr_gate.py` — `is_auto_mergeable()` drops the opt-in: safe class + not XL + not
  `do-not-merge` → auto-merge (returns `BLOCK_LABEL not in list_labels`). Removed `OPT_IN_LABEL`.
  `render_comment()` rewritten for 4 states: enabled / human-review(src·tests·other) /
  human-review(XL) / held(do-not-merge). Module docstring + `pr-gate.yaml` header updated.
- [x] `bin/enable_repo_rules.sh` — new `enable_merge_policy()`: PATCHes `allow_auto_merge` +
  `delete_branch_on_merge`, ensures the `do-not-merge` label (idempotent, non-blocking). Wired into
  `enable_repo_rules()`. **Ran it live** — ruleset updated, merge policy set, label present.
- [x] `Makefile` + `tasks.sh` — descriptions updated (parity verified: `make help` == `tasks.sh
  help`).
- [x] `tests/unit/test_pr_gate.py` — rewrote the auto-merge tests for opt-out (safe class merges with
  `[]`; `do-not-merge` opts out; src/tests never; XL never; 3 new render-message tests). **851 unit
  tests pass**; ruff + ruff-format + shellcheck + bash -n + codespell clean.
- [x] BlueprintX lesson `scaffold-pr-gate-automerge-by-path-not-size.md` updated (opt-in→opt-out +
  the `allow_auto_merge`-inert finding) in the global store, README unchanged (same file), and repo
  mirror `docs/blueprintx-lessons.md`.

## Residual risk (accepted, documented)

A `deps` bump green in CI still merges even though CI tests only the *locked* version, not every
in-range version a consumer might resolve (floor-vs-lock gap). Mitigations: `do-not-merge`,
held-majors in `dependabot.yml`, and a future min-version (floor) CI matrix (separate follow-up).

## Remaining

- [ ] Open PR (`Closes #81`). **Guardrail change → present for explicit review; do NOT auto-merge
  this one** (even though it's `ci`-class and would now qualify).
- [ ] After merge: release (minor bump `0.24.0`→`0.25.0`) Test PyPI → verify → PyPI → verify.
- [ ] Then **#76** (gate freeze fix), then Wave 1 = FIE.
- [ ] Post-merge cleanup: the `automerge` repo label is now vestigial (code no longer reads it) —
  optionally delete it to avoid confusion.

## pr-gate-poll-until-terminal_20260712_145656

# Work ledger — PR gate freeze fix (#76)

Issue **#76** · branch `fix/pr-gate-poll-until-terminal`. The quality gate froze its sticky comment
on "❌ Blocked — Security (CodeQL) failing" for PRs whose CodeQL was, seconds later, entirely green
(seen on #75 and again on #78), and never corrected itself.

Excluded from the docs site (`backlog/`). Never deleted — tick the last box on completion.

## Root cause (two compounding defects, both reproduced live)

1. **The poll loop broke on the first non-pending state.** `main()` stopped when
   `gate_state(...) != "pending"`, but `gate_state` deliberately lets a **red outrank a pending** one
   *for display*. So a single transient ❌ ended the loop **while other axes were still running** —
   the comment froze on "Blocked" and, because the gate only runs on a push, nothing ever re-rendered
   it. Evidence (PR #78, head `966e3e5`): gate printed `gate=failing` at 13:01:00; `Analyze (actions)`
   finished green at 13:01:05 and `Analyze (python)` at 13:01:16. The comment never updated.
2. **The CodeQL axis read the wrong check.** It matched the check literally named `CodeQL` — the
   code-scanning-default-setup **umbrella**, which completes in ~2 seconds (13:00:55→13:00:57) and
   flaps while awaiting a result for a new head SHA — instead of the real `Analyze (…)` analyses that
   run to completion. GitHub's own message said it plainly: *"Code scanning is still expecting 1
   result from CodeQL for …"* — i.e. **pending, not failing**.

**Never a real block:** CodeQL was green with **0 open alerts**; the `code_scanning` ruleset rule
(the actual enforcement) cleared on its own, and the PRs were `MERGEABLE / CLEAN` while the comment
still said Blocked. The comment was advisory and stale.

## Done

- [x] New pure helper `axes_are_terminal(list_axes)` — the **only** condition that may stop the poll
  loop (at least one axis, and none pending). Distinct from `gate_state`, which keeps red-beats-pending
  for *display*. The loop now keeps polling while any axis runs, so a transient red self-corrects.
- [x] `_AXIS_PREFIXES` constant; the CodeQL axis now tracks **`Analyze`**, not the 2-second `CodeQL`
  umbrella check.
- [x] **"Show why" UX** (the maintainer's ask): a failing axis now **names the failing checks**
  (`` `Analyze (python)` failure ``) instead of only counting them; an axis with no check-run yet on
  this head SHA reads **⏳ "awaiting result"** instead of ❌.
- [x] Docstrings on `main()` / `_axes_from_checks` / `axes_are_terminal` record the failure mode so it
  cannot be reintroduced.
- [x] Tests: 6 new (48 in `test_pr_gate.py`, **857 unit tests** total) — the freeze regression (red +
  pending ⇒ `gate_state == "failing"` **but** `axes_are_terminal is False`), the umbrella-vs-Analyze
  regression, "awaiting result" pending, and the failing-check naming. ruff + ruff-format + codespell
  clean.

## Third defect — found by the PR's own CI (2026-07-12)

PR #83's **Quality Gate job itself failed** (red check, 19 others green). Cause was **not** the #76
logic: a transient **GitHub `HTTP 502 Bad Gateway`** on the sticky comment's `PATCH` raised an
unhandled `HTTPError` and killed the job — reddening a PR whose CodeQL, docs and every test passed.

Two real defects it exposed, both fixed here:

- [x] **`_api()` had no retry.** A single transient 5xx/429 decided the gate's fate. Now retries on
  `RETRYABLE_STATUS` (429/500/502/503/504) with capped exponential backoff (4 attempts, 1→2→4 s); a
  real 4xx still raises at once, because retrying a malformed request only buries the bug. Pure
  predicate `is_retryable_status()` so it is unit-tested offline.
- [x] **A reporting failure failed the build.** The gate's contract is *"it reports, the ruleset
  blocks"* (`main()` returns 0 always) — but an unhandled exception bypassed that. The poll body is
  now wrapped: whatever survives the retries is logged and the job **exits 0**. A lost comment is
  cosmetic; a red PR is not.
- [x] 10 more tests (58 in file, **867 total**); ruff/format/codespell clean.

**Note:** #76's fix *increased exposure* to this (polling to completion = more API calls = more
chances to hit a hiccup), so it belongs in this PR rather than a follow-up.

## Remaining

- [ ] Open PR (`Closes #76`). Class = `ci` + touches `tests/` → `risk:tests` → **not auto-merged**
  (human review), which is correct for a guardrail change.
- [ ] **NO RELEASE** — ci/tests only, no `src/` diff (per the new release policy). PyPI stays 0.24.0.
- [ ] Then Wave 1 = **FIE** (`FIE/DOC/BALANCETE`, `BALANCO`, `FIE/CAD`) — a `feat` in `src/`, so a
  **PATCH** bump; note the next version must clear the Test-PyPI floor (0.25.0).
- [ ] Follow-up (docs-only, no release): `docs/backlog/kanban-ready-backlog-sweep_20260708_220638.md`
  still documents the dead "Release gate — minor bump every merge" rule; correct it.

## Lessons captured (dotfiles-dev store + repo mirror)

- `release-only-when-shipped-package-changes.md` — `/release` skill + PreToolUse dispatch guard.
- `no-implementation-without-a-tracked-issue.md` — branch-creation guard + protected-`main` commit guard.
- `prefer-expression-form-over-statement-form.md` — expression over statement; `if cond: break` is E701.

## pr-gate-reage-a-thread-resolvida_20260809_204500

# pr-gate entrega o merge no fim do run (#216)

Branch: `fix/216-auto-merge-pr-comentado` · Issue: #216 · PR: #217

## O defeito, medido

O PR #214 era `risk:docs` + `size:XS` + `gate:passing` — classe auto-fundível, sem `do-not-merge` —
e mesmo assim ficou aberto até ser mergeado à mão. No log do run `31332843721` (o único run de
`pr-gate.yaml` daquele PR): `auto_merge=True` e **nenhuma** linha `auto-merge not enabled:`.
`allow_auto_merge` está `true` no repo, então não era config.

- [x] **A mutação de auto-merge foi recusada em silêncio.** GraphQL responde recusa com **HTTP 200 +
  `errors`**, e o `_enable_auto_merge` descartava o corpo. O seam de erro do `_api` é de status
  (4xx/5xx), então é **cego por construção** para esse canal.
- [x] **E foi recusada porque o gate armava no pior instante.** O `main()` armava o auto-merge
  **antes** do poll — no `opened`, quando nenhum check registrou e nenhuma thread existe, ou seja,
  quando o PR *parece* fundível. O GitHub recusa armar auto-merge exatamente nesse estado
  ("Pull request is in clean status").

## A hipótese ERRADA que este branch tentou primeiro — e como caiu

A primeira tentativa foi acrescentar `pull_request_review_thread: [resolved, unresolved]` ao `on:`,
partindo de "resolver thread não dispara nada na família `pull_request`" (verdade) e de uma consulta
à doc de **webhooks**, que confirma o evento e os tipos (também verdade, e **irrelevante**).

- [x] **`pull_request_review_thread` NÃO é gatilho de workflow.** O GitHub rejeitou o arquivo
  inteiro: o run `31335491644` voltou *"This run likely failed because of a workflow file issue"*, e
  **não houve nenhum run de `pull_request`** para o PR #217 — daí o PR ter ficado sem rótulo e sem
  comentário fixo. Levantado pelo CodeRabbit (actionlint 1.7.12: *unknown Webhook event*) e
  confirmado pelo run.
- **A lição:** o evento de webhook existir **não** implica que ele seja aceito no `on:`. São duas
  listas diferentes, e a doc de webhooks — que foi a que eu consultei — não distingue.

## Feito

- [x] Gatilho inválido removido; o `on:` volta a ser só `pull_request`, com o comentário registrando
  por que não se deve tentar de novo. ⚠️ **Duas razões distintas, não uma:**
  `pull_request_review_thread` **não é aceito no `on:`** (o arquivo é rejeitado);
  `pull_request_review` e `pull_request_review_comment` **são** gatilhos válidos, mas **nenhum
  dispara ao resolver uma thread** — logo não servem de substituto. Escrever "nem
  `pull_request_review*`" achatava as duas coisas.
- [x] `_enable_auto_merge` lê `errors` do corpo e imprime a razão no stderr.
- [x] `_merge_now` (novo) devolve `bool`; o `main()` entrega o merge **no fim do run**:
  `if bool_merge and not _merge_now(...): _enable_auto_merge(...)`. Os dois casos são mutuamente
  exclusivos — o GitHub aceita o merge quando nada bloqueia, e aceita armar o auto-merge quando
  algo bloqueia.
- [x] **Não é preciso gatilho nenhum para a thread:** quem espera o último bloqueio cair é o
  auto-merge nativo, que observa check obrigatório **e** conversa não resolvida.
- [x] `tests/unit/test_pr_gate.py`: **5 testes acrescentados** (4 no primeiro commit, 1 no segundo),
  levando o arquivo de **67 para 72** — medido, não incrementado: `git diff main...HEAD` mostra 5
  `+def test_`, todos sem `parametrize`, e `pytest -q` local fecha em `72 passed`. Um deles
  **proíbe** o gatilho inválido de voltar, e é **negative-control**: reintroduzir o gatilho (na forma
  citada `'pull_request_review_thread':`, que a asserção anterior por substring **deixava passar**)
  põe o teste vermelho, e removê-lo o põe verde de novo.
- [x] `docs/contributing.md` reescrito para a ordem certa + o aviso sobre o gatilho.

## Aberto

- [ ] ⚠️ **Este PR NÃO pode ser a prova de ponta a ponta — e isso é medido, não suposto.** Ele toca
  `tests/unit/test_pr_gate.py`, então `classify_risk` devolve `tests`, que **nunca** é
  auto-fundível. O run `31336165715` confirma: `risk=tests size=L gate=passing auto_merge=False` — o
  gate se recusou sozinho, corretamente. Logo nem `_merge_now` nem `_enable_auto_merge` chegam a ser
  chamados aqui, e o caminho continua **sem exercício real**. A verificação precisa de um PR de
  classe `docs`/`ci`/`deps` — o próximo da fila serve, e é ele que tem de registrar o log
  (`not merged now (405) — arming auto-merge instead` + `autoMergeRequest != null`, e depois o merge
  pelo próprio GitHub ao cair o último bloqueio).
- [ ] **Falta um gate de lint de workflow (`actionlint`).** Foi ele que pegou isto, via CodeRabbit, e
  o repo não o tem: `yamllint` valida YAML, não o schema do Actions. Issue de follow-up + paridade
  pre-commit ↔ CI.
- [ ] Interage com a **#212** (thread sem veredito): implementar na ordem, nunca em paralelo.
