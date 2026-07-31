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
