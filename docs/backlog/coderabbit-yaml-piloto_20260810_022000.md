# Piloto do `.coderabbit.yaml` (#220)

Branch: `chore/220-coderabbit-yaml-piloto` · Issue: #220 · Origem: blueprintx#129

## Por que aqui antes do template

Decidido com o mantenedor: este repo é o proving ground que gerou a evidência da blueprintx#129, e
congelar num template uma config nunca exercitada é o erro que a própria issue evita em outros
pontos. Medir 2–3 PRs, **depois** destilar.

## Feito

- [x] `.coderabbit.yaml` criado (não existia — o bot rodava no padrão).
- [x] **7 `path_instructions`**, todas levantadas de um `CLAUDE.md` que já governa aquele caminho;
  nenhuma inventada: `contracts/**`, `ingestion/**`, `src/**/*.py`, `tests/**/*.py`, `bin/**/*.sh`,
  `.github/workflows/**`, `docs/**`.
- [x] `language: en-US` — **sub-decisão da #129 fechada ao contrário do que ela propunha**. Não
  amarrar em `mkdocs.yml theme.language`: a fronteira já decidida aqui é *bot fala com contribuidor
  ⇒ inglês; só doc publicada segue o site*. **A fronteira é o público, não o repositório.**
- [x] `pre_merge_checks.docstrings` deliberadamente **ausente** (duplicaria
  `bin/check_docstrings.py`).
- [x] **Auditoria dos `tools`, um a um** — ver abaixo.

## ⭐ A auditoria, e o achado que ela produziu

A regra usual ("desabilite os linters do bot que duplicam os seus") está certa e é **metade**. A
outra metade é a lição do #217/#218: **um linter que o bot roda e nós NÃO temos é evidência de gate
faltando**. Foi literalmente assim que o `actionlint` chegou aqui.

**10 desabilitados — gate nosso, uma casa por regra:** `ruff`, `flake8`/`pylint` (superados pelo
ruff), `shellcheck`, `yamllint`, `sqlfluff`, `hadolint`, **`actionlint`** (só honesto desligar
**depois** do #218), `gitleaks`/`trufflehog` (dono = GitGuardian, required check).

**5 mantidos LIGADOS — não possuímos o gate:**

| tool | a lacuna |
|---|---|
| `zizmor` | **Segurança** de Actions — ≠ schema do `actionlint`. É a classe *workflow injection* (`github.event.*` interpolado em `run:`), e não temos gate nenhum |
| `markdownlint` | não há lint de markdown; o codespell é só ortografia |
| `checkmake` | o `Makefile` é superfície de CI e está inteiramente sem gate |
| `osvScanner` | CVE de dependência — a pergunta ainda aberta no **#90** |
| `presidio` | PII: o repo lida com CPF sob LGPD e mantém fixtures header-only **de propósito** |

⚠️ **Ligado ≠ adotado.** Cada um é pergunta em aberto; desligar só é honesto **depois** de adotar o
gate ou escrever por que não. O que eles reportarem no piloto é a medição que decide.

⚠️ **Tools de linguagens que este repo não tem ficam FORA do arquivo** — nunca disparam, então um
`enabled: false` para elas seria decisão que ninguém tomou, num arquivo que aí ninguém consegue ler.

## Aberto

- [ ] **A medição** — ao longo de 2–3 PRs, registrar aqui: o que ele passou a pegar que não pegava,
  o que virou ruído, e se as `path_instructions` de fato mudaram a revisão. **Linha de base sem
  config:** os reviews de #210 (5 achados, 4 procediam), #214, #217 (1, procedia) e #219 (3, os 3
  procediam).
- [x] `profile: assertive` — **decidido pelo mantenedor**, ciente do custo: o protocolo da casa dá
  veredito verificado a **toda** thread (medido: 356–1126 chars por resposta em 7 reais), então cada
  achado a mais custa uma resposta escrita. Vale enquanto as `path_instructions` são não-provadas —
  um profile quieto esconderia o que elas pegam atrás de "nada a relatar". Revisitar após a medição.
- [ ] **Este PR é a primeira medição de si mesmo:** o `.coderabbit.yaml` vale para o PR que o
  introduz? Registrar o que for observado — se não valer, a 1ª medição real é o PR seguinte.
- [ ] Destilar para `templates/common/` (blueprintx#129) **só depois** da medição.
