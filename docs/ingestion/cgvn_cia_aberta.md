# **CGVN Companhias Abertas — leitura**

Leitura (← CVM) do **Informe sobre o Código Brasileiro de Governança Corporativa**
(`cgvn_cia_aberta_AAAA.zip`), publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/CGVN/DADOS/).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md) ·
> o [IPE](ipe_cia_aberta.md), o [VLMO](vlmo_cia_aberta.md) e o [FCA](fca_cia_aberta.md).

---

## Os 2 membros — índice + conteúdo (molde do VLMO)

| reader | membro | cols | linhas (2025) |
|---|---|---|---|
| `CgvnCiaAbertaReader` | `cgvn_cia_aberta.csv` | 12 | 382 |
| `CgvnCiaAbertaPraticasReader` | `cgvn_cia_aberta_praticas.csv` | 11 | **19.980** |

O ZIP tem ~4 MiB, mas isso é **um membro de conteúdo grande**, não muitos membros: a `Explicacao`
chega a **~6.000 caracteres**. **Particionado por ano** — o `date_ref` seleciona o **ano**, e os dois
readers baixam o **mesmo** arquivo.

---

## ⚠️ O índice do CGVN não repete a anomalia do FCA

| | índice CGVN | índice FCA |
|---|---|---|
| CNPJ | `CNPJ_Companhia` | `CNPJ_CIA` |
| data ref. | `Data_Referencia` | `DT_REFER` |
| denominação | `Nome_Empresarial` | `DENOM_CIA` |

O [FCA](fca_cia_aberta.md) é o **único** dataset do `DOC` cujo índice usa maiúsculas abreviadas.
Generalizar a partir dele escreveria este errado — por isso **cada dataset é fundamentado nos
próprios bytes**, e a divergência entre os dois contracts é **pinada por teste**.

---

## ⚠️ `Codigo_CVM` vem com zero à esquerda

No arquivo real o código é **`001023`**. É o primeiro lugar deste *portal root* em que tipar como
texto é **load-bearing** (no [IPE](ipe_cia_aberta.md) não havia zeros à esquerda, então a tipagem era
apenas convenção).

Provado por mutação: tipando a coluna como `int64`, a asserção falha com
`np.int64(1023) == '001023'` — **os zeros simplesmente desaparecem**.

`ID_Item` é um identificador **hierárquico** (`1.1.1`) e também fica texto exato.

---

## Tipagem

| membro | colunas de data |
|---|---|
| índice | **4**: `Data_Referencia`, `Data_Entrega`, `Data_Inicio_Exercicio_Social`, `Data_Fim_Exercicio_Social` |
| conteúdo | **1**: `Data_Referencia` (as datas do exercício ficam no índice) |

Todas 100% ISO no arquivo real. Todo o restante é **texto exato da fonte**.
`Motivo_Reapresentacao` chega quase sempre vazio (13 de 382 linhas); `Explicacao` está preenchida em
11.935 das 19.980 linhas; `Pratica_Adotada` é `Sim`/`Não`.

⚠️ O `Link_Download` do índice aponta para **`http://www.rad.cvm.gov.br/ENETCONSULTA/…`** — `http`
puro e um caminho diferente do `https://…/ENET/…` do IPE/VLMO. É devolvido **como publicado**: o
reader não normaliza nem segue o link.

---

## Uso

```python
from datetime import date
from pathlib import Path

from filings_cvm.ingestion.cia_aberta import CgvnCiaAbertaPraticasReader, CgvnCiaAbertaReader

# O índice dos informes entregues no ano:
df_indice = CgvnCiaAbertaReader(date_ref=date(2025, 6, 15)).read()

# As práticas, prática por prática, guardando o .zip cru:
df_praticas = CgvnCiaAbertaPraticasReader(
    date_ref=date(2025, 6, 15),
    path_raw=Path("/data/bronze/cvm/cgvn"),
).read()

# Quais práticas a companhia declarou NÃO adotar, e por quê:
nao_adotadas = df_praticas[df_praticas["Pratica_Adotada"] == "Não"]
```

O frame devolvido carrega, além das colunas da fonte, as seis colunas de
[proveniência](../api.md).

---

## META

A especificação da CVM sai em `MetaCgvnCiaAbertaReader` (o **41º** Meta reader) — veja
[META](meta.md). Os 2 membros da META (12 e 11 campos) batem exatamente com os headers reais.

⚠️ Aqui a forma **padrão** é a que funciona — `meta_cgvn_cia_aberta.zip`. As outras 3 candidatas dão
**404**, incluindo `cgvn_cia_aberta.zip` **sem prefixo**, que é justamente a forma correta do
[FCA](fca_cia_aberta.md). Cinco datasets deste sub-root, cinco medições diferentes: a URL é **pinada
por dataset, jamais derivada**.
