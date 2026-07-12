# **FIE — leitura**

Leitura (← CVM) dos três datasets dos **Fundos de Investimento Especialmente constituídos** (FIE),
publicados no [portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/FIE/). **Completa** o
*portal root* `fie/` da biblioteca (irmão de `fi/`, `fidc/`, `fii/`, `fip/`, `fiagro/`).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

O portal `FIE/` publica **3 datasets** — não há `FIE/CAD` (ambos `DADOS/` e `META/` estão vazios).
Cada dataset tem o seu reader (arquivo de um único membro, 6 colunas cada, grão único):

| Reader | Artefato | Partição | Conteúdo |
|--------|----------|----------|----------|
| `BalanceteFieReader` | `balancete_fie_AAAAMM.zip` (ZIP, 1 membro) | **mensal**, 202401→ | Balancete contábil — uma linha por fundo/classe × mês × conta (`VL_SALDO_BALCTE`). Nomenclatura **pós-RCVM 175** (`TP_FUNDO_CLASSE` / `CNPJ_FUNDO_CLASSE`). |
| `BalancoFieReader` | `balanco_fie_AAAA.zip` (ZIP, 1 membro) | **anual**, 2005–2020 (**descontinuado**) | Balanço patrimonial — uma linha por fundo × data × conta (`VL_SALDO_BALANCO`). Nomenclatura **pré-175** (`TP_FUNDO` / `CNPJ_FUNDO`). |
| `MedidasMesFieReader` | `medidas_mes_fie_AAAAMM.csv` (CSV solto) | **mensal** | Medidas mensais — uma linha por fundo × mês, com patrimônio líquido (`VL_PATRIM_LIQ`) e número de cotistas (`NR_COTST`). |

`FIE/MEDIDAS` é **irmão** de `FIE/DOC` no portal, então o seu reader mora no *root* `fie/`, não em
`fie/doc/`. Os dois balanços são ZIPs de um único membro (o membro é selecionado por **nome exato**);
o medidas é um CSV solto, lido direto.

O balanço e o balancete diferem apenas no regime: `balanco` (pré-RCVM 175) usa `TP_FUNDO`/`CNPJ_FUNDO`
e foi **descontinuado em 2020**; `balancete` (pós-175) usa `TP_FUNDO_CLASSE`/`CNPJ_FUNDO_CLASSE` e é a
série viva a partir de 202401. CNPJs vêm **mascarados** (`02.010.153/0001-45`).

### Tipagem

Apenas `DT_COMPTC` é convertida para `date` puro. Saldos (`VL_*`), contagens (`NR_COTST`) e códigos de
conta mantêm o **texto exato da CVM** — **nunca `float`/`int`** —, para que um consumidor converta
para `Decimal` no ponto em que calcula. O mapa de tipos é derivado do contrato, então os dois não
podem divergir.

---

## Política de retry

Todo reader aceita `retry_policy: RetryPolicy | None = None` e declara o seu padrão em
`_RETRY_POLICY` (padrão de fábrica paciente: **5 tentativas**, *backoff* exponencial limitado
~2, 4, 8, 10 s). O argumento do construtor vence o padrão do módulo para aquela instância. Veja a
[visão geral da leitura](index.md#politica-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Balancete de um mês

```python
from decimal import Decimal
from datetime import date
from filings_cvm import BalanceteFieReader

df_ = BalanceteFieReader(date_ref=date(2026, 6, 1)).read()   # o MÊS 2026-06
df_["SALDO"] = df_["VL_SALDO_BALCTE"].dropna().map(Decimal)   # texto exato → Decimal
# muitas linhas por fundo/classe — uma por conta.
```

### Balanço de um ano (série descontinuada em 2020)

```python
from datetime import date
from filings_cvm import BalancoFieReader

df_ = BalancoFieReader(date_ref=date(2020, 6, 1)).read()   # o ANO de 2020
# uma linha por fundo × data × conta.
```

### Medidas mensais + persistir o CSV bruto (camada *bronze*)

```python
from datetime import date
from pathlib import Path
from filings_cvm import MedidasMesFieReader

df_ = MedidasMesFieReader(
    date_ref=date(2026, 6, 1),
    path_raw=Path("/data/bronze/cvm/medidas_mes_fie/202606"),
).read()
# df_[["CNPJ_FUNDO", "DT_COMPTC", "VL_PATRIM_LIQ", "NR_COTST"]]
```

Cada `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou — nos
dois balanços — `ValueError` (o ZIP não contém o membro esperado do período) — falha cedo, sem
devolver dados corrompidos.
