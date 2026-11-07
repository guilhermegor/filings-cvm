## backlog-ledger-gate_20260717_091038

# Work ledger — #108 deterministic work-ledger gate

Branch: `chore/108-backlog-ledger-gate` · Issue: #108 · Started: 2026-07-17

Make the per-branch work-ledger rule (`docs/CLAUDE.md`) structural instead of prose-only —
the analogue of `bin/check_typing.py` / `bin/check_provenance.py`.

## Done

- [x] `bin/check_backlog_ledger.py` — diff-based gate. Reuses `pr_gate.classify_risk`
      **per path** (set-membership, not most-dangerous collapse, so a `tests/` path can't hide a
      `ci`/`src` path). Fails on: src/ci diff with no ledger; bad ledger filename; ledger without a
      `- [ ]`/`- [x]` checkbox. Pure `check(paths, read_text)` core + injected git/IO edges.
- [x] `tests/unit/test_check_backlog_ledger.py` — covers `requires_ledger` (incl. the tests-hides-ci
      case), name regex, checkbox regex, and the four `check()` outcomes.
- [x] Wire `check-backlog-ledger` into `.pre-commit-config.yaml` (`always_run`, `pass_filenames:
      false`).
- [x] Wire the matching CI step into `.github/workflows/tests.yaml` + `fetch-depth: 0` on checkout
      (needs merge-base history). Gate parity honoured (both files, same change).

- [x] Gates green: ruff/ruff-format/codespell/pydocstyle/yamllint clean; 1244 unit tests pass
      (bin/ is ruff-excluded, so the module matches its space-indented peer `check_provenance.py`);
      gate proven end-to-end both ways (exit 0 with ledger staged, exit 1 without).

## Open

- [ ] Open PR (`Closes #108`), wait for review + merge. `ci` class → **no release**.

## Decisions / notes

- **`pyproject.toml` is exempt** (class `deps`, like `poetry.lock`). Reusing `pr_gate`'s path axis
  puts both under `deps`; the issue only named `poetry.lock`. If a hand-edited dependency range
  should demand a ledger, add `deps` to `LEDGER_CLASSES` — one-line change. Left exempt for now.
- The gate is a **no-op off a feature branch** (on `main`/tags the merge-base is `HEAD`, diff empty).

## ledger-bot-exemption-pr-author-176_20260730_215158

# Work ledger — #176 isenção de bot deve ler o AUTOR do PR, não o ator do run

Branch `fix/176-ledger-bot-exemption-pr-author`. Fecha **#176**. **Sem release** (`ci`/`docs`).
Follow-up direto do #174/PR #175 — e conserto de um bug **meu**.

## O que deu errado

O #175 introduziu a isenção de bot lendo **`GITHUB_ACTOR`**. Depois de mergeado, o #167 **continuou
vermelho no mesmo step**. Medindo os runs:

| run | quando | `actor` |
|---|---|---|
| `30191245294` | push original do dependabot | `dependabot[bot]` |
| `30470287147` | após meu 1º `update-branch` | **`guilhermegor`** |
| `30594329762` | após meu 2º `update-branch` | **`guilhermegor`** |
| **autor do PR #167** | imutável | **`dependabot[bot]`** |

⚠️ **`GITHUB_ACTOR` é quem DISPAROU o run, não o autor do PR.** Qualquer humano que toque num PR de
bot — `update-branch`, re-run manual, fixup — vira o ator e **desliga a isenção justamente quando ela
é necessária**. Pior: fui **eu** quem disparou os runs tentando desbloquear o PR, ou seja o ato de
consertar era o que impedia o conserto de funcionar.

⚠️ **A regra estava certa e o sinal errado.** O docstring que escrevi no #175 dizia *"keys on the
**author**, never the path"* — e a implementação lia o **ator**. Enunciar "isente por autor" não
basta: é preciso dizer **qual variável carrega o autor**.

## Feito

- [x] `tests.yaml`: `LEDGER_PR_AUTHOR: ${{ github.event.pull_request.user.login }}` no `env` do step,
  ao lado do `LEDGER_BASE_REF` que já usa esse mesmo padrão de contexto de PR.
- [x] `_ledger_author()`: prefere `LEDGER_PR_AUTHOR`, cai para `GITHUB_ACTOR` quando não há payload
  de PR (push em `main`, rodada local) — ali o ator **é** a resposta certa e é humano, então o gate
  vale. **Fallback na direção segura.**
- [x] `is_bot_actor()` continua **puro**; a precedência mora no helper de env.
- [x] Docstring do `is_bot_actor` corrigido com o aviso explícito de não alimentar `GITHUB_ACTOR`.
- [x] `docs/CLAUDE.md` corrigido — afirmava `GITHUB_ACTOR`.
- [x] 5 casos de precedência + 2 testes de regressão nomeados (o cenário #167 e o **inverso**: PR
  humano re-disparado por CI bot **não** isenta).

## Verificação (ponta a ponta, mesmo diff, variando só os atores)

- [x] PR de bot + run humano (**o caso do #167**) → **EXIT 0**
- [x] PR humano + run de bot → **EXIT 1**
- [x] sem `LEDGER_PR_AUTHOR`, humano → **EXIT 1**
- [x] comportamento antigo reproduzido → emite exatamente o erro que travava o #167
- [x] 54 testes no arquivo do gate; ruff (com `--config=ruff.toml`); yamllint; suíte completa.
- [x] ⚠️ Reincidência do `ERA001`: comentário **dentro de uma lista de tuplas** com `:` lido como
  código. Depois de 2 tentativas de reescrita, resolvido **movendo a prosa para o docstring** — que é
  onde ela pertence. Padrão já visto nesta sessão: não brigar com a heurística, mudar de lugar.

## Aberto / próximo

- [ ] PR (`Closes #176`) → aprovação → merge. **Sem release.**
- [ ] Então `gh pr update-branch 167` → checks verdes → **mergear o #167 por mérito**.
- [ ] Emendar a lição `human-artifact-gates-need-a-bot-exemption`: dizer **qual** variável carrega o
  autor, porque `GITHUB_ACTOR` é o palpite óbvio e é o errado.

## ledger-gate-bot-exemption-174_20260729_162040

# Work ledger — #174 work-ledger gate isenta PRs de bot

Branch `fix/174-ledger-gate-bot-exemption`. Fecha **#174**. **Sem release** (`ci`/`docs`, zero diff
em `src/`). Desbloqueia o **PR #167** do dependabot.

## O diagnóstico (o PR #167 não estava "parado", estava estruturalmente bloqueado)

O #167 (`actions/setup-python` v6→v7, 9 workflows) estava aberto desde **2026-07-26** e vermelho. A
primeira leitura — `mergeStateStatus: BEHIND` + 3 checks `CANCELLED` — sugeria **branch velha**.
Atualizei a branch (`gh pr update-branch`), o CI re-rodou… e falhou de novo.

⚠️ **Os `CANCELLED` eram ruído:** as pernas irmãs da matriz sendo derrubadas pelo `fail-fast`. O
sinal real era **um** job `failure`, e dentro dele **um** step:

```
Run Work-Ledger Enforcement
❌ branch touches a src/ci path but its diff adds no docs/backlog/...md work ledger
```

**`.github/workflows/**` classifica como `ci`, e um bot não escreve ledger** → todo PR de GitHub
Actions do dependabot nasce immergeável.

| PR do dependabot | toca | classe | resultado |
|---|---|---|---|
| #168 (`pre-commit`) | `.pre-commit-config.yaml` | `deps` (isento) | ✅ mergeou |
| #167 (`setup-python`) | `.github/workflows/**` | `ci` | ❌ bloqueado |

Foi por isso que o #168 passou e o #167 não — a diferença nunca esteve no conteúdo.

## Feito

- [x] `is_bot_actor()` em `bin/check_backlog_ledger.py`: sufixo `[bot]` (marcador **do próprio
  GitHub**, então nenhuma allow-list de nomes de bot para manter/apodrecer).
- [x] A isenção entra **no seam de I/O** (`__main__`), **não** na regra: `check()` continua **pura**
  e testável sem ambiente.
- [x] 12 casos de `is_bot_actor` (casing, espaços, `robotics-dev` que **não** é bot, `someone[bot]x`
  que **não** casa, `None`/`""` = humano).
- [x] **Controle negativo** — o teste que impede a isenção de virar buraco: `check()` **continua**
  reprovando um diff de workflow sem ledger, e o caminho humano normal (workflow + ledger válido)
  continua limpo.
- [x] `docs/CLAUDE.md`: a isenção documentada **com o porquê** e com o aviso de que ela é **por
  autor, jamais por caminho**.

## Verificação (simulação ponta a ponta, mesmo diff, só mudando o ator)

- [x] `GITHUB_ACTOR=dependabot[bot]` → **EXIT 0** (`ℹ️ bot-authored branch…`)
- [x] `GITHUB_ACTOR=guilhermegor` → **EXIT 1** (❌ ledger exigido)
- [x] **sem** `GITHUB_ACTOR` (rodada local) → **EXIT 1** — dev na máquina continua obrigado
- [x] ⚠️ **A 1ª simulação deu 3× EXIT 0 e quase me enganou:** o gate diffa o **índice**, e minhas
  mudanças estavam **unstaged** → ele via diff vazio e no-opava. **Um teste que passa por não ter
  visto nada é pior que um que falha.** Refeito com `git add -A` e aí os 3 casos discordaram como
  deviam. Sempre conferir *o que o gate enxerga* antes de acreditar num verde.
- [x] 47 testes no arquivo do gate; ruff/format; suíte completa.

## Aberto / próximo

- [ ] PR (`Closes #174`) → aprovação → merge. **Sem release.**
- [ ] Com o gate corrigido, **rerodar o check do #167** e mergear **por mérito** (sem `--admin`,
  sem ledger na mão).
- [ ] Lição BlueprintX a arquivar: um gate que exige **artefato humano** precisa de isenção para
  autor-bot, senão a automação de dependências morre em silêncio.
