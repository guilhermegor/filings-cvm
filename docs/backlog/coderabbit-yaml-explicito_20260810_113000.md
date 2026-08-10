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
