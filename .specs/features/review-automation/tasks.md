## coderabbit-yaml-explicito_20260810_113000

# `.coderabbit.yaml` explícito (#224)

Branch: `chore/224-coderabbit-yaml-explicito` · Issue: #224 · Continua o #220/#222

## Princípio adotado

**Toda chave de comportamento fica pinada, inclusive as que já batem com o default de hoje**, cada
uma anotada com `(default: X)`. Um default que vira do lado do servidor muda o que acontece aqui
**sem commit** — e esta sessão levou 3 mordidas dessa família em 2 dias (#217, #222). O arquivo
passa a ser a verdade; a anotação faz uma deriva futura aparecer como **diff contra a realidade**,
em vez de mudança silenciosa.

**A fronteira, medida e não estética:** pinar comportamento **sim**; pinar os ~45 linters de
linguagens que o repo não tem **não** — eles nunca disparam, e a parede ilegível destrói a
auditoria (foi ela que revelou o `actionlint`).

**Cobertura medida:** 0 chave inválida contra o schema; **1 única** chave do schema fora do
arquivo (`reviews.slop_detection.label`), e a razão está escrita no próprio yaml.

## Feito

- [x] ⭐ **`knowledge_base.code_guidelines.filePatterns` → `**/CLAUDE.md` + `docs/contributing.md`.**
  O bot lê as convenções **onde elas vivem**. As `path_instructions` deixam de ser o rulebook e
  ficam com o **subconjunto enfático** (contrato pinado ao header, float proibido, PII fora de
  `tuple_cnpj_cols`) — redundância deliberada onde errar é caro. Escrito no arquivo: *quando uma
  regra daqui e um `CLAUDE.md` discordarem, o `CLAUDE.md` vence e este arquivo está velho.*
- [x] ⭐ **`abort_on_close: false`** (default `true`). O default **abortava a review quando o PR
  fundia** — foi o que matou a review do #223 (`Currently processing new changes…` + auto-merge).
  Não impede o merge; para de **perder** o achado.
- [x] **`high_level_summary_in_walkthrough: true`** — o resumo sai da **descrição** do PR. O repo
  tem template obrigatório de 5 seções com hook de bloqueio; conteúdo gerado fora da descrição
  mantém a descrição 100% humana.
- [x] `high_level_summary_instructions` — pede que o resumo nomeie o que a casa considera perigoso:
  mudança em `contracts/`, coluna numérica virando float, CPF em `tuple_cnpj_cols`, gate sem
  paridade pre-commit ↔ CI, contagem derivada restatada em doc publicada.
- [x] `auto_title_instructions` — só dispara com `@coderabbitai` no título (opt-in por PR).
  Codifica que **o título vira o subject do squash commit**: Conventional Commits, ≤72, imperativo.
- [x] `poem: false` e `in_progress_fortune: false` explícitos; `chat.art: false`.
- [x] **Labels: `suggested_labels`/`auto_apply_labels`/`issue_enrichment.labeling.*` todos off** —
  o `pr_gate.py` é dono de `risk:`/`size:`/`gate:`, e **só um** pode ser.
- [x] `auto_review.auto_pause_after_reviewed_commits: 0` (default **5**) — um PR longo é justamente
  onde o commit tardio é menos revisado; pausa silenciosa é gate que para sem avisar.
- [x] `path_filters` exclui só artefato gerado (`poetry.lock`, `coverage.*`). **`tests/fixtures/`
  fica revisável de propósito**: um fixture mudando **é** o evento que interessa.
- [x] `code_generation.{docstrings,unit_tests}.path_instructions` — o que as *finishing touches*
  escrevem tem de passar nos mesmos gates (NumPy + tabs + 99 cols; pytest sem `TestCase`, e o aviso
  explícito de que **teste derivado do próprio contrato é tautologia**).
- [x] `issue_enrichment.planning.auto_planning: false` — issue aqui é registro de decisão, escrita
  por template; conteúdo gerado fica fora, pela mesma razão da descrição do PR.

## ⚠️ Dois achados do schema que a doc não deixa óbvios

1. **`auto` NÃO é constante — ele lê a visibilidade do repositório.** Em `scope` significa "local
   para repo público, global para privado"; nas integrações, "desabilitado para repo público". O
   repo é público **hoje**; no dia em que virar privado, **todas** essas chaves mudam de
   comportamento **sem commit e sem diff**. Por isso `knowledge_base.{issues,pull_requests}.scope`
   ficaram **`local`** e as integrações **`disabled`**, explícitos.
2. **`pre_merge_checks.<check>.mode: error` só BLOQUEIA se `request_changes_workflow: true`.** Ou
   seja, essa flag não é só "auto-aprovar" — é o **interruptor que dá dentes** aos pre-merge checks.
   Sem ela, `error` só reclama mais alto.

## ⚠️ Lacuna encontrada e NÃO fechada

**O título do PR vira o subject do squash commit** quando o auto-merge funde — e **nada o valida**:
o commitizen e o gitlint rodam na **mensagem de commit**, nunca no título do PR. Hoje o único
controle é `pre_merge_checks.title.mode: warning`.

Fechar de verdade exige `mode: error` **+** `request_changes_workflow: true`, o que significa
**permitir que um bot segure um merge**. Ficou documentado no arquivo como caminho de upgrade, para
decidir depois da medição do #220.

## Aberto

- [ ] Decidir o upgrade acima (título vinculante) — após a medição do #220.
- [ ] **Gate de schema** para o `.coderabbit.yaml`: a validação que pegou tudo isto foi **ad-hoc**
  (baixar o `schema.v2.json` e comparar as chaves). O `yamllint` aprova o arquivo quebrado, igual
  ao workflow inválido do #217. Sem gate, o próximo erro de chave volta a ser silencioso.
- [ ] Medir se o `code_guidelines` de fato muda a revisão — é a aposta central deste PR.

## coderabbit-yaml-piloto_20260810_022000

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

⚠️ **Sobre as `path_instructions`: ainda SEM sinal nesta rodada.** O review foi
`No actionable comments`, então este PR **não** mede se elas mudam a revisão — mede só que o arquivo
é lido.

## ✅ Medição 2 — PR #227 · **o primeiro sinal real, e ele veio das instruções**

Primeiro PR revisado com a config completa em `main` (`code_guidelines` apontando para os
`CLAUDE.md`, `assertive`, `abort_on_close: false`). **3 achados, os 3 marcados
`_Source: Path instructions_`** — ou seja, produzidos pelas instruções, não pela análise genérica.
**Os 3 procediam**, verificados contra o código antes de aceitar:

| achado | verificação |
|---|---|
| faltava `docs/submission/` no checklist | a listagem de `docs/` traz `ingestion` **e** `submission` |
| ⚠️ **regra de reader aplicada a writer** | `submission/__init__.py:34-35` reexporta **direto** (sem portal root) e `grep -rn FileContract src/filings_cvm/submission/*.py` volta **vazio** |
| conclusão explícita só p/ mudança interna | deixava de fora a mudança **pública** que legitimamente não pede doc |

⚠️⚠️ **O segundo é o achado que justifica o piloto inteiro.** Eu escrevi uma regra de **leitor** e a
apliquei a um glob `{ingestion,submission}` que inclui **escritor** — onde as **duas** afirmações são
falsas. A instrução mandaria o revisor cobrar `FileContract` e cadeia de portal root de um writer que
não tem nem um nem outro: **revisão confiante e errada**, sem nada vermelho em lugar nenhum.

E o detalhe que fecha o círculo: **esse era exatamente o risco escrito no *Reviewer Focus* do próprio
PR** (*"instrução errada custa mais que instrução ausente"*). O risco que eu declarei se materializou
no PR que o declarou — e quem pegou foi a config que o PR estava introduzindo.

**Consequência de desenho:** a instrução foi **dividida por direção**. As duas metades desta
biblioteca **não compartilham caminho de registro**, então um glob único sobre `{ingestion,submission}`
é errado por construção. Comentário no arquivo registra o porquê, para ninguém re-unificar.

**Comparação com a linha de base (`chill`, sem config):**

| PR | profile | config | achados | procediam | origem |
|---|---|---|---|---|---|
| #210 | `chill` | — | 5 | 4 | genérica |
| #217 | `chill` | — | 1 | 1 | genérica (`actionlint`) |
| #219 | `chill` | — | 3 | 3 | genérica |
| #221 | `assertive` | parcial | 0 | — | — (diff sem lógica) |
| **#227** | `assertive` | **completa** | **3** | **3** | ⭐ **path instructions** |

⚠️ **Ainda não dá para atribuir o resultado ao `profile`** — a amostra é 1 PR por configuração, e as
classes de diff são diferentes. O que **está** medido é a **origem**: as instruções produzem achados
que a análise genérica não produzia, e a precisão nesta rodada foi **3/3**.

## Aberto

- [ ] **Continuar a medição** por mais 1–2 PRs com código de verdade (um reader novo é o caso ideal,
  já que as instruções mais fortes são as de `contracts/**` e `ingestion/**`). Perguntas em aberto:
  taxa de **ruído** (0 até agora) e se o `code_guidelines` (ler os `CLAUDE.md`) produz achado
  próprio, distinguível dos das `path_instructions`.
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
- ~~**(c)** aceitar como está, registrando que a trava real é a
  `required_review_thread_resolution`.~~ ⛔ **DESCARTADA — MEDIDA COMO FALSA, 2×.**

⚠️ **A "rede de segurança" que eu supus aqui NÃO existe.** Escrevi que a (c) valia porque as threads
do CodeRabbit são vinculantes, então nada fundiria com thread aberta. **Errado**: a regra bloqueia
thread **existente e não resolvida** — ela **não espera o revisor chegar**.

Medido nos dois sentidos:

- **#221** fundiu **antes** de o bot comentar qualquer coisa;
- **#223** fundiu **durante** a review, com o comentário do bot dizendo literalmente
  *"Currently processing new changes in this PR"*.

Ou seja, não é corrida de timing: **é ausência de regra**. Num PR de classe auto-fundível que o bot
ainda não comentou, **não há trava nenhuma**. Sobram (a) e (b) — e a (b) ganhou força, porque o
comportamento seguro já acontece por acidente quando o `.coderabbit.yaml` vem sozinho no diff
(classe `other`, medido no #227), e só falha quando ele pega carona num diff com `docs/`.

## review-workflows-296_20261031_120000

# Review-automation workflows from the BlueprintX scaffold (#296)

Source: `blueprintx/templates/python-common/` and `templates/common/bin/` (read only). None of the
target files existed on `origin/main` before this branch.

## Imported

- [x] `.github/workflows/coderabbit_trigger.yaml` — CodeRabbit refuses automatic reviews here
  (fewer than 10 stars, refusal notice on #291), so `auto_review` never fires. The request is
  posted with the existing `GH_PAT_REVIEW_TRIGGER` user PAT. Fork PRs are skipped.
- [x] `bin/check_review_threads.py` + `.review-bots.yaml` + `tests/unit/test_check_review_threads.py`.
  The surface was extended to these files by the coordinator: the three items below depend on
  them. Roster: `coderabbitai[bot]`, `guilhermegor-review-ladder[bot]`, plus the ladder's
  comment-marker row.
- [x] `.github/workflows/review_threads.yaml` + `bin/rerun_stale_gate_runs.sh`.
- [x] `.github/workflows/review_retry.yaml` + `bin/retry_rate_limited_review.py`.

## Adaptations

- [x] Ruff: indentation converted to tabs (this repo's `ruff.toml`), and a `codespell` hit fixed
  in a docstring.
- [x] Test helper `_git` drops inherited `GIT_*` variables. Under the pre-commit `unit-tests`
  hook, `GIT_INDEX_FILE` points at the real index, so the scratch repo's `git add` staged `a.txt`
  into this branch's commit. The bug is upstream too, and worth backporting to the scaffold.
- [x] The workflows use the repo's `actions/checkout@v7` / `setup-python@v7` tags and a pinned
  `pyyaml==6.0.3` (the locked version), not Poetry, matching `pr-gate.yaml`. The jobs need
  only `pyyaml` + `gh`, and `review_threads` runs on every review comment.
- [x] `review_threads` gets a per-PR `concurrency` group so a burst of comments keeps one run.

## Dropped as duplicates

- [x] `pr-reconcile.yaml` + `bin/pr_reconcile.sh` — same job as the existing
  `reconcile-merged-prs.yaml` + `bin/reconcile_merged_prs.py`, which has the same triggers
  (`closed` + a daily sweep + dispatch). The existing one is unit-tested
  (`tests/unit/test_reconcile_merged_prs.py`) and also refuses to delete the default branch.
  Two workflows would race on the same issues and branches.
- [x] `pr-gate.yaml` — left unchanged. The template's `pr-gate.yaml` / `bin/pr_gate.py` are
  older than this repo's own gate. `review_threads` is a separate check that only reads. It
  never labels the PR, comments on it, or arms auto-merge, so nothing gets gated twice.

## Gate parity

- [x] No pre-commit hook for `review_threads` / `review_retry` / `coderabbit_trigger`: each
  needs a live PR number, the GitHub API and (for two of them) a secret, and none of those
  exist at commit time. The gate's unit tests run in both pre-commit and CI through the
  existing unit-test hook and step. The new YAML is covered by `lint-yaml` / `lint-actions`.

## Not done here — owner decisions / follow-ups

- [ ] Making `Review threads answered` a required check is an owner decision (ruleset). It is
  not required by this PR. Measured locally: #287 and #291 both report "reviewed only on
  SUPERSEDED code", so it would block PRs whose last push was not re-reviewed.
- [ ] `tests/unit/test_review_retry.py` (1,023 lines upstream) was not imported. It is outside
  the claimed surface, so `bin/retry_rate_limited_review.py` ships without unit tests.
  A `--dry-run` against the live repo ran clean: 16 open PRs, none rate-limited.

## Docs

- [x] `.github/CLAUDE.md` — a "Review automation" section
- [x] `CONTRIBUTING.md` — what happens to a PR after it opens

## roster-git-dir-326_20261031_120000

# Stop the roster lookup following GIT_DIR inside a git hook

- [x] Reproduced: `test_an_absent_roster_makes_the_gate_a_no_op` failed under the pre-commit unit hook and passed standalone, because the hook's `GIT_DIR` outranks `git -C`
- [x] `_roster_exists_on_default_branch` drops `GIT_DIR`, `GIT_WORK_TREE` and `GIT_INDEX_FILE` from the subprocess environment
- [x] Regression test sets `GIT_DIR` to a repo holding the roster on `origin/main` and asserts an unrelated dir still reports it absent

Completed — kept as a record.
