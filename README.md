<!-- readme-archetype: library -->
# filings-cvm

<p align="center"><img src="https://raw.githubusercontent.com/guilhermegor/filings-cvm/main/assets/cvm-logo.png" width="200" alt="Emblema da CVM"></p>

[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)
[![PyPI Version](https://img.shields.io/pypi/v/filings-cvm)](https://pypi.org/project/filings-cvm/)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue)](https://guilhermegor.github.io/filings-cvm/)
[![Linting](https://img.shields.io/badge/linting-ruff_%7C_codespell-blue)](https://github.com/astral-sh/ruff)
[![Type-checked: mypy](https://img.shields.io/badge/type--checked-mypy-blue)](https://mypy-lang.org/)
![Test Coverage](https://raw.githubusercontent.com/guilhermegor/filings-cvm/main/coverage.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Open Issues](https://img.shields.io/github/issues/guilhermegor/filings-cvm)
![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-darkgreen.svg)
![PyPI Downloads](https://static.pepy.tech/badge/filings-cvm)

<!-- slug: overview -->
## Visão geral

Biblioteca Python **tipada** para os padrões de arquivo XML regulatórios da
[CVM](https://www.gov.br/cvm) (Comissão de Valores Mobiliários). Monte, valide e
serialize documentos no formato exigido pela CVM — e, à medida que a biblioteca cresce,
leia arquivos baixados da CVM de volta para modelos tipados.

Modelos [Pydantic v2](https://docs.pydantic.dev/) validam **tudo** na construção — formato
de datas, dígitos verificadores de CNPJ/CPF e a **escala decimal** de cada campo — e valores
com casas decimais em excesso são **truncados em direção a zero** (`ROUND_DOWN`), nunca
arredondados, para que um valor reportado jamais seja inflado.

> **Fonte da verdade:** nomes de campo, escalas decimais e cardinalidades vêm do catálogo
> oficial da CVM — <https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadroesXML.asp> —
> não desta documentação.

<!-- slug: features -->
## Funcionalidades

Toda solução vive em uma de duas macrosseções:

| Seção | Sentido | O que faz |
|-------|---------|-----------|
| `filings_cvm.submission` | **envio** → CVM | Recebe modelos de schema validados e produz o arquivo XML compatível com a CVM, pronto para envio. |
| `filings_cvm.ingestion` | **leitura** ← CVM | Analisa um arquivo baixado da CVM de volta para modelos tipados. Criada quando o primeiro padrão de leitura for implementado. |

O **schema compartilhado** (modelos Pydantic que espelham cada padrão XML) é neutro em
relação à direção e reexportado pelas seções públicas — você importa tudo de que precisa a
partir de `filings_cvm.submission`.

### Padrões implementados (envio)

- ✅ **Perfil Mensal — V4** ([`PadraoXMLPerfilV4.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfilV4.asp)) — `PerfilMensal` / `PerfilMensalDocument`
- ✅ **Perfil Mensal — ICVM 739** ([`PadraoXMLPerfil739.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfil739.asp)) — `PerfilMensal739` / `PerfilMensal739Document`
- ✅ **Informe Diário — V4** ([`PadraoXMLInfoDiarioNetV4.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiarioNetV4.asp)) — `InformeDiario` / `InformeDiarioDocument`
- ✅ **Atualização do Cadastro de Ativos** ([`PadraoXMLAtivos.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLAtivos.asp)) — `CadastroAtivos` / `CadastroAtivosDocument`

Os demais padrões do catálogo (CDA, Lâmina, Informe Mensal FIDC, etc.) estão pendentes —
consulte o `CLAUDE.md` do repositório para o catálogo completo com o status de cada um.

<!-- slug: documentation -->
## Documentação

A documentação completa (em pt-BR) fica em **<https://guilhermegor.github.io/filings-cvm/>**
ou pode ser servida localmente:

```bash
make docs_server     # serve em http://0.0.0.0:8000  (sem make: ./tasks.sh docs_server)
```

<!-- slug: getting-started -->
## Primeiros Passos

### Pré-requisitos

- Python **>= 3.10**
- Poetry (recomendado)
- Opcional: Makefile (ou use `./tasks.sh` no Git Bash / Windows)

<!-- slug: install -->
### Instalação

**Como dependência:**

```bash
pip install filings-cvm
# ou
poetry add filings-cvm
```

**A partir do código-fonte:**

```bash
git clone https://github.com/guilhermegor/filings-cvm.git
cd filings-cvm
make init            # cria a .venv e instala os hooks de pre-commit
                     # (sem make: ./tasks.sh init)
```

<!-- slug: usage -->
### Uso básico

```python
from filings_cvm.submission import (
    DocumentHeader,
    PerfilMensal,
    PerfilMensalDocument,
    PerfilMensalRow,
)

header = DocumentHeader(dt_compt="01/2025", dt_gerac_arq="15/01/2025")
row = PerfilMensalRow(cnpj_fdo="11222333000181", ...)  # validado na construção
doc = PerfilMensalDocument(header=header, rows=[row])

xml = PerfilMensal().export(doc)                          # XML como str
PerfilMensal().export(doc, output_path="perfil.xml")     # ou grava em disco (windows-1252)
```

E a leitura (← CVM) devolve um `DataFrame` tipado e validado por contrato:

```python
from datetime import date

from filings_cvm.ingestion.fi import InformeDiarioReader

df = InformeDiarioReader(date_ref=date(2025, 1, 15)).read()   # dump mensal inf_diario_fi
```

O exemplo completo (incluindo o bloco obrigatório de contagem de clientes) está em
**[Uso](https://guilhermegor.github.io/filings-cvm/usage/)**.

<!-- slug: project-structure -->
## Estrutura do projeto

```text
filings-cvm/
├── assets/                 # logo e imagens do projeto
├── bin/                    # scripts de gate e utilitários (inclui check_readme_structure.sh)
├── docs/                   # documentação MkDocs (pt-BR) — make docs_server
├── mkdocs.yml              # configuração do site de documentação
├── src/filings_cvm/
│   ├── __init__.py         # API pública (controlada por __all__)
│   ├── submission/         # envio → CVM (modelo validado → XML)
│   ├── ingestion/          # leitura ← CVM (arquivo baixado → DataFrame tipado)
│   └── _internal/          # PRIVADO — schemas Pydantic, ports (interfaces) + helpers
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

Cada seção é dona dos seus nomes; o `filings_cvm.__all__` de topo guarda apenas o que não
pertence a nenhuma delas. Tudo sob `_internal/` é privado.

| O quê | Importe de |
|-------|------------|
| Um reader de ingestão | `filings_cvm.ingestion.<raiz_do_portal>` (ex.: `filings_cvm.ingestion.fi`) |
| Um writer de envio | `filings_cvm.submission` |
| `RetryPolicy`, `__version__` | `filings_cvm` |

<!-- slug: publishing -->
## Publicação

As versões saem pelos workflows `release-test-pypi.yaml` (ensaio no Test PyPI) e
`release-pypi.yaml` (PyPI + GitHub Release) em `.github/workflows/`; a tag git é a versão.

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

- [Documentação](https://guilhermegor.github.io/filings-cvm/)
- [PyPI](https://pypi.org/project/filings-cvm/)
- [Repositório no GitHub](https://github.com/guilhermegor/filings-cvm)
- [Issues](https://github.com/guilhermegor/filings-cvm/issues)

---

<sub>Agradecimentos: gerado a partir do template **lib-minimal** via
[BlueprintX](https://github.com/guilhermegor/BlueprintX). Biblioteca não oficial,
mantida pela comunidade: sem afiliação ou endosso da CVM; o emblema é do regulador.</sub>
