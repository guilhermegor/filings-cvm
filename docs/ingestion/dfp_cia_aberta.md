# **DFP Companhias Abertas — leitura**

Leitura (← CVM) das **Demonstrações Financeiras Padronizadas** das companhias abertas
(`dfp_cia_aberta_AAAA.zip`), publicadas no [portal de dados abertos](https://dados.cvm.gov.br).

> **Ver também:** [Referência da API](../api.md) · [Uso](../usage.md) · os irmãos do mesmo
> sub-root: [IPE](ipe_cia_aberta.md), [VLMO](vlmo_cia_aberta.md), [FCA](fca_cia_aberta.md),
> [CGVN](cgvn_cia_aberta.md), [FRE](fre_cia_aberta.md).

---

## Os 19 membros

**ZIP anual**, 12,73 MB, **~1,17 milhão de linhas** em 2025, **nenhum ragged**.

| reader | membro | cols | linhas (2025) |
|---|---|---|---|
| `DfpCiaAbertaReader` | índice | 9 | 750 |
| `DfpCiaAbertaBpaConReader` | `BPA_con` | 14 | 59.262 |
| `DfpCiaAbertaBpaIndReader` | `BPA_ind` | 14 | 88.897 |
| `DfpCiaAbertaBppConReader` | `BPP_con` | 14 | 101.380 |
| `DfpCiaAbertaBppIndReader` | `BPP_ind` | 14 | 150.064 |
| `DfpCiaAbertaDfcMdConReader` | `DFC_MD_con` | 15 | 504 |
| `DfpCiaAbertaDfcMdIndReader` | `DFC_MD_ind` | 15 | 758 |
| `DfpCiaAbertaDfcMiConReader` | `DFC_MI_con` | 15 | 48.500 |
| `DfpCiaAbertaDfcMiIndReader` | `DFC_MI_ind` | 15 | 65.449 |
| `DfpCiaAbertaDmplConReader` | `DMPL_con` | 16 | 225.735 |
| `DfpCiaAbertaDmplIndReader` | `DMPL_ind` | 16 | 246.495 |
| `DfpCiaAbertaDraConReader` | `DRA_con` | 15 | 6.520 |
| `DfpCiaAbertaDraIndReader` | `DRA_ind` | 15 | 6.702 |
| `DfpCiaAbertaDreConReader` | `DRE_con` | 15 | 30.786 |
| `DfpCiaAbertaDreIndReader` | `DRE_ind` | 15 | 43.367 |
| `DfpCiaAbertaDvaConReader` | `DVA_con` | 15 | 38.554 |
| `DfpCiaAbertaDvaIndReader` | `DVA_ind` | 15 | 56.070 |
| `DfpCiaAbertaComposicaoCapitalReader` | `composicao_capital` | 10 | 665 |
| `DfpCiaAbertaParecerReader` | `parecer` | 8 | 3.715 |

`_con` é o **consolidado**, `_ind` o **individual**. **Particionado por ano** — o `date_ref`
seleciona o ano, e **todos** os readers baixam o **mesmo** arquivo (um `path_raw` escrito por um
serve os outros).

---

## ⚠️⚠️ Este dataset INVERTE a armadilha de todos os anteriores

Em CRA, CRI, FCA e FRE a regra era *"membros de mesma largura têm colunas diferentes — nunca copie
o irmão"*. **Aqui é o contrário:** os 16 membros de demonstração colapsam em **3** listas de
colunas, e membros diferentes são **genuinamente idênticos**:

| cols | membros | por quê |
|---|---|---|
| **14** | `BPA_con/ind`, `BPP_con/ind` | balanço é retrato num instante → só `DT_FIM_EXERC` |
| **15** | `DFC_MD`, `DFC_MI`, `DRA`, `DRE`, `DVA` (× `con`/`ind`) | fluxo cobre período → soma `DT_INI_EXERC` |
| **16** | `DMPL_con/ind` | soma `COLUNA_DF`, a coluna do PL a que a mutação pertence |

19 membros → **6** listas distintas (as 3 acima + índice, composição do capital e parecer).

**Isso é medido, não presumido.** Cada contrato continua **gerado do seu próprio header** e pinado,
e um teste afirma o agrupamento **contra as fixtures**. Presumir que membros são iguais e presumir
que são diferentes é o mesmo erro — nenhum dos dois é medição.

## ⚠️⚠️ O buraco que as listas idênticas abrem (e como foi fechado)

Como 10 membros têm a **mesma** lista de colunas, um reader apontado para o membro **errado**
(o swap `con`↔`ind`, que a nomenclatura convida) devolve um frame **perfeitamente válido**: as
colunas conferem, os tipos conferem, o contrato passa. **Nada fica vermelho.**

Medido por mutação: trocar o `_MEMBER_STEM` de `DRE_con` pelo de `DRE_ind` passava na suíte
**inteira**. A defesa é afirmar a **identidade do membro** — cada membro sintético dos testes se
identifica numa coluna, e cada reader tem de ler **o seu**. Com isso, o mesmo swap fica vermelho.

---

## ⚠️⚠️ A escala do valor está em OUTRA coluna

`VL_CONTA` chega com **10 casas decimais** (`2398719197.0000000000`) e é **texto exato** — um
`float64` apaga os dígitos publicados em silêncio (mesma falha já medida no VLMO).

E o número **sozinho não significa nada**: `ESCALA_MOEDA` vale `MIL` ou `UNIDADE`. Somar `VL_CONTA`
sem ler `ESCALA_MOEDA` erra por **1000×**.

**Os readers não reescalam** — ficam thin, e reescalar destruiria o valor publicado. A conversão é
decisão de quem consome:

```python
from decimal import Decimal

fator = {"MIL": Decimal(1000), "UNIDADE": Decimal(1)}
valor = Decimal(row["VL_CONTA"]) * fator[row["ESCALA_MOEDA"]]
```

## Tipagem

Colunas de data são exatamente as `DT_*` (todas 100% ISO): `DT_REFER` + `DT_RECEB` no índice,
`DT_FIM_EXERC` no balanço, `DT_INI_EXERC` + `DT_FIM_EXERC` nos demais. Branco vira `NaT`.

Todo o restante é **texto exato**, incluindo `VL_CONTA` (monetário) e `QT_ACAO_*` (contagens).

⚠️ **`CD_CVM` vem `001023`, com zero à esquerda** — texto *load-bearing*, como no CGVN.

⚠️ **`ORDEM_EXERC` (`ÚLTIMO`/`PENÚLTIMO`) duplica cada conta**: o exercício corrente e o
comparativo. **Nenhuma chave única é afirmada.**

⚠️ `COLUNA_DF` (DMPL) e `TP_RELAT_AUD` (parecer) chegam **parcialmente vazias**.

## ⚠️ Todos os 19 membros usam a convenção do índice

`CNPJ_CIA` / `DT_REFER` em **todos** — diferente do [FCA](fca_cia_aberta.md) e do
[FRE](fre_cia_aberta.md), cujos satélites trocam para `CNPJ_Companhia` / `Data_Referencia`. Não há
regra entre os datasets do `DOC`, só medição por dataset; o teste usa o FRE como contra-exemplo
vivo.

## ⚠️ META

`meta_dfp_cia_aberta_txt.zip` — **infixo `_txt`**. As outras 3 grafias dão **404**, inclusive a
sem-prefixo que é a **correta do FCA**. A URL é constante por dataset e **medida**.

---

## Uso

```python
from datetime import date
from pathlib import Path

from filings_cvm.ingestion.cia_aberta import (
    DfpCiaAbertaDreConReader,
    DfpCiaAbertaReader,
)

# O índice das DFP entregues no ano:
df_indice = DfpCiaAbertaReader(date_ref=date(2025, 6, 15)).read()

# A demonstração do resultado consolidada, guardando o .zip cru:
df_dre = DfpCiaAbertaDreConReader(
    date_ref=date(2025, 6, 15),
    path_raw=Path("/data/bronze/cvm/dfp"),
).read()

# Só o exercício corrente (o comparativo vem na mesma tabela):
df_atual = df_dre[df_dre["ORDEM_EXERC"] == "ÚLTIMO"]
```
