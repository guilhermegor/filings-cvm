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
