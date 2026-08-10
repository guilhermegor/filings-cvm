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

## ✅ Medição 1 — o próprio PR #221 (e ela rendeu 4 fatos, 3 deles inesperados)

1. ⚠️⚠️ **A config subiu com um bloco INVÁLIDO e ninguém teria visto.** `pre_merge_checks` foi
   escrito no **topo** e não é chave válida ali — o CodeRabbit **ignorou o bloco inteiro**
   (`Unrecognized key: "pre_merge_checks"`) e reportou num `NOTE` **dentro do comentário de
   review**, num PR que **fundiu sozinho**. Eu havia conferido as chaves na *configuration
   reference*, que lista `pre_merge_checks` como seção própria. **A doc confirma que o nome
   EXISTE; ela não diz ONDE ele é aceito.** Corrigido no #222, agora validado contra o **schema
   publicado** (top-level, `reviews.*` e os 57 `tools` — 0 chave inválida).
2. ⭐ **O auto-merge funcionou — 1ª vez desde o #216.** `risk=docs size=L gate=passing
   auto_merge=True`, `mergedBy: app/github-actions`. Era a prova pendente, e ela só apareceu num PR
   **sem arquivo de teste** — exatamente como o achado estrutural do #219 previa.
3. ⚠️ **O bug #104 reproduziu (4ª observação):** merge por bot ⇒ issue **OPEN**, branch remota
   **viva**, card travado em *In progress*. Remediado pelo caminho documentado
   (`gh workflow run reconcile-merged-prs.yaml`), **nunca à mão** — o sweep fechou a issue e apagou
   a branch.
4. ⚠️ **`required_review_thread_resolution` NÃO é trava num PR sem thread.** O CodeRabbit revisou e
   disse `No actionable comments`, mas o PR **fundiu antes** de qualquer thread existir. A regra
   bloqueia thread **existente e não resolvida** — ela não espera o revisor chegar. Isso muda a
   leitura da opção **(c)** do achado abaixo: a "rede de segurança" que eu supus **não existe** para
   um PR que o bot não comenta.

5. ✅ **PERGUNTA RESPONDIDA: o `.coderabbit.yaml` VALE para o PR que o introduz.** Prova direta — o
   aviso `Unrecognized key` só pode ter vindo de o bot **ter lido o arquivo do próprio PR**. Então
   o #221 já foi revisado sob `assertive`, e a medição começa nele, não no seguinte.
6. ✅ **A linha de base é `chill`, e isso agora é fato, não suposição.** Não existia
   `.coderabbit.yaml` no repo até o #221, e o `profile` **default do schema é `chill`** — logo
   **todos** os reviews anteriores (#210, #214, #217, #219) rodaram em `chill`. A comparação
   `chill` × `assertive` é portanto direta:

   | PR | profile | achados | procediam |
   |---|---|---|---|
   | #210 | `chill` (default) | 5 | 4 |
   | #217 | `chill` (default) | 1 | 1 |
   | #219 | `chill` (default) | 3 | 3 |
   | **#221** | **`assertive`** | **0** | — |

   ⚠️ **O zero do #221 não mede o profile** — o diff é uma config declarativa mais um ledger, sem
   lógica a criticar. Amostra de 1, e da classe errada. **Não concluir nada daqui.**

⚠️ **Sobre as `path_instructions`: ainda SEM sinal.** O review foi `No actionable comments`, então
este PR **não** mede se elas mudam a revisão — mede só que o arquivo é lido. Seguem 2–3 PRs de
medição real, e o primeiro com código de verdade é o que conta.

## Aberto

- [ ] **A medição das `path_instructions`** — ao longo de 2–3 PRs: o que ele passou a pegar que não
  pegava, e o que virou ruído. **Linha de base sem config:** #210 (5 achados, 4 procediam), #214,
  #217 (1, procedia), #219 (3, os 3 procediam).
- [ ] **Gate de schema para `.coderabbit.yaml`** — hoje o `yamllint` aprova (é YAML válido), do
  mesmo jeito que aprovava o workflow inválido do #217. A validação que pegou isto foi **ad-hoc**
  contra o schema publicado; sem gate, o próximo erro de chave volta a ser silencioso.
- [x] `profile: assertive` — **decidido pelo mantenedor**, ciente do custo: o protocolo da casa dá
  veredito verificado a **toda** thread (medido: 356–1126 chars por resposta em 7 reais), então cada
  achado a mais custa uma resposta escrita. Vale enquanto as `path_instructions` são não-provadas —
  um profile quieto esconderia o que elas pegam atrás de "nada a relatar". Revisitar após a medição.
- [ ] **Este PR é a primeira medição de si mesmo:** o `.coderabbit.yaml` vale para o PR que o
  introduz? Registrar o que for observado — se não valer, a 1ª medição real é o PR seguinte.
- [ ] Destilar para `templates/common/` (blueprintx#129) **só depois** da medição.

## ⚠️ Achado do gate sobre si mesmo — `.coderabbit.yaml` é INVISÍVEL ao `classify_risk`

O gate rotulou este PR **`risk:docs`**, e a medição explica por quê: `.coderabbit.yaml` **não casa
nenhuma regra** de `_RISK_RULES` (`bin/pr_gate.py:74-92`) — não é `src/`, `tests/`, lockfile, nem
prefixo de `ci` (`.github/`, `bin/`, `Makefile`, `tasks.sh`, `.pre-commit-config.yaml`,
`.coveragerc`, `.codespellrc`, `.yamllint`), nem termina em `.md`. A classe **veio inteira do
ledger** (`docs/backlog/*.md` → `docs`).

**Duas consequências, e a segunda é a que importa:**

1. Sozinho, o arquivo cairia em `other` ⇒ **não** auto-fundível. Conservador, tudo bem.
2. **Acompanhado de qualquer arquivo `docs`, ele herda `docs` ⇒ auto-fundível.** Ou seja, **o
   arquivo que governa como todo PR é revisado pode fundir sozinho**, pegando carona na classe do
   vizinho de diff.

⚠️ **E ele tem exatamente a forma que o próprio repo usa para justificar que `src/` nunca
auto-funde:** uma mudança de **um caractere** (`auto_review.enabled: true` → `false`) reduz a
cobertura de revisão em silêncio, e **todos os testes passam**, porque não há teste que afirme o
conteúdo desta config.

**Não corrigido neste PR** — é decisão de desenho, não conserto óbvio, e mudar o classificador aqui
seria alargar o escopo. As opções, para decidir com o mantenedor:

- **(a)** acrescentar `.coderabbit.yaml` aos prefixos de `ci` — rótulo passa a ser honesto, mas
  `ci` **também** é auto-fundível, então **não muda a elegibilidade**;
- **(b)** criar a noção de *"governa o próprio gate"* (`.coderabbit.yaml`,
  `bin/enable_repo_rules.sh`, talvez `.github/workflows/pr-gate.yaml`) como classe **não**
  auto-fundível — é o mesmo argumento do `src/`, aplicado à guarda em vez do produto;
- **(c)** aceitar como está, registrando que a trava real é a
  `required_review_thread_resolution` (as threads do CodeRabbit são vinculantes, então nada funde
  com thread aberta).

**Rede de segurança hoje:** a (c) vale de fato — este PR só funde depois de as threads do review
serem resolvidas. Então o risco é de *classificação*, não de merge sem revisão.
