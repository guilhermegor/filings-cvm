# **Informes periódicos FIP — leitura**

Leitura (← CVM) dos informes periódicos dos **Fundos de Investimento em Participações**,
publicados no [portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/FIP/DOC/). São dois
datasets, um reader cada, que **inauguram o portal root `fip/`**:

- **`InfTrimestralFipReader`** — `inf_trimestral_fip_AAAA.csv`, o informe **trimestral** do regime
  **pré-RCVM 175** (série 2010–2023).
- **`InfQuadrimestralFipReader`** — `inf_quadrimestral_fip_AAAA.csv`, o informe **quadrimestral**
  que o substituiu no regime **pós-RCVM 175** (a partir de 2024).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md) ·
> os informes FII ([Trimestral](inf_trimestral_fii.md), [Anual](inf_anual_fii.md)), de forma
> semelhante particionados por ano.

---

## Dois regimes, uma transição

A CVM trocou o informe **trimestral** pelo **quadrimestral** em 2024, junto com a RCVM 175. Os dois
datasets continuam publicados lado a lado — o histórico trimestral (2010–2023) e o quadrimestral em
curso (2024→). O conteúdo é **quase idêntico**; a única diferença estrutural está nas duas primeiras
colunas:

| | Trimestral (pré-175) | Quadrimestral (pós-175) |
|---|---|---|
| Identificador do fundo | `CNPJ_FUNDO` | `TP_FUNDO_CLASSE` + `CNPJ_FUNDO_CLASSE` |
| Nº de colunas | 54 | 55 |
| Cadência | trimestral | quadrimestral |
| Período | 2010–2023 | 2024→ |

A RCVM 175 desdobra o fundo em fundo/classe — daí `CNPJ_FUNDO_CLASSE` no lugar de `CNPJ_FUNDO`. Todo
o restante (patrimônio, cotas, capital comprometido/subscrito/integralizado, o *breakdown* de
cotistas subscritores por categoria de investidor e os campos de cota por classe) é o mesmo.

Duas notas de forma, valendo para os dois:

- **Particionado por ano** (`inf_trimestral_fip_2023.csv`, `inf_quadrimestral_fip_2024.csv`) — o
  `date_ref` seleciona o **ano**, mesmo no quadrimestral.
- São **CSVs soltos, não ZIPs** — não há membro a extrair; o arquivo baixado é lido direto.

---

## Descrição

Cada linha é um fundo (ou fundo/classe) num período de competência. Colunas principais:

| Coluna | Conteúdo |
|--------|----------|
| `TP_FUNDO_CLASSE` | Tipo do fundo/classe (**só no quadrimestral**). |
| `CNPJ_FUNDO` / `CNPJ_FUNDO_CLASSE` | CNPJ do fundo (trimestral) / do fundo/classe (quadrimestral). |
| `DENOM_SOCIAL` | Denominação social. |
| `DT_COMPTC` | Data de competência do documento. |
| `VL_PATRIM_LIQ`, `QT_COTA`, `VL_PATRIM_COTA` | Patrimônio líquido, quantidade e valor da cota. |
| `VL_CAP_COMPROM`, `VL_CAP_SUBSCR`, `VL_CAP_INTEGR` | Capital comprometido / subscrito / integralizado. |
| `NR_COTST_SUBSCR_*`, `PR_COTA_SUBSCR_*` | Nº de cotistas subscritores e % das cotas subscritas, por categoria de investidor. |
| `CLASSE_COTA`, `VL_QUOTA_CLASSE`, `DIREITO_POLIT_CLASSE`, `DIREITO_ECON_CLASSE` | Campos da classe de cotas. |

**Sem chave única.** Um fundo reporta uma vez por período; múltiplas classes repetem o fundo entre
linhas.

### Tipagem

Apenas `DT_COMPTC` vira `date` puro; toda outra coluna — inclusive os valores de dinheiro e cota —
é texto exato da CVM (valores monetários/quantidade ficam `str`, nunca convertidos a `float` aqui,
para não perder precisão antes de uma camada superior decidir a própria escala).

---

## Política de retry

Como todo leitor da biblioteca, ambos seguem o padrão de **`_RETRY_POLICY` por módulo**: declaram a
sua paciência (padrão: 5 tentativas, *backoff* exponencial limitado) e aceitam um `retry_policy=`
por instância que a sobrescreve. Veja
[a visão geral da leitura](index.md#política-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Ler o informe trimestral (regime pré-175)

```python
from datetime import date
from filings_cvm import InfTrimestralFipReader

df_ = InfTrimestralFipReader(date_ref=date(2023, 5, 15)).read()   # o ANO de 2023
# df_[["CNPJ_FUNDO", "DT_COMPTC", "VL_PATRIM_LIQ", "VL_CAP_INTEGR"]]
```

### Ler o informe quadrimestral (regime pós-175)

```python
from datetime import date
from filings_cvm import InfQuadrimestralFipReader

df_ = InfQuadrimestralFipReader(date_ref=date(2024, 8, 15)).read()   # o ANO de 2024
# df_[["CNPJ_FUNDO_CLASSE", "TP_FUNDO_CLASSE", "DT_COMPTC", "VL_PATRIM_LIQ"]]
```

### Persistir o CSV bruto (camada *bronze*)

```python
from datetime import date
from pathlib import Path
from filings_cvm import InfQuadrimestralFipReader

InfQuadrimestralFipReader(
    date_ref=date(2024, 8, 15),
    path_raw=Path("/data/bronze/cvm/inf_quadrimestral_fip/2024"),
).read()
```

Cada `read` levanta `OSError` (falha de download) ou `ContractError` (CSV viola o contrato) —
falha cedo, sem devolver dados corrompidos.
