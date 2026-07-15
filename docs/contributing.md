# **Contribuindo**

Tudo o que você precisa para desenvolver, testar e lançar esta biblioteca.

> **Veja também:** [Uso](usage.md) · [Referência da API](api.md) · o `CONTRIBUTING.md` na raiz do
> repositório contém a política autoritativa de branch/PR e de mensagem de commit.

---

## Preparando o ambiente de desenvolvimento

O projeto traz um `Makefile` e um `tasks.sh` equivalente, então use o que couber na sua máquina —
**`make init`** ou **`bash tasks.sh init`** quando `make` não estiver disponível (por exemplo, num
shell padrão do Windows).

```bash
make init        # cria o virtualenv do Poetry + instala deps + instala hooks de pre-commit
# ou, sem make:
bash tasks.sh init
```

`init` compõe `venv` (cria o virtualenv do Poetry e instala **todas** as dependências, inclusive
dev + docs) e `precommit` (instala os git hooks). O Poetry é instalado automaticamente se estiver
faltando.

## Testes e lint

```bash
make unit_tests          # poetry run pytest tests/unit/
make integration_tests   # poetry run pytest tests/integration/
make lint                # ruff + mypy + codespell + pydocstyle + gates de shell/sql/yaml
```

A CI roda os mesmos gates em cada pull request; mantenha-os verdes localmente antes de dar push.

## Servindo a documentação localmente

```bash
make docs_server   # mkdocs serve em http://0.0.0.0:8000
```

## Documentação versionada (mike + GitHub Pages)

O site é **versionado com [mike](https://github.com/jimporter/mike)**: cada release publica a sua
própria versão navegável na branch `gh-pages`, e o leitor alterna entre versões por um **dropdown**
no cabeçalho. O alias `latest` sempre aponta para a release mais recente, então a URL raiz do site
cai na versão mais nova.

**Como cada peça se encaixa:**

- **Build-check (CI):** o workflow `Docs - Build Check` roda `mkdocs build --strict` a cada push e
  PR — sem publicar. É só a garantia de que a doc sempre compila; um release nunca descobre uma
  árvore de docs quebrada na hora de publicar.
- **Deploy (CI):** o job `Deploy Versioned Docs (mike)` do `Release to PyPI` roda **depois** do
  publish no PyPI (só documenta versão que efetivamente subiu): `mike deploy --push X.Y latest` +
  `mike set-default --push latest`, empurrando para `gh-pages` com o `GITHUB_TOKEN` embutido
  (`contents: write`) — sem token externo. A granularidade é **minor** (`X.Y`): um patch herda o
  slot da sua minor em vez de multiplicar entradas. Prereleases (`rc1`, `b1`, …) **não** movem
  `latest` (o job é pulado para elas).

**Configuração do mantenedor — uma única vez, com admin no repositório:** apontar o GitHub Pages
para a branch `gh-pages` (o modelo mike), em vez da fonte *GitHub Actions*. O workflow **não** faz
isso: o `GITHUB_TOKEN` é um token de GitHub App que não altera as configurações do Pages.

```bash
make enable_pages          # ou: bash tasks.sh enable_pages
```

Já roda dentro de `make init` / `bash tasks.sh init`. É **idempotente e não-bloqueante**, e — para
**nunca** deixar o site em 404 — só troca a fonte para `gh-pages` **depois** que essa branch existir
(o primeiro `mike deploy` do release a cria). Se rodar antes disso, ele avisa e não mexe no Pages;
basta rodar `make enable_pages` de novo após o primeiro release. Alternativa manual:
*Settings → Pages → Build and deployment → Source: Deploy from a branch → `gh-pages` / `(root)`*.

**Semear a versão atual imediatamente (opcional):** se quiser publicar a versão já lançada sem
esperar o próximo release, rode uma vez, com a branch limpa:

```bash
git config user.name "<você>" && git config user.email "<seu-email>"
poetry run mike deploy --push --update-aliases 0.18 latest
poetry run mike set-default --push latest
make enable_pages          # agora que gh-pages existe, aponta o Pages para ela
```

## Verificando o pacote construído

Antes de abrir um PR de release, confirme que a wheel realmente constrói e importa — isso pega
erros de empacotamento (um `__init__` faltando, um subpacote `_internal/` não incluído) que os
testes na árvore de fontes nunca revelam:

```bash
make install_dist_locally    # python -m build → instala → smoke-import → reporta a wheel
```

## Pull requests

1. Crie a branch a partir da branch padrão seguindo a política de prefixo (`feat/…`, `fix/…`, …).
2. Preencha o template de PR por completo.
3. Garanta que os checks de CI (testes, lint, build da documentação) passem — eles são o gate de
   merge.

### O ruleset `pr-quality-gate` (revisão automática e proteção da branch)

A branch padrão é protegida por um **branch ruleset** chamado `pr-quality-gate`, provisionado
**inteiramente por código** — nenhuma caixinha marcada à mão:

```bash
make enable_repo_rules     # ou: bash tasks.sh enable_repo_rules
```

Já roda dentro de `make init` / `bash tasks.sh init`. É **idempotente** (um ruleset existente é
atualizado no lugar, não duplicado) e **não-bloqueante** (sem `gh`, sem auth ou sem permissão de
admin, ele avisa e sai com 0 — o `init` completa). Exige `gh` autenticado com direitos de admin no
repositório: o `GITHUB_TOKEN` do CI **não** consegue escrever rulesets, por isso isto é um passo do
mantenedor, não um job de workflow.

O que o ruleset aplica:

| Regra | Efeito |
|---|---|
| `pull_request` | Toda mudança passa por PR. **0 aprovações exigidas** — o GitHub não deixa o autor aprovar o próprio PR, então exigir ≥1 travaria um mantenedor solo. As conversas precisam estar resolvidas (`required_review_thread_resolution`), o que torna os comentários do Copilot **vinculantes**. |
| `required_status_checks` | Os testes (`Run Automated Tests`, nos 3 SOs) e o `build` da documentação **bloqueiam** o merge de fato. |
| `code_scanning` | CodeQL: alertas de segurança `high_or_higher` e alertas de erro bloqueiam o merge. |
| `copilot_code_review` | **Revisão automática do Copilot** em todo PR, revisando cada novo push (`review_on_push`). Grátis em repositórios públicos. |
| `non_fast_forward` + `deletion` | Sem force-push e sem deletar a branch padrão. |

**Automático × manual — a fronteira é *repositório* × *conta*.** Tudo que é **configuração do
repositório** é gravável pela REST API e já vem no script — inclusive a revisão do Copilot, que é um
**rule type próprio** (`copilot_code_review`), e **não** um parâmetro de `pull_request` (essa grafia
devolve HTTP 422, o que faz a regra *parecer* exclusiva da UI). **Nenhuma caixinha precisa ser
marcada à mão.** O outro pré-requisito de repositório — habilitar o CodeQL (*default setup*), sem o
qual a regra `code_scanning` não tem ferramenta para checar — também é API:

```bash
gh api -X PATCH repos/:owner/:repo/code-scanning/default-setup -f state=configured
```

O que **não** dá para automatizar daqui é o **direito de uso na conta**, não no repositório: a regra
`copilot_code_review` só dispara "*se o autor tiver acesso ao Copilot code review*" — e o **code
review não está incluído no Copilot Free** (a própria tela de planos lista "*AI reviews*" como
recurso de upgrade). Sem um plano que o inclua (Pro / Pro+ / Business), a regra fica **configurada e
correta, porém inerte: nenhuma revisão aparece e nada dá erro** — o silêncio é a armadilha.

Como obter revisão automática de fato:

- **Copilot Pro gratuito** — é gratuito para estudantes, professores e mantenedores de projetos
  open-source populares (verificação em [github.com/settings/billing](https://github.com/settings/billing)).
- **Sem plano nenhum** — um workflow de `pull_request` chamando um LLM de tier gratuito (ex.: Gemini
  Flash) para comentar o PR. Independe do Copilot.

> **Regra geral:** configuração de **repositório** → script (é o que este helper faz, 100%). Direito
> de uso de **conta** → depende do plano, e não se resolve do repositório. As demais regras do gate
> (PR obrigatório, CI verde, CodeQL limpo) funcionam **independentemente** do Copilot.

### O painel de Quality Gate e o auto-merge

Todo PR recebe, automaticamente (workflow `pr-gate.yaml` → `bin/pr_gate.py`):

- **Rótulos**: `risk:*` (classe de risco pelos caminhos alterados), `size:*` (XS…XL, pelo volume do
  diff) e `gate:passing` / `gate:pending` / `gate:failing` — **`pending` não é `failing`**: um check
  ainda rodando não diz nada sobre o resultado.
- **Um comentário fixo** (atualizado no lugar, nunca empilhado) com a tabela por eixo — testes nos 3
  SOs, build da documentação, CodeQL.

> **Idioma.** O bot escreve em **inglês**, como todo o resto voltado a quem contribui (código,
> mensagens de commit, saída de CI). Só a **documentação publicada** segue o idioma do site
> (`mkdocs.yml` → `theme.language`, pt-BR). A fronteira é o **público**, não o repositório.

**Auto-merge — por caminho, nunca por tamanho.** Um diff pequeno **não** é um diff seguro aqui: a
falha real desta biblioteca é semântica (uma coluna de `FileContract` aterrada errado, um `date_ref`
pegando a partição errada). Uma mudança de **um caractere** em `_internal/config/contracts/` é
minúscula e catastrófica — e **todos os testes passam**, porque os testes afirmam o contrato que foi
escrito. Por isso a classificação é por **caminho**:

| Classe | Caminhos | Auto-merge? |
|---|---|---|
| `docs` | `docs/**`, `*.md`, `mkdocs.yml` | ✅ |
| `ci` | `.github/**`, `bin/**`, `Makefile`, `tasks.sh`, configs de lint | ✅ |
| `deps` | `poetry.lock`, `pyproject.toml` | ✅ (os testes são o gate) |
| `tests` | `tests/**` | ❌ — definem o que "passar" significa |
| `src` | `src/filings_cvm/**` | ❌ **nunca**, em nenhum tamanho |
| `other` | qualquer outro | ❌ (desconhecido = inseguro) |

Numa classe auto-fundível, o auto-merge é **opt-out**: a classificação **é** o consentimento, então
nenhum rótulo é preciso para armá-lo — as bumps semanais do Dependabot fundem sozinhas. O rótulo
`do-not-merge` é a válvula de escape que segura um PR específico.

Um diff `XL` também não funde — **exceto quando o único arquivo alterado é o `poetry.lock`**. O veto
por tamanho pergunta "esse diff é grande o bastante para um humano olhar?"; num lockfile regenerado
a pergunta não significa nada, porque o tamanho acompanha quantos *hashes* de dependência se
moveram, não quanto risco chegou — uma bump de 3 ferramentas de dev deu 579 linhas (`XL`, vetada)
enquanto uma de 2 pacotes deu menos de 500 (`L`, fundida). O `pyproject.toml` **não** entra na
exceção: é lá, num range editado à mão, que o risco de dependência de fato mora.

E ele **não burla nada**: usa o **auto-merge nativo** do GitHub, que segura o merge até *todos* os
checks obrigatórios do ruleset ficarem verdes. O script decide apenas *elegibilidade*; quem decide
*se passou* continua sendo o ruleset. (Auto-**aprovação** seria inútil aqui: o ruleset exige **0**
aprovações, então uma aprovação de bot não destravaria nada.)

Duas regras da UI ficam **deliberadamente desligadas**, para não criar uma segunda fonte de verdade:
*Require code quality results* (severidade subjetiva de IA no caminho do merge — `ruff`, `mypy` e os
gates de `bin/check_*.py` já cobrem qualidade de forma determinística) e *Restrict code coverage* (o
piso já é single-source em `.coveragerc`, aplicado por pre-commit + CI).

## Lançando

Os releases são **dirigidos por tag** quando o projeto está conectado a um remoto no GitHub:

- A versão é a **tag git** (via `poetry-dynamic-versioning`); o `pyproject.toml` guarda um
  placeholder `0.0.0`. Não edite à mão. Dispare um release pela aba Actions
  (`Release to PyPI` / `Release to Test PyPI`, `workflow_dispatch` com a versão) ou empurrando uma
  tag `vX.Y.Z`.
- O workflow de release roda a **suíte completa de testes** como gate rígido, constrói com
  `python -m build` e publica via **trusted publishing (OIDC)** (`pypa/gh-action-pypi-publish`) —
  sem `PYPI_TOKEN` armazenado.
- O changelog é regenerado a partir das tags no momento do build (`make changelog` localmente); a
  CI nunca faz commit de `CHANGELOG.md` de volta na branch padrão protegida.

### Configuração do mantenedor — trusted publisher (uma vez, antes do primeiro release)

Registre um **trusted publisher** tanto em [pypi.org](https://pypi.org) quanto em
[test.pypi.org](https://test.pypi.org). Cada claim precisa bater exatamente com o workflow, ou o
upload falha com um `invalid-publisher` opaco:

| Claim | Valor |
|-------|-------|
| Owner / repository | seu `<owner>` / `<repo>` no GitHub |
| Workflow filename | `release-pypi.yaml` (PyPI) / `release-test-pypi.yaml` (Test PyPI) |
| Environment | `release-pypi` / `release-test-pypi` |
| PyPI **Project Name** | deve ser igual ao nome de distribuição (`name` no `pyproject.toml`) |

Para o primeiro upload o projeto ainda não existe — registre um **pending publisher** no nível da
conta (não dentro das configurações de um projeto existente). Publicar de um laptop em vez da CI é
o único caso que ainda precisa de um API token; OIDC só funciona a partir do GitHub Actions.
