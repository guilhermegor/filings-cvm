# Work ledger — #93 destravar as PRs do Dependabot + corrigir a regra de release revogada

Branch `chore/unblock-dependabot-93`. Fecha **#93**. Sem release (`ci`/`docs`, zero diff em `src/`).

## O que estava em jogo

#93 tinha duas metades: (a) destravar as PRs **#79**/**#80** do Dependabot, verdes mas congeladas
com `gate:failing` obsoleto e auto-merge não armado; (b) corrigir um doc git-trackeado que ainda
documentava a regra de release **revogada**. A execução revelou **mais três** defeitos reais.

## Feito

- [x] **Diagnóstico de #93 confirmado** (não presumido): as duas PRs seguiam `OPEN`, `MERGEABLE`,
  `CLEAN`, com `gate:failing` obsoleto e `autoMergeRequest: null`. Causa raiz = janela temporal
  (abertas 2026-07-12 14:02/14:05; #82 inverteu opt-in→opt-out e ligou `allow_auto_merge` às 17:31;
  o gate só roda em evento de PR) — **não** um bug do gate. Código do gate estava certo *nesse*
  ponto.
- [x] **Revisão de #79** (6 bumps de Actions) — as 6 versões conferidas contra as releases reais
  (`checkout@v7`, `setup-python@v6`, `cache@v6`, `upload-artifact@v7`, `download-artifact@v8`,
  `action-gh-release@v3`; todas são a latest de verdade). Par `upload@v7` ↔ `download@v8` é
  compatível por desenho (v8 existe *para* o formato do v7; `archive: true` segue default → zipa →
  v8 deszipa). `digest-mismatch: error` (novo default do v8) é endurecimento, não quebra.
  `gh-release@v3` = só runtime Node 24.
  - ⚠️ **Achado registrado**: os checks verdes **não cobrem** o que mais importa em #79.
    `release-pypi.yaml`, `release-test-pypi.yaml` e `deploy-docs.yaml` são `workflow_dispatch` /
    `workflow_call` — o handoff upload→download de artifact e o passo de GitHub Release **só serão
    exercidos no próximo release**. Mitigação já embutida no processo: o release do CRA usa o
    two-step Test PyPI → verify → PyPI, então o Test PyPI exercita o caminho novo antes do PyPI.
- [x] **Revisão de #80** (mypy 2.1→2.2, build 1.5.0→1.5.1) — CI roda `poetry install` a partir do
  lock, então o passo verde "Run Static Type Check (mypy)" **de fato** rodou o mypy novo. Ambas em
  `groups = ["dev"]` → zero efeito na wheel distribuída.
- [x] **#79 destravada e MERGED** via `@dependabot rebase` → o gate reavaliou sob as regras atuais →
  **auto-merge armou-se sozinho, sem rótulo** (`app/github-actions`, 12:11:18) → fundiu. É a
  confirmação que #81/#82 pedia. (Rótulo ficou em `gate:pending` só porque o merge caiu enquanto o
  gate ainda fazia poll — cosmético; o merge nativo esperou os checks obrigatórios.)
- [x] **#80 → substituída por #94**: o `@dependabot rebase` concluiu que o branch velho era obsoleto
  ("updatable in another way") e **fechou #80 abrindo #94** contra a main atual (3 bumps: codespell
  2.4.2→2.4.3, coverage 7.15.0→7.15.1, mypy 2.1.0→2.3.0; só `poetry.lock`; tudo dev). Desfecho
  saudável — #94 nasce sob as regras atuais.

### Defeito 1 (novo) — `dependabot.yml` pedia rótulos que não existem

Dependabot comentava um **erro em toda PR que abria** (#79, #80, #94): *"The following labels could
not be found: `deps`"*. `.github/dependabot.yml` declarava `labels: ["ci"]` e `labels: ["deps"]` —
**nenhum dos dois existe** no repo (existem `risk:ci` / `risk:deps`, aplicados pelo gate). Resíduo
de #77/#78.

**Correção = deleção, não provisionamento.** `bin/pr_gate.py` rotula toda PR pelos **caminhos**
alterados e decide auto-merge por essa classificação — nada lê um rótulo `ci`/`deps` cru
(`AUTO_MERGEABLE` guarda *nomes de classe* internos, não rótulos; só `do-not-merge` é lido do repo).
Os `labels:` eram uma segunda taxonomia que ninguém consome. Removidos, com um comentário no arquivo
explicando o porquê para que não voltem.

### Defeito 2 (novo, o importante) — o veto `XL` inutilizava o auto-merge de `deps`

#94 = `risk:deps` + **`size:XL`** (579 linhas, 1 arquivo) → `is_auto_mergeable` vetava. Mas #80, com
2 bumps, deu `size:L` → armaria. **Se a bump semanal se auto-funde dependia de quantos pacotes
calharam de se mover na semana** — a metade `pip` da meta de #81/#82 estava estruturalmente morta.

O veto `XL` pergunta *"esse diff é grande o bastante para um humano olhar?"*. Num lockfile
regenerado a pergunta não significa nada: o tamanho acompanha quantos **hashes** se moveram, não
quanto risco chegou.

**Correção (escolha do usuário, opção recomendada):** o veto `XL` é dispensado **só** quando o
diff é **exclusivamente `poetry.lock`**. `pyproject.toml` fica **fora** da exceção de propósito — é
lá, num range editado à mão, que o risco de dependência mora.
- `LOCKFILE = "poetry.lock"` nomeado uma vez (é gatilho de `deps` **e** a exceção — não podem
  divergir).
- `is_lockfile_only(list_paths)` — seam puro e testável.
- `is_auto_mergeable(..., bool_lockfile_only=False)` — parâmetro novo com default seguro, então
  todas as chamadas/testes existentes seguem válidos.
- **TDD**: 9 testes escritos primeiro, falhando pelo motivo certo, depois a implementação.
- **Verificado contra os bytes reais de #94** (243+336, `["poetry.lock"]`) → `risk=deps size=XL
  lockfile_only=True auto_merge=True`. Vetos de `src`/`docs` em `XL` e o carve-out do `pyproject`
  seguem intactos.

### Defeito 3 (novo) — `docs/contributing.md` documentava o modelo **revogado**

Página **publicada** afirmando *"o auto-merge **só acontece com o rótulo `automerge`** (opt-in
explícito — a classificação não é consentimento)"*. #82 inverteu isso para **opt-out** e não
atualizou a página — errada desde 2026-07-12. Reescrita para o modelo opt-out + a exceção do
lockfile (em pt-BR: página publicada, público humano, conforme a fronteira de idioma que a própria
página define).

### A metade (b) de #93 — a regra de release revogada

- [x] `docs/backlog/kanban-ready-backlog-sweep_20260708_220638.md` (git-trackeado) reescrito: título
  + intro + `4a` agora dizem **release só quando `src/` muda**; pre-1.0 `feat`/`fix` → **PATCH**,
  breaking → **MINOR**; versão calculada contra o **máximo dos DOIS índices**. Marcado explicitamente
  que a regra de 2026-07-09 está **revogada**, para uma sessão futura não a seguir. Máquina do
  two-step Test PyPI → PyPI (4b–4e) **preservada** — continua correta. `X.Y.0` → `X.Y.Z` (3
  ocorrências) e o back-reference "Release gate" da linha ~280 corrigido.
  - ⚠️ O parágrafo final de **Rationale** ainda defendia o bump **minor** — pego lendo o arquivo, não
    pelo grep. Reescrito.
- [x] `SECURITY.md` (**publicado, voltado ao usuário**) afirmava *"every release is a minor bump"* —
  falso desde 2026-07-12. Corrigido para "only the newest release receives fixes" (a afirmação que
  sustenta a política e segue verdadeira).
- [x] **Ledgers por branch NÃO reescritos** de propósito (`docs/CLAUDE.md`): "minor bump → 0.15.0"
  num ledger é **registro histórico** do que era verdade então, não uma regra viva.

## Gates

- [x] `ruff check` + `ruff format --check` · `mypy` · `codespell` · `yamllint` — limpos.
- [x] **1019 testes unitários** passam (9 novos).
- [x] `mkdocs build --strict` limpo.
- [x] Verificação end-to-end contra os dados reais de #94 (acima).
- [ ] Rodar sob **os dois pandas majors**: nada aqui toca pandas (`bin/`, docs, yaml) — o suite não
  discrimina. Registrado como decisão consciente, não omissão.

## Aberto / próximo

- [ ] **#94** deve **armar auto-merge sozinha assim que esta PR fundir** e o gate reavaliar. Se não
  armar, o bug está no wiring do call site, não em `is_auto_mergeable` (testado).
- [ ] Confirmar que a **próxima** PR semanal do Dependabot arma sozinha, sem erro de rótulo — os dois
  defeitos que impediam isso (rótulo inexistente + veto XL) morrem com esta PR.
- [ ] Lição BlueprintX a capturar: **um heurístico de tamanho não mede nada num artefato gerado por
  máquina** — vetar por tamanho um lockfile é medir contagem de hash e chamar de risco. Generaliza
  para qualquer gate size-based (lockfiles, snapshots, migrations, código gerado).
- [ ] Depois desta: **Wave 2 PR 3/4 = `SECURIT/DOC/INF_MENSAL_CRA`** (zip anual, 8 membros) →
  release **PATCH** (provável 0.25.4).
