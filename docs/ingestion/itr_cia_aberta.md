# **ITR Companhias Abertas — leitura**

Leitura (← CVM) das **Informações Trimestrais** das companhias abertas
(`itr_cia_aberta_AAAA.zip`), publicadas no [portal de dados abertos](https://dados.cvm.gov.br).

> **Ver também:** [Referência da API](../api.md) · [Uso](../usage.md) · os irmãos do mesmo
> sub-root: [IPE](ipe_cia_aberta.md), [VLMO](vlmo_cia_aberta.md), [FCA](fca_cia_aberta.md),
> [CGVN](cgvn_cia_aberta.md), [FRE](fre_cia_aberta.md), [DFP](dfp_cia_aberta.md).

---

## Os 19 membros

**ZIP anual**, 31,63 MB, **3.640.994 linhas** em 2025 — **3× o DFP**, o maior artefato que esta
biblioteca lê. **Nenhum ragged.**

| reader | membro | cols | linhas (2025) |
|---|---|---|---|
| `ItrCiaAbertaReader` | índice | 9 | 2.257 |
| `ItrCiaAbertaBpaConReader` | `BPA_con` | 14 | 181.678 |
| `ItrCiaAbertaBpaIndReader` | `BPA_ind` | 14 | 276.195 |
| `ItrCiaAbertaBppConReader` | `BPP_con` | 14 | 310.302 |
| `ItrCiaAbertaBppIndReader` | `BPP_ind` | 14 | 465.952 |
| `ItrCiaAbertaDfcMdConReader` | `DFC_MD_con` | 15 | 1.538 |
| `ItrCiaAbertaDfcMdIndReader` | `DFC_MD_ind` | 15 | 1.795 |
| `ItrCiaAbertaDfcMiConReader` | `DFC_MI_con` | 15 | 139.342 |
| `ItrCiaAbertaDfcMiIndReader` | `DFC_MI_ind` | 15 | 189.402 |
| `ItrCiaAbertaDmplConReader` | `DMPL_con` | 16 | 623.847 |
| `ItrCiaAbertaDmplIndReader` | `DMPL_ind` | 16 | 700.872 |
| `ItrCiaAbertaDraConReader` | `DRA_con` | 15 | 32.114 |
| `ItrCiaAbertaDraIndReader` | `DRA_ind` | 15 | 33.000 |
| `ItrCiaAbertaDreConReader` | `DRE_con` | 15 | 156.900 |
| `ItrCiaAbertaDreIndReader` | `DRE_ind` | 15 | 226.309 |
| `ItrCiaAbertaDvaConReader` | `DVA_con` | 15 | 116.854 |
| `ItrCiaAbertaDvaIndReader` | `DVA_ind` | 15 | 173.507 |
| `ItrCiaAbertaComposicaoCapitalReader` | `composicao_capital` | 10 | 2.079 |
| `ItrCiaAbertaParecerReader` | `parecer` | 8 | 7.051 |

`_con` é o **consolidado**, `_ind` o **individual**. **Particionado por ano** — o `date_ref`
seleciona o ano, e **todos** os readers baixam o **mesmo** arquivo (um `path_raw` escrito por um
serve os outros).

---

## ⚠️⚠️ 18 dos 19 membros são IDÊNTICOS ao DFP — e exatamente 1 não é

Comparados **header a header contra as fixtures pinadas do DFP**:

| | DFP (anual) | ITR (trimestral) |
|---|---|---|
| `parecer`, coluna 5 | `TP_RELAT_AUD` | **`TP_RELAT_ESP`** |

Faz sentido — o DFP é **auditado**, o ITR passa por **revisão especial** — e é exatamente por isso
que é perigoso: copiar o contract do `parecer` do DFP acerta a **largura** (8), a **posição** e
**7 dos 8 nomes**. Só o header pinado discorda.

⚠️ **É o contraponto da lição que o DFP ensinou.** Lá o achado foi "aqui, ao contrário de
CRA/CRI/FCA/FRE, membros irmãos SÃO idênticos". Levar *essa* generalização para o dataset vizinho é
o mesmo erro de sempre — **18/19 idênticos é precisamente o que faz alguém copiar o 19º.**

Como no DFP, os 16 membros de demonstração colapsam em **3** listas (19 → **6** distintas):

| cols | membros | por quê |
|---|---|---|
| **14** | `BPA_con/ind`, `BPP_con/ind` | balanço é retrato num instante → só `DT_FIM_EXERC` |
| **15** | `DFC_MD`, `DFC_MI`, `DRA`, `DRE`, `DVA` (× `con`/`ind`) | fluxo cobre período → soma `DT_INI_EXERC` |
| **16** | `DMPL_con/ind` | soma `COLUNA_DF` |

## ⚠️⚠️ O buraco que as listas idênticas abrem (e como foi fechado)

Como 10 membros têm a **mesma** lista de colunas, um reader apontado para o membro **errado**
(o swap `con`↔`ind`, que a nomenclatura convida) devolve um frame **perfeitamente válido**: as
colunas conferem, os tipos conferem, o contrato passa. **Nada fica vermelho.**

Medido por mutação no DFP, e a mesma defesa vale aqui: trocar o `_MEMBER_STEM` de `DRE_con`
pelo de `DRE_ind` fica **vermelho** graças ao teste de identidade do membro. A defesa é afirmar a **identidade do membro** — cada membro sintético dos testes se
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

⚠️ `COLUNA_DF` (DMPL) e `TP_RELAT_ESP` (parecer) chegam **parcialmente vazias**.

## ⚠️ Todos os 19 membros usam a convenção do índice

`CNPJ_CIA` / `DT_REFER` em **todos** — diferente do [FCA](fca_cia_aberta.md) e do
[FRE](fre_cia_aberta.md), cujos satélites trocam para `CNPJ_Companhia` / `Data_Referencia`. Não há
regra entre os datasets do `DOC`, só medição por dataset; o teste usa o FRE como contra-exemplo
vivo.

## ⚠️ META

`meta_itr_cia_aberta_txt.zip` — **infixo `_txt`**. As outras 3 grafias dão **404**, inclusive a
sem-prefixo que é a **correta do FCA**. A URL é constante por dataset e **medida**.

---

## Uso

```python
from datetime import date
from pathlib import Path

from filings_cvm.ingestion.cia_aberta import (
    ItrCiaAbertaDreConReader,
    ItrCiaAbertaReader,
)

# O índice das ITR entregues no ano:
df_indice = ItrCiaAbertaReader(date_ref=date(2025, 6, 15)).read()

# A demonstração do resultado consolidada, guardando o .zip cru:
df_dre = ItrCiaAbertaDreConReader(
    date_ref=date(2025, 6, 15),
    path_raw=Path("/data/bronze/cvm/itr"),
).read()

# Só o exercício corrente (o comparativo vem na mesma tabela):
df_atual = df_dre[df_dre["ORDEM_EXERC"] == "ÚLTIMO"]
```
