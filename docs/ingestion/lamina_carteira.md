# **Lâmina carteira FIF — leitura**

Leitura (← CVM) do membro `lamina_fi_carteira_AAAAMM.csv` do dump mensal da **Lâmina**
(`lamina_fi_AAAAMM.zip`), publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/FI/DOC/LAMINA/DADOS/).

> **Veja também:** [Referência da API](../api.md) para cada símbolo público · [Uso](../usage.md)
> para instalação e o conceito geral.

---

## Descrição

`LaminaCarteiraReader` baixa o ZIP mensal, extrai **todos** os membros, lê o de `carteira`, valida
o **contrato** (colunas obrigatórias + coluna de CNPJ coercível), aplica os **tipos declarados** —
nunca a inferência do pandas — e devolve a alocação de cada fundo **por tipo de ativo**, como
percentual do patrimônio líquido.

### Três leitores de carteira, três granularidades

Três artefatos da CVM descrevem a carteira de um fundo. São leitores distintos porque são
**arquivos distintos**, não três visões de um só:

| Leitor | Artefato | Granularidade |
|--------|----------|---------------|
| [`CdaReader`](cda.md) | `cda_fi_AAAAMM.zip` | fundo × data × **ativo** — uma linha por título, com valor de mercado. |
| **`LaminaCarteiraReader`** | `lamina_fi_carteira_AAAAMM.csv` | fundo × **tipo de ativo** — apenas `PR_PL_ATIVO`, o percentual do PL. |
| `lamina_fi_AAAAMM.csv` | mesmo ZIP | A lâmina propriamente dita — leitor próprio. |

### `PR_PL_ATIVO` **não** soma 100

O percentual é **sinalizado** e os totais por fundo **não** somam 100: um fundo pode ter exposição
vendida ou alavancada. Em 2025-04 o total por fundo variou de **-37,08** a **1123,00** (mediana
100,03). Por isso o leitor **não** impõe nenhuma invariante de "soma 100%" — ela rejeitaria fundos
alavancados perfeitamente válidos.

| Coluna | Tipo | Observação |
|--------|------|-----------|
| `TP_FUNDO_CLASSE`, `CNPJ_FUNDO_CLASSE`, `DENOM_SOCIAL` | `str` | `CNPJ_FUNDO_CLASSE` vem mascarado e deve ter ao menos um CNPJ válido. |
| `ID_SUBCLASSE` | `str` | Exigido como coluna; **vazio** em todas as linhas até hoje. É a costura pela qual a CVM identificará subclasses. |
| `DT_COMPTC` | `date` | Data de competência (uma única por arquivo). |
| `TP_ATIVO` | `str` | O tipo de ativo — a granularidade da linha. |
| `PR_PL_ATIVO` | `str` | Percentual **sinalizado** do PL, texto exato da CVM — **nunca `float`**. |

---

## Exemplos

### Ler o mês de referência

```python
from datetime import date

from filings_cvm.ingestion import LaminaCarteiraReader

# Qualquer dia do mês seleciona o dump; o padrão é hoje. Prefira um mês passado
# para dados completos — o mês corrente pode ainda não estar publicado.
df = LaminaCarteiraReader(date_ref=date(2025, 4, 15)).read()

print(df["TP_ATIVO"].value_counts())
```

### Somar a alocação de um fundo

```python
from decimal import Decimal

# O percentual vem como texto exato; converta no ponto em que for calcular.
df["PCT"] = df["PR_PL_ATIVO"].map(Decimal)

total = df.groupby("CNPJ_FUNDO_CLASSE")["PCT"].sum()
# Não espere 100: alavancagem e posições vendidas afastam o total dos 100%.
```

### Persistir o artefato bruto (camada *bronze*)

Sem `path_raw` o ZIP é baixado num diretório temporário e descartado. Informando um caminho, o
artefato **bruto e intacto** é gravado ali e **mantido**, antes de qualquer parsing — e não apenas
o membro lido: **todos** os CSVs do ZIP, para que um leitor posterior (o da lâmina) reproduza os
mesmos bytes em vez de rebaixar uma fonte que já pode ter mudado.

```python
from pathlib import Path

df = LaminaCarteiraReader(
    date_ref=date(2025, 4, 15),
    path_raw=Path("/data/bronze/cvm/lamina/202504"),
).read()
```

### Timeout

```python
df = LaminaCarteiraReader(date_ref=date(2025, 4, 15)).read(int_timeout_s=60)
```

O `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou
`ValueError` (o ZIP não contém o membro `lamina_fi_carteira_*`) — falha cedo, sem devolver dados
corrompidos.
