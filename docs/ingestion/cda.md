# **CDA FIF — leitura**

Leitura (← CVM) do dump mensal de *open-data* do **Demonstrativo de Composição e Diversificação
das Aplicações** (`cda_fi_AAAAMM`), publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/FI/DOC/CDA/DADOS/).

> **Veja também:** [Referência da API](../api.md) para cada símbolo público · [Uso](../usage.md)
> para instalação e o conceito geral.

---

## Descrição

`CdaReader` baixa o ZIP mensal, lê **todos os blocos de ativos** (`BLC_1`…`BLC_8`), valida o
**contrato** de cada um (colunas obrigatórias + coluna de CNPJ coercível), aplica os **tipos
declarados** — nunca a inferência do pandas — e consolida tudo em um único `DataFrame`.

> **Nota:** este leitor consome o CSV de *open-data* — um artefato **distinto** do XML do padrão
> CDA V4 de envio. Por isso tem o seu próprio contrato de colunas.

### Duas granularidades, um único `DataFrame`

O arquivo traz membros em **granularidades diferentes**:

| Membro | Granularidade | Conteúdo |
|--------|---------------|----------|
| `cda_fi_BLC_1` … `cda_fi_BLC_8` | fundo × data × **ativo** | Uma linha por posição em carteira. Cada bloco é um *layout* de tipo de ativo diferente. |
| `cda_fi_PL` | fundo × data | Apenas o patrimônio líquido (`VL_PATRIM_LIQ`). |
| `cda_fie` | — | *Layout* distinto (FIE). **Fora do escopo** deste leitor. |

Empilhar essas granularidades produziria um frame em que `VL_PATRIM_LIQ` só existe nas linhas de
`PL` e todas as colunas de carteira ficam nulas ao lado — um frame que passa em qualquer contrato
de colunas mas **contabiliza em dobro** num `groupby().sum()`.

Por isso o leitor **concatena** os blocos (marcando a origem na coluna `BLOCO`) e faz um
**`left join`** do `VL_PATRIM_LIQ` de `PL` sobre as chaves
`(TP_FUNDO_CLASSE, CNPJ_FUNDO_CLASSE, DT_COMPTC)`. O resultado tem **uma única granularidade** —
fundo × data × ativo — e torna a *diversificação* diretamente calculável.

| Coluna | Tipo | Observação |
|--------|------|-----------|
| `TP_FUNDO_CLASSE`, `CNPJ_FUNDO_CLASSE`, `DENOM_SOCIAL` | `str` | Colunas comuns a todos os blocos. `CNPJ_FUNDO_CLASSE` vem mascarado e deve ter ao menos um CNPJ válido. |
| `DT_COMPTC` | `date` | Data de competência. |
| `BLOCO` | `str` | Sintética: `BLC_1`…`BLC_8`, o bloco de origem da linha. |
| `VL_PATRIM_LIQ` | `str` | Vindo de `PL` pelo *join*; nulo se o fundo não constar de `PL` (o leitor emite um `warning`). |
| Demais colunas (`VL_MERC_POS_FINAL`, `QT_POS_FINAL`, `CD_ISIN`, …) | `str` | Texto exato da CVM — **nunca `float`**. Colunas específicas de um bloco ficam nulas nas linhas dos outros. |

---

## Exemplos

### Ler o mês de referência

```python
from datetime import date

from filings_cvm.ingestion import CdaReader

# Qualquer dia do mês seleciona o dump; o padrão é hoje. Prefira um mês passado
# para dados completos — o mês corrente pode ainda não estar publicado.
df = CdaReader(date_ref=date(2025, 4, 15)).read()

print(df["BLOCO"].value_counts())
```

### Calcular a diversificação (% do patrimônio líquido)

É para isso que o `VL_PATRIM_LIQ` é trazido junto de cada posição:

```python
from decimal import Decimal

# As colunas monetárias vêm como texto exato; converta no ponto em que for calcular.
valor = df["VL_MERC_POS_FINAL"].map(Decimal)
patrimonio = df["VL_PATRIM_LIQ"].map(Decimal)

df["PCT_PL"] = valor / patrimonio
```

### Persistir o artefato bruto (camada *bronze*)

Sem `path_raw` o ZIP é baixado num diretório temporário e descartado. Informando um caminho, o
artefato **bruto e intacto** (o `.zip` e todos os CSVs extraídos) é gravado ali e **mantido**,
antes de qualquer parsing:

```python
from pathlib import Path

df = CdaReader(
    date_ref=date(2025, 4, 15),
    path_raw=Path("/data/bronze/cvm/cda/202504"),
).read()
```

Assim, se a CVM alterar o contrato dos dados e a transformação quebrar, os **bytes exatos** que
causaram a falha continuam em disco, reproduzíveis — em vez de perdidos num novo *download* de
uma fonte que já pode ter mudado outra vez.

### Injetar um logger

O leitor **avisa em vez de falhar** quando um fundo da carteira não consta de `PL`: você continua
recebendo as demais linhas boas do mês, e o aviso nomeia os CNPJs afetados.

```python
df = CdaReader(date_ref=date(2025, 4, 15)).read(int_timeout_s=60)  # timeout maior
```

O `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato),
`ValueError` (o ZIP não contém bloco `BLC_*` ou membro `PL`) ou `pandas.errors.MergeError` (o
membro `PL` não tem uma linha por fundo/data) — falha cedo, sem devolver dados corrompidos.
