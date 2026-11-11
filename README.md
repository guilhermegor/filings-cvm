<!-- readme-archetype: library -->
# opendata-cvm

<p align="center"><img src="https://raw.githubusercontent.com/guilhermegor/opendata-cvm/main/assets/cvm-logo.png" width="200" alt="Emblema da CVM"></p>

[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)
[![PyPI Version](https://img.shields.io/pypi/v/opendata-cvm)](https://pypi.org/project/opendata-cvm/)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue)](https://guilhermegor.github.io/opendata-cvm/)
[![Linting](https://img.shields.io/badge/linting-ruff_%7C_codespell-blue)](https://github.com/astral-sh/ruff)
[![Type-checked: mypy](https://img.shields.io/badge/type--checked-mypy-blue)](https://mypy-lang.org/)
![Test Coverage](https://raw.githubusercontent.com/guilhermegor/opendata-cvm/main/coverage.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Open Issues](https://img.shields.io/github/issues/guilhermegor/opendata-cvm)
![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-darkgreen.svg)
![PyPI Downloads](https://static.pepy.tech/badge/opendata-cvm)

<!-- slug: overview -->
## Visão geral

Biblioteca Python **tipada** para ler os arquivos abertos da
[CVM](https://www.gov.br/cvm) (Comissão de Valores Mobiliários): baixa o dump publicado em
<https://dados.cvm.gov.br/dados/> e devolve um `DataFrame` tipado e validado por contrato.

Valores decimais seguem a regra do projeto: nada de `float` onde a precisão importa. Colunas
numéricas voltam como **texto exato da fonte**, sem truncar nem arredondar — a escala e o
`Decimal` ficam a cargo de quem consome.

> **Migração:** a seção de **envio** (`opendata_cvm.submission`, modelo validado → XML) foi
> removida e vive no pacote separado `layouts-cvm` (`from layouts_cvm import PerfilMensal`). Esta biblioteca não depende dele.

> **Fonte da verdade:** nomes de coluna e tipos vêm dos arquivos reais publicados no portal de
> dados abertos da CVM — <https://dados.cvm.gov.br/dados/> — não desta documentação.

<!-- slug: features -->
## Funcionalidades

Toda solução vive em `opendata_cvm.ingestion` (**leitura** ← CVM): analisa um arquivo baixado
da CVM de volta para modelos tipados, agrupado por raiz do portal (ex.: `opendata_cvm.ingestion.fi`).

Para **gerar** os arquivos XML de envio → CVM, use o pacote separado `layouts-cvm`.

<!-- slug: documentation -->
## Documentação

A documentação completa (em pt-BR) fica em **<https://guilhermegor.github.io/opendata-cvm/>**
ou pode ser servida localmente:

```bash
make docs_server     # serve em http://0.0.0.0:8000  (sem make: ./tasks.sh docs_server)
```

<!-- slug: getting-started -->
## Primeiros Passos

### Pré-requisitos

- Python **>= 3.11**
- Poetry (recomendado)
- Opcional: Makefile (ou use `./tasks.sh` no Git Bash / Windows)

<!-- slug: install -->
### Instalação

**Como dependência:**

```bash
pip install opendata-cvm
# ou
poetry add opendata-cvm
```

**A partir do código-fonte:**

```bash
git clone https://github.com/guilhermegor/opendata-cvm.git
cd opendata-cvm
make init            # cria a .venv e instala os hooks de pre-commit
                     # (sem make: ./tasks.sh init)
```

<!-- slug: usage -->
### Uso básico

A leitura (← CVM) devolve um `DataFrame` tipado e validado por contrato:

```python
from datetime import date

from opendata_cvm.ingestion.fi import InformeDiarioReader

df = InformeDiarioReader(date_ref=date(2025, 1, 15)).read()   # dump mensal inf_diario_fi
```

O exemplo completo (incluindo o bloco obrigatório de contagem de clientes) está em
**[Uso](https://guilhermegor.github.io/opendata-cvm/usage/)**.

<!-- slug: project-structure -->
## Estrutura do projeto

```text
opendata-cvm/
├── assets/                 # logo e imagens do projeto
├── bin/                    # scripts de gate e utilitários (inclui check_readme_structure.sh)
├── docs/                   # documentação MkDocs (pt-BR) — make docs_server
├── mkdocs.yml              # configuração do site de documentação
├── src/opendata_cvm/
│   ├── __init__.py         # API pública (controlada por __all__)
│   ├── ingestion/          # leitura ← CVM (arquivo baixado → DataFrame tipado)
│   └── _internal/          # PRIVADO — contratos, ports (interfaces) + helpers
├── tests/
│   ├── unit/  integration/  performance/
├── .pre-commit-config.yaml
├── Makefile  /  tasks.sh   # interfaces espelhadas (com e sem make)
├── pyproject.toml
└── README.md
```

<!-- slug: development -->
## Desenvolvimento

```bash
make unit_tests      # pytest tests/unit/
make test_cov        # cobertura + badge (coverage.svg)
make lint            # ruff, codespell, pydocstyle, check_docstrings
make help            # lista todos os comandos disponíveis
```

O `README.md` em si é validado por `bin/check_readme_structure.sh` (hook `readme-structure`
no pre-commit e passo equivalente no CI): títulos sem emoji, marcadores `<!-- slug: ... -->`
nas seções obrigatórias e lista de autores com links do GitHub e do LinkedIn.

<!-- slug: public-api -->
## API pública

A seção `ingestion` é dona dos seus nomes; o `opendata_cvm.__all__` de topo guarda apenas o que não
pertence a nenhuma delas. Tudo sob `_internal/` é privado.

| O quê | Importe de |
|-------|------------|
| Um reader de ingestão | `opendata_cvm.ingestion.<raiz_do_portal>` (ex.: `opendata_cvm.ingestion.fi`) |
| `RetryPolicy`, `__version__` | `opendata_cvm` |

<!-- slug: publishing -->
## Publicação

As versões saem pelos workflows `release-test-pypi.yaml` (ensaio no Test PyPI) e
`release-pypi.yaml` (PyPI + GitHub Release) em `.github/workflows/`; a tag git é a versão.

O caminho do 0.x ao 1.0.0, e o portão de release que o protege, está em
[docs/releasing-1-0-0.md](docs/releasing-1-0-0.md).

<!-- slug: contributing -->
## Contribuição

Contribuições são bem-vindas — leia o
[docs/contributing.md](docs/contributing.md) antes de abrir sua primeira branch. Fluxo
resumido:

```bash
make lint            # ruff, codespell, pydocstyle
make unit_tests      # pytest tests/unit/
```

Toda mudança entra por **pull request**: a branch padrão é protegida pelo ruleset
`pr-quality-gate` (PR obrigatório, testes nos 3 SOs + build da doc verdes, CodeQL limpo e
**revisão automática do Copilot** a cada push). Ele é provisionado por código — `make init` já o
aplica, e `make enable_repo_rules` o (re)aplica sozinho; nenhuma configuração manual na UI do
GitHub é necessária. Detalhes em
[docs/contributing.md](docs/contributing.md#o-ruleset-pr-quality-gate-revisão-automática-e-proteção-da-branch).

<!-- slug: license -->
## Licença

Este projeto é licenciado sob a Licença **MIT** — veja [LICENSE](LICENSE).

<!-- slug: authors -->
## Autores

- Guilherme Rodrigues — [GitHub](https://github.com/guilhermegor) | [LinkedIn](https://www.linkedin.com/in/guilhermegor/)

<!-- slug: useful-links -->
## Links úteis

- [Documentação](https://guilhermegor.github.io/opendata-cvm/)
- [PyPI](https://pypi.org/project/opendata-cvm/)
- [Repositório no GitHub](https://github.com/guilhermegor/opendata-cvm)
- [Issues](https://github.com/guilhermegor/opendata-cvm/issues)

---

<sub>Agradecimentos: gerado a partir do template **lib-minimal** via
[BlueprintX](https://github.com/guilhermegor/BlueprintX). Biblioteca não oficial,
mantida pela comunidade: sem afiliação ou endosso da CVM; o emblema é do regulador.</sub>
