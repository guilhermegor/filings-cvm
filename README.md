# filings-cvm <img src="assets/cvm-logo.png" align="right" width="200" style="border-radius: 15px;" alt="filings-cvm">

[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![PyPI Version](https://img.shields.io/pypi/v/filings-cvm)
![PyPI Downloads](https://static.pepy.tech/badge/filings-cvm)
[![Linting](https://img.shields.io/badge/linting-ruff_|_codespell-blue)](https://github.com/astral-sh/ruff)
![Test Coverage](./coverage.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue)](https://guilhermegor.github.io/filings-cvm/)

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

## 📖 Documentação

A documentação completa (em pt-BR) fica em **<https://guilhermegor.github.io/filings-cvm/>**
ou pode ser servida localmente:

```bash
make docs_server     # serve em http://0.0.0.0:8000  (sem make: ./tasks.sh docs_server)
```

## ✨ Funcionalidades

Toda solução vive em uma de duas macrosseções:

| Seção | Sentido | O que faz |
|-------|---------|-----------|
| `filings_cvm.submission` | **envio** → CVM | Recebe modelos de schema validados e produz o arquivo XML compatível com a CVM, pronto para envio. |
| `filings_cvm.ingestion` | **leitura** ← CVM | Analisa um arquivo baixado da CVM de volta para modelos tipados. Criada quando o primeiro padrão de leitura for implementado. |

O **schema compartilhado** (modelos Pydantic que espelham cada padrão XML) é neutro em
relação à direção e reexportado pelas seções públicas — você importa tudo de que precisa a
partir de `filings_cvm.submission`.

### 🧩 Padrões implementados (envio)

- ✅ **Perfil Mensal — V4** ([`PadraoXMLPerfilV4.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfilV4.asp)) — `PerfilMensal` / `PerfilMensalDocument`
- ✅ **Informe Diário — V4** ([`PadraoXMLInfoDiarioNetV4.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiarioNetV4.asp)) — `InformeDiario` / `InformeDiarioDocument`

Os demais padrões do catálogo (CDA, Lâmina, Informe Mensal FIDC, etc.) estão pendentes —
consulte o `CLAUDE.md` do repositório para o catálogo completo com o status de cada um.

## 🚀 Primeiros Passos

### Pré-requisitos

- Python **>= 3.10**
- Poetry (recomendado)
- Opcional: Makefile (ou use `./tasks.sh` no Git Bash / Windows)

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

xml = PerfilMensal().to_xml(doc)                          # XML como str
PerfilMensal().to_xml(doc, output_path="perfil.xml")     # ou grava em disco (windows-1252)
```

O exemplo completo (incluindo o bloco obrigatório de contagem de clientes) está em
**[Uso](https://guilhermegor.github.io/filings-cvm/usage/)**.

### Execução dos testes

```bash
make unit_tests      # pytest tests/unit/
make test_cov        # cobertura + badge (coverage.svg)
make lint            # ruff, codespell, pydocstyle, check_docstrings
make help            # lista todos os comandos disponíveis
```

## 📂 Estrutura do projeto

```
filings-cvm/
├── assets/                 # logo e imagens do projeto
├── docs/                   # documentação MkDocs (pt-BR) — make docs_server
├── mkdocs.yml              # configuração do site de documentação
├── src/filings_cvm/
│   ├── __init__.py         # API pública (controlada por __all__)
│   ├── submission/         # envio → CVM (modelo validado → XML)
│   ├── ingestion/          # leitura ← CVM (criada quando o 1º padrão landar)
│   └── _internal/          # PRIVADO — schemas Pydantic + helpers vendorizados
├── tests/
│   ├── unit/  integration/  performance/
├── .pre-commit-config.yaml
├── Makefile  /  tasks.sh   # interfaces espelhadas (com e sem make)
├── pyproject.toml
└── README.md
```

## 🤝 Contribuição

Contribuições são bem-vindas — leia o
[docs/contributing.md](docs/contributing.md) antes de abrir sua primeira branch. Fluxo
resumido:

```bash
make lint            # ruff, codespell, pydocstyle
make unit_tests      # pytest tests/unit/
```

## 👨‍💻 Autores

**Guilherme Rodrigues**

[![GitHub](https://img.shields.io/badge/GitHub-guilhermegor-181717?style=flat&logo=github)](https://github.com/guilhermegor)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Guilherme_Rodrigues-0077B5?style=flat&logo=linkedin)](https://www.linkedin.com/in/guilhermegor/)

## 📜 Licença

Este projeto é licenciado sob a Licença **MIT** — veja [LICENSE](LICENSE).

## 🙌 Agradecimentos

- Gerado a partir do template **lib-minimal** via [BlueprintX](https://github.com/guilhermegor/BlueprintX).
