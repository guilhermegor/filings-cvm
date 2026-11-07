## bin-gates-unit-tests-192_20261029_120000

# Work ledger — #192 unit tests for `check_docstrings`, `check_typing`, `check_provenance`

Branch `test/bin-gates-192`. Fecha **#192**. **Sem release** (só `tests/` e `docs/`).

- [x] `tests/unit/test_check_provenance.py` (5 testes) — read sem stamp falha, par passa.
- [x] `tests/unit/test_check_typing.py` (9 testes) — função sem `@type_checker`, classe raiz sem
  metaclass, subclasse, dunder e Pydantic com metaclass.
- [x] `tests/unit/test_check_docstrings.py` (7 testes) — tipo de retorno/parâmetro divergente é
  erro duro; docstring ausente e drift de `Raises` são só aviso.
- [x] Mutação por script: cada gate quebrado (`if False`) deixa testes vermelhos; restore
  verificado por sha256 nos três.
- [x] Scripts de `bin/` não modificados; nenhum precisou de refactor para ser testável.
- [x] Completed — kept as a record.

## gate-actionlint_20260810_011500

# Gate de actionlint (#218)

Branch: `chore/218-gate-actionlint` · Issue: #218 · Origem: #217

## Por que existe

O #217 mandou para a CI um `on:` com `pull_request_review_thread`, que **não é gatilho de
workflow**. Passou em **todos** os hooks locais, inclusive o `yamllint` — era YAML impecável. O
GitHub rejeitou o arquivo inteiro (run `31335491644`), e o workflow **não rodou de forma alguma**:
o PR ficou sem rótulo e sem comentário do gate, o que parece lentidão, não morte. Quem pegou foi o
CodeRabbit, que roda `actionlint` por conta própria.

## Feito

- [x] `bin/lint_actions.sh` — fonte única (molde do `lint_shell.sh`): resolve `poetry run actionlint`
  → binário de sistema → skip com aviso. **Falha se não achar workflow nenhum** (o `actionlint` sai 0
  sem arquivos; um gate que passa vazio é pior que nenhum).
- [x] `SHELLCHECK_OPTS=--severity=warning` pinado no script. O `actionlint` chama shellcheck em todo
  bloco `run:`; sem o pin, os snippets inline ficariam num padrão **mais rígido** que o dos
  `bin/*.sh` (`bin/CLAUDE.md`). Não mexe nos erros de schema — medido: os 3 achados reais
  permanecem, os 14 `info`/`style` somem.
- [x] Paridade completa: hook `lint-actions` (`.pre-commit-config.yaml`, escopado por `files:`),
  step na `tests.yaml`, `make lint`, `tasks.sh`.
- [x] **Na CI o binário é instalado e a ausência FALHA o job** (`command -v actionlint || exit 1`) —
  o skip gracioso é certo localmente e seria placebo lá. Pinado em `v1.7.12`, baixado da página de
  releases (não `curl | sh`).
- [x] **Não é dev-dep do Poetry:** `actionlint-py` é **sdist-only** (medido: `pip download
  --only-binary=:all:` → *No matching distribution*) e baixa o binário Go em tempo de build. Viraria
  um fetch de rede dentro de todo `poetry install`, nas 3 matrizes. O `shellcheck-py`/`shfmt-py`
  publicam wheels de verdade — é essa diferença que decide.
- [x] 2 testes de integração, com **negative control**: o defeito exato do #217 num workflow
  sintético tem de dar `unknown Webhook event`. Guard de skip quando o binário falta — verificado
  nos dois estados (com binário: 6 passed; sem: **2 skipped**, nunca passe falso).
- [x] Docs: `.github/CLAUDE.md` (tabela yamllint × actionlint + as 2 decisões deliberadas) e
  `docs/contributing.md`.

## Dois defeitos REAIS que o gate expôs de saída

Nenhum é deste diff — estavam em `main`, verdes, há tempo:

- [x] **`tests.yaml` declarava um output impossível.** `ready_for_release:
  ${{ jobs.test.result == 'success' }}` — dentro de `on.workflow_call.outputs.value` o contexto
  `jobs.<id>` expõe **só `outputs`**, nunca `result`. Ou seja, um output que anunciava "os testes
  passaram?" **jamais poderia dizer sim**. E era morto: nada o lia (as duas workflows de release
  gateiam por `needs:`). Removido, com o porquê no arquivo.
- [x] **SC2046 nas duas workflows de release** (`--without $(IFS=,; …)` sem aspas): um nome de grupo
  com espaço viraria dois argumentos e o `poetry install` excluiria o grupo errado, em silêncio, **no
  caminho de release**. Aspas postas nas duas.

Isso é o argumento do gate melhor que qualquer prosa: o primeiro uso já achou um bug no caminho de
publicação.

## Aberto

- [ ] `bin/install_shell_linters.sh` **não** instala o `actionlint` — o apt não o empacota, e as 4
  branches por gerenciador são escopo próprio. Docs e a mensagem de skip apontam para a página de
  releases, sem prometer o instalador. Avaliar se vale acrescentar.
- [ ] ⚠️ **Verificação de ponta a ponta do #216 segue pendente — e este PR TAMBÉM não serve.**
  Eu previ classe `ci`; o gate mediu **`risk:tests`**. O PR acrescenta testes, e `tests` **precede**
  `ci` em `_RISK_RULES` (`bin/pr_gate.py:74-86`) — a classe é sempre a mais perigosa que qualquer
  caminho casa. Mesma razão do #217.
  **O achado estrutural:** todo PR que traz o próprio teste é classe `tests`, logo **nunca**
  auto-fundível. Como a casa exige teste com a mudança, **um PR de `ci` com teste jamais exercita o
  auto-merge** — o caminho só se prova num PR sem nenhum arquivo de teste: docs puro, ou uma bump do
  Dependabot (que é `deps` e não leva teste). É por isso que o caminho ficou 2 PRs sem exercício sem
  ninguém notar.

## precommit-poetry-lock-check-264_20261029_120000

# Work ledger — #264 pre-commit poetry-lock check

Branch `ci/precommit-lock-check-264`. Closes **#264**. No release (zero diff in `src/`).

## Done

- [x] Confirmed at `origin/main`: no `poetry check --lock` hook exists in
  `.pre-commit-config.yaml`; the check is CI-only.
- [x] Added local hook `poetry-lock-check` (`bash bin/poetry_exec.sh check --lock`,
  `files: ^(pyproject\.toml|poetry\.lock)$`, `pass_filenames: false`), the same
  command as the CI step, routed through the repo's poetry wrapper.
- [x] Proved in a scratch copy: clean passes; a dependency added to `pyproject.toml`
  without re-locking fails ("pyproject.toml changed significantly since
  poetry.lock was last generated"); reverting passes again.
- [x] `.github/CLAUDE.md` gate list checked: it does not enumerate this check, so
  no edit. `tests.yaml` untouched (held by #258).
- [x] Ledger ticked — Completed — kept as a record.

## quality-guards-294_20261031_120000

# Work ledger — #294 code- and test-quality guards

Branch `ci/294-quality-guards`. Closes **#294** (child B of #292). No release (zero diff in `src/`).

## Done

- [x] Confirmed at `origin/main` (`git ls-tree --name-only origin/main bin/`): none of the nine
  guards, `bin/required-checks.txt` nor a required-checks sync script exists.
- [x] Vendored VERBATIM from `~/github/blueprintx/templates/python-common/bin/`:
  `check_function_length.py`, `check_complexity.sh`, `check_dead_code.py`,
  `check_all_exports.py`, `check_one_assert.py`, `check_fixture_scope.py`,
  `check_assertion_weakening.py`, `check_gate_integrity.py`. Verbatim so a later sync is a copy.
  `bin/` is excluded from ruff (`ruff.toml`), so the template's space indentation stays.
- [x] Adapted `check_coverage_floor.py`: the template derives its floor from
  `src/capabilities/*/{domain,application}`, which this library does not have (it would no-op
  forever). Here the floor is every function-bearing module under `ingestion/` + `submission/`
  (58 today); zero discovered modules is a failure.
- [x] `check_required_checks_sync.py` — trimmed from BlueprintX `bin/ci/` to its
  `--required-list` mode, with one adaptation: a `pull_request.branches` filter naming `main` is
  not a filter (the ruleset only judges PRs into `main`). `bin/required-checks.txt` mirrors the
  ruleset read on 2026-10-31: the 3 `Run Automated Tests (<os>)` contexts + `build`.
- [x] Ratchet instead of weakening: the template's guards fail hard and offer only per-line
  hatches (`# complexity-ok:`, `# one-assert-ok:`). Hatching ~1000 existing lines would edit
  ~150 files outside this PR's surface, so `bin/quality_ratchet.py` wraps the five flagging
  guards with the template's own ratchet shape (`check_comment_budget.py`'s `<count> <path>`,
  both directions: above fails, below fails "lower it"). Baseline: `bin/quality_baseline.txt`.
- [x] Baseline sizes (findings / files) recorded on 2026-10-31, re-measured after merging `71065cd`
  (first measured at `9ce9409`: complexity 309/88, one-assert 525/70 — #287 and #300 landed
  in between, which is why the ratchet must be re-written whenever main moves under this PR):
  - function-length: **6** / 5
  - complexity (C901 + PLR1702; tests 1, src 2, bin 8): **337** / 98
  - all-exports: **195** / 3 (193 of them `_internal/config/schemas/__init__.py`)
  - one-assert: **580** / 78
  - dead-code (>=80% confidence, gating tier only): **1** / 1 (`http_downloader.py` `msg`,
    an override parameter `urllib` requires)
  - fixture-scope, assertion-weakening, gate-integrity, coverage-floor, required-checks sync:
    **0** — pass on the tree with no baseline.
- [x] `check_dead_code.py` self-skips without `vulture` (template behaviour; not a Poetry dep
  here). CI installs a pinned `vulture` before the step, so the gate does run there.
- [x] `.codespellrc`: `notin` added to `ignore-words-list` (the template's own entry;
  `check_assertion_weakening.py` names the `ast.NotIn` node).
- [x] Hooks in `.pre-commit-config.yaml` and steps in `.github/workflows/tests.yaml`, each one
  contiguous labelled block (#293/#295 append to the same files).
- [x] Integration tests in `tests/integration/test_bin_scripts.py` for the ratchet and the
  required-checks sync.
- [x] CONTRIBUTING.md section, as its own final commit (file held by #296).

## Remaining

None: the work is complete (2026-10-31). Open items only follow main moving under the baseline, which
is fixed by re-running `--write-baseline` for the guard that moved.

Completed — kept as a record.

## ruf022-sorted-all_20261030_120000

# Enable ruff RUF022 (#101)

- [x] Confirm RUF022 is off in `ruff.toml` on origin/main
- [x] Add `RUF022` to `[lint] select`
- [x] Sort the 4 unsorted `__all__` (contracts, fidc, fidc/doc, fidc/doc/inf_mensal)
- [x] `ruff check src/ tests/ bin/` clean

Completed - kept as a record. Re-measure found 4 files, not the 6 in the issue
(`filings_cvm/__init__.py` and `ingestion/__init__.py` are already sorted).

Completed — kept as a record.

## schemas-gate-73_20261030_120000

# Work ledger — #73 schemas gate

Branch `ci/schemas-gate-73`. Gate: every class in `_internal/config/schemas/*.py` is a `BaseModel`.

- [x] `bin/check_schemas.py` (AST, in-file transitive bases, Enum family allowed).
- [x] `tests/unit/test_check_schemas.py` incl. negative case and real-tree non-empty check.
- [x] Hook + CI step in the same commit; notes in both CLAUDE.md files.
- [x] PR (`Closes #73`): #274.

Completed — kept as a record. PR #274 carries the work; the ledger stays as the branch history.

## isolate-git-env-in-tests-374_20261101_120000

# Isolate GIT_* env in tests (#374)

- [x] Autouse fixture in `tests/conftest.py` drops the git-hook `GIT_*` variables.
- [x] `tests/unit/test_conftest_git_isolation.py` proves it in a subprocess, one case per variable.

Completed — kept as a record.
