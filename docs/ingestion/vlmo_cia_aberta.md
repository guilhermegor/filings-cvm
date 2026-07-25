# **VLMO Companhias Abertas — leitura**

Leitura (← CVM) dos **valores mobiliários negociados e detidos** por companhias abertas, seus
controladores e controladas (`vlmo_cia_aberta_AAAA.zip`), publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/VLMO/DADOS/).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md) ·
> o [IPE](ipe_cia_aberta.md), que abre o sub-root `CIA_ABERTA/DOC`.

---

## ⚠️ Os 2 membros são **índice + conteúdo**, não registro+satélite

| membro | reader | cols | linhas (2025) | o que é |
|---|---|---|---|---|
| `vlmo_cia_aberta_AAAA.csv` | `VlmoCiaAbertaReader` | 12 | ~5.812 | **índice** dos informes entregues |
| `vlmo_cia_aberta_con_AAAA.csv` | `VlmoCiaAbertaConReader` | 17 | ~63.056 | **conteúdo**: as movimentações |

O índice tem a forma do [IPE](ipe_cia_aberta.md) mais `Motivo_Reapresentacao`, e traz um
`Link_Download` para o documento no RAD da CVM — **devolvido como texto, não seguido**. O conteúdo
não tem link nenhum: são as posições e movimentações em si.

**Particionado por ano** — o `date_ref` seleciona o **ano**. Os dois readers baixam o **mesmo**
arquivo, então um `path_raw` escrito por um serve o outro.

---

## ⚠️ Colunas monetárias: texto exato, nunca float

`Preco_Unitario` e `Volume` chegam com **10 casas decimais** e `Quantidade` é inteiro. O META os
declara `decimal`/`decimal`/`bigint`. **Todos são devolvidos como texto exato da fonte.**

Por quê, concretamente:

```python
"61961072.9999543100"          # o que a CVM publica
float("61961072.9999543100")   # -> 61961072.99995431  (os 2 últimos dígitos somem, em silêncio)
```

Os dígitos finais `…99995` são resíduo de aritmética float **a montante**, na própria CVM — devolvê-los
como publicados é fidelidade, re-arredondá-los é inventar dado. Converta para `Decimal` a jusante se
precisar de aritmética; `bin/check_dtypes.py` impede o atalho `float64` no código deste repositório.

---

## ⚠️ Não há dado pessoal

Apesar de ser um informe de participações de insiders, **o indivíduo nunca é nomeado**:

- `Empresa` é a **companhia** — `Tipo_Empresa` ∈ `Companhia` / `Controlada` / `Controladora`.
- `Tipo_Cargo` é **categoria de cargo** (`Diretor ou Vinculado`, `Conselho Fiscal ou Vinculado`…).
- Medido: **zero** CPF ou CNPJ dentro de `Empresa`.

`tuple_cnpj_cols` é o `CNPJ_Companhia` nos dois membros — **100% válidos**, sem o placeholder
`00.000.000/0000-00` que o IPE tem.

---

## Tipagem

| membro | colunas de data |
|---|---|
| índice | `Data_Referencia`, `Data_Entrega` — ambas 100% ISO |
| conteúdo | `Data_Referencia` (100% ISO) e **`Data_Movimentacao`, ~58% VAZIA** (26.328 de 63.056) |

`Data_Movimentacao` é data por contrato; o branco vira **`NaT`**, não levanta. Todo o restante —
incluindo `Codigo_CVM`, `Versao`, `Link_Download` e as monetárias — é **texto exato da fonte**.

Chegam **parcialmente preenchidos** (colunas obrigatórias, valores não): `Motivo_Reapresentacao`
(452), `Tipo_Cargo` (62.792), `Descricao_Movimentacao` (2.682), `Intermediario` (19.990),
`Caracteristica_Valor_Mobiliario` (62.984).

---

## Uso

```python
from datetime import date
from pathlib import Path

from filings_cvm import VlmoCiaAbertaConReader, VlmoCiaAbertaReader

# O índice dos documentos entregues no ano:
df_indice = VlmoCiaAbertaReader(date_ref=date(2025, 6, 15)).read()

# As movimentações em si, guardando o .zip cru na camada bronze:
df_mov = VlmoCiaAbertaConReader(
    date_ref=date(2025, 6, 15),
    path_raw=Path("/data/bronze/cvm/vlmo"),
).read()

# Aritmética a jusante — Decimal, nunca float:
from decimal import Decimal

total = sum(Decimal(v) for v in df_mov["Volume"] if v)
```

O frame devolvido carrega, além das colunas da fonte, as seis colunas de
[proveniência](../api.md) (`url`, `updated_at`, `source_key`, `package_version`,
`ingestion_run_id`, `content_hash`).

---

## META

A especificação da CVM sai em `MetaVlmoCiaAbertaReader` (o **39º** Meta reader) — veja
[META](meta.md).

⚠️ A META do VLMO é um **`.zip` de 2 membros**, e `meta_vlmo_cia_aberta.txt` dá **404** — o
**inverso exato** do irmão [IPE](ipe_cia_aberta.md), cujo `.txt` solto é a única forma. A URL é
**constante por dataset e jamais derivada**.

⚠️ As `section` voltam **assimétricas** (`meta_vlmo_cia_aberta` + `con`), porque o 1º membro é o
*stem* puro — mesma forma do INTERMED e do COORD_OFERTA. É honrado como está, não corrigido na base.
