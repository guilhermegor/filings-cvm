# **Informe Diário FIF — leitura**

Leitura (← CVM) do dump mensal de *open-data* do **Informe Diário de fundos**
(`inf_diario_fi_AAAAMM`), publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/).

> **Veja também:** [Referência da API](../api.md) para cada símbolo público · [Uso](../usage.md)
> para instalação e o conceito geral.

---

## Descrição

`InformeDiarioReader` baixa o ZIP mensal, extrai o CSV, valida o **contrato**
(colunas obrigatórias + coluna de CNPJ coercível) e devolve um `DataFrame` com os **tipos
declarados** aplicados — nunca a inferência do pandas.

> **Nota:** este leitor consome o CSV de *open-data* — um artefato **distinto** do XML do padrão
> Informe Diário V4 produzido no [Envio](../submission/informe_diario.md). Por isso ele tem o
> seu próprio contrato de colunas, e não reaproveita o schema de submissão.

| Coluna | Tipo | Observação |
|--------|------|-----------|
| `TP_FUNDO_CLASSE`, `CNPJ_FUNDO_CLASSE`, `ID_SUBCLASSE` | `str` | `CNPJ_FUNDO_CLASSE` deve ter ao menos um CNPJ válido. |
| `DT_COMPTC` | `date` | Data de competência. |
| `VL_TOTAL`, `VL_QUOTA`, `VL_PATRIM_LIQ`, `CAPTC_DIA`, `RESG_DIA` | `str` | Texto exato da CVM — **nunca `float`**; converta para `Decimal` ao calcular. |
| `NR_COTST` | `Int64` | Inteiro nulável. |

---

## Exemplos

### Ler o mês de referência

```python
from datetime import date

from filings_cvm.ingestion import InformeDiarioReader

# Qualquer dia do mês seleciona o dump; o padrão é hoje. Prefira um mês passado
# para dados completos — o mês corrente pode ainda não estar publicado.
df = InformeDiarioReader(date_ref=date(2025, 1, 15)).read()

print(df.dtypes)
print(df.head())
```

### Converter valores monetários para `Decimal`

As colunas monetárias vêm como texto exato; converta no ponto em que for calcular:

```python
from decimal import Decimal

df["VL_PATRIM_LIQ"] = df["VL_PATRIM_LIQ"].map(Decimal)
```

### Persistir o artefato bruto (camada *bronze*)

Sem `path_raw` o ZIP é baixado num diretório temporário e descartado. Informando um caminho, o
artefato **bruto e intacto** (o `.zip` e o CSV extraído) é gravado ali e **mantido**, antes de
qualquer parsing — veja [a visão geral da leitura](index.md#artefato-bruto-path_raw).

```python
from pathlib import Path

df = InformeDiarioReader(
    date_ref=date(2025, 1, 15),
    path_raw=Path("/data/bronze/cvm/informe_diario/202501"),
).read()
```

### Ajustar o timeout

```python
from filings_cvm.ingestion import InformeDiarioReader

reader = InformeDiarioReader(date_ref=date(2025, 1, 15))
df = reader.read(int_timeout_s=60)   # timeout de download maior
```

O `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou
`ValueError` (o ZIP não contém CSV) — falha cedo, sem devolver dados parciais.
