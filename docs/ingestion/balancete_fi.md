# **Balancete FI — leitura**

Leitura (← CVM) do **balancete mensal** dos fundos de investimento: uma linha por fundo/classe ×
mês de competência × conta contábil, com o saldo da conta. Fonte: `balancete_fi_AAAAMM.zip`, do
dataset [`FI/DOC/BALANCETE`](https://dados.cvm.gov.br/dataset/fi-doc-balancete).

> **Veja também:** [Referência da API](../api.md) · [META](meta.md) · [Proveniência](index.md).

---

## Descrição

| | |
|---|---|
| formato | **ZIP de 1 membro** (`balancete_fi_AAAAMM.csv`), `;`, UTF-8/ASCII puro (lido como ISO-8859-1), CRLF, sem aspas |
| partição | **por mês** (`_AAAAMM`) — o `date_ref` seleciona ano **e** mês |
| série | `201501` … em diante (141 arquivos no diretório; o CKAN lista só os 12 últimos) |
| tamanho | ~6,8 MB (2015) · 13,4 MB (2023) · 14,7 MB zipado / 153 MB CSV / 2.191.291 linhas (`202609`) |
| chave única | **nenhuma é afirmada** (grão natural: fundo/classe × data × conta) |

### Um padrão de nome, dois schemas — o corte é `202311`

| regime | meses | colunas | bloco-chave | reader |
|---|---|---|---|---|
| legado | `201501`–**`202310`** | **5** | `CNPJ_FUNDO` | `BalanceteFiPre202311Reader` |
| fundo/classe | **`202311`**– | **6** | `TP_FUNDO_CLASSE` + `CNPJ_FUNDO_CLASSE` | `BalanceteFiReader` |

O corte foi **medido** sobre os headers publicados (todo mês de `202302` a `202312`, mais amostras
de 2015 a 2022), **não deduzido** da RCVM 175 nem herdado do Perfil Mensal, cujo corte é `202312`:
aqui a troca chega **um mês antes**. Por isso o reader legado se chama pela data medida, não por
uma norma — nome é afirmação.

As 4 colunas finais são idênticas nos dois regimes; mesmo assim são **dois contracts**, cada um
gerado do seu header publicado e pinado a `tests/fixtures/balancete_fi/*_header.csv`. Pedir a um
reader o mês do outro levanta `ValueError` **nomeando o irmão**, antes de baixar 14 MB.

Os 6 campos do fundo/classe são os mesmos do `balancete_fie` (FIE), mas cada dataset é pinado à sua
própria fonte.

## Tipagem

Só `DT_COMPTC` vira `datetime.date` (ISO, 100% preenchida). **Todo o resto é texto exato**:
`VL_SALDO_BALCTE` é `numeric(23,2)` na META, sempre com 2 casas e com **negativos** (~19%) — nunca
`float`; `CD_CONTA_BALCTE` é `char(8)` (~470 contas distintas) e `PLANO_CONTA_BALCTE` é `COFI` em
todas as linhas medidas.

- `CNPJ_FUNDO[_CLASSE]` é a única coluna de CNPJ (`tuple_cnpj_cols`): 100% bem formada, pontuada.
- `TP_FUNDO_CLASSE` volta `FI` em `202311`, mas em `202609` já mistura `CLASSES - FIF` (2.190.840)
  e `FI` (451) — a grafia da CVM é preservada.
- ⚠️ Em `201501`, **22 linhas** chegam com `CD_CONTA_BALCTE` e `VL_SALDO_BALCTE` **vazios**; vazio
  volta vazio. Em `202310`, `202311` e `202609` não há células vazias.

## Política de retry

Padrão do repo: 5 tentativas com espera exponencial limitada (~2, 4, 8, 10 s) em `_RETRY_POLICY`;
`retry_policy=` por instância sobrescreve. Cada leitura baixa ~14 MB.

## META

`meta_balancete_fi.txt` — `.txt` solto, **6 campos = o header de `202311` em diante**, sem
`CNPJ_FUNDO`. Logo a META **não é oráculo do contrato legado** (registrado em
`_META_UNDESCRIBED_READERS`). Declara `VL_SALDO_BALCTE` como `numeric` precisão 23 / escala 2.

## Exemplos

```python
from datetime import date
from pathlib import Path

from filings_cvm.ingestion.fi import BalanceteFiPre202311Reader, BalanceteFiReader

# Regime atual (202311 em diante)
df_ = BalanceteFiReader(date_ref=date(2025, 6, 15)).read()
print(df_[["CNPJ_FUNDO_CLASSE", "CD_CONTA_BALCTE", "VL_SALDO_BALCTE"]].head())

# Série histórica (201501–202310)
df_pre = BalanceteFiPre202311Reader(date_ref=date(2020, 1, 15)).read()

# Guardar o ZIP bruto para a bronze de um datalake
df_ = BalanceteFiReader(date_ref=date(2025, 6, 15), path_raw=Path("/data/bronze")).read()
```
