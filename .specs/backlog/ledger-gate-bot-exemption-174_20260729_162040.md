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
