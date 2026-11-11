# **Uso**

Como instalar a biblioteca e ler o seu primeiro arquivo da CVM.

> **Veja também:** [Referência da API](api/reference.md) · [Leitura](ingestion/index.md)

---

## Instalação

```bash
pip install opendata-cvm
```

Ou com Poetry:

```bash
poetry add opendata-cvm
```

Requer **Python >= 3.11**.

---

## Envio (→ CVM)

A geração de XML de envio saiu desta biblioteca e vive no pacote separado `layouts-cvm`.

---

## Leitura (← CVM)

O fluxo de leitura (`ingestion`) faz o caminho inverso: baixa um arquivo publicado pela CVM e o
devolve como um `DataFrame` **tipado e validado por contrato**. O primeiro leitor cobre o dump
mensal de *open-data* do Informe Diário de fundos (`inf_diario_fi_AAAAMM`):

```python
from datetime import date

from filings_cvm.ingestion.fi import InformeDiarioReader

# Qualquer dia do mês de referência seleciona o dump mensal; o padrão é hoje.
df_ = InformeDiarioReader(date_ref=date(2025, 1, 15)).read()
```

O leitor baixa, descompacta e faz o parse em um diretório temporário, valida o
[contrato](api/reference.md) (colunas obrigatórias + coluna de CNPJ coercível) e aplica os tipos
declarados. As colunas monetárias são mantidas como **texto exato** (o que a CVM publicou),
nunca `float` — converta para `Decimal` no ponto em que for calcular.

---

## Rodando os testes

```bash
make unit_tests         # apenas testes unitários
make integration_tests  # apenas testes de integração
make test_cov           # testes unitários + relatório de cobertura + badge
```

---

## Lint e formatação

```bash
make lint          # ruff check + ruff format + codespell + pydocstyle
```

---

## Publicando no PyPI

Dois workflows do GitHub Actions cuidam dos lançamentos (presentes quando o repositório tem um
remoto no GitHub):

- **`release-test-pypi.yaml`** — publica primeiro no [Test PyPI](https://test.pypi.org).
- **`release-pypi.yaml`** — publica no [PyPI](https://pypi.org) e cria um release no GitHub.

Ambos são disparados pela aba **Actions** (`workflow_dispatch`) com a versão a lançar, verificam
que a nova versão é maior que a última publicada e constroem com Poetry. Detalhes de configuração
em [Contribuindo](contributing.md).
