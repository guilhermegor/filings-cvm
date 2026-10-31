# **Complemento FI — leitura**

Leitura (← CVM) das **informações complementares** que os fundos de investimento declaram: política
de risco e de voto, agência de classificação de risco, meios de divulgação de informações ao
cotista e prestadores de serviço. Fonte: `compl_fi_AAAAMM.zip`, do dataset
[`FI/DOC/COMPL`](https://dados.cvm.gov.br/dataset/fi-doc-compl).

> **Veja também:** [Referência da API](../api.md) · [META](meta.md) · [Proveniência](index.md).

---

## Descrição

| | |
|---|---|
| formato | **ZIP de 4 membros** (`<membro>_AAAAMM.csv`), `;`, ISO-8859-1, CRLF; aspas são literais |
| partição | **por mês** (`_AAAAMM`) — o `date_ref` seleciona ano **e** mês |
| série | **fechada**: `201801` … `201904` (16 arquivos); nada foi publicado depois |
| chave única | **nenhuma é afirmada** |

Um reader por membro. Os cabeçalhos são **idênticos nos 16 meses** (medido), logo há um contrato por
membro e nenhum corte de schema:

| membro | reader | colunas | linhas (16 meses) |
|---|---|---|---|
| `compl_fi` | `ComplFiReader` | 20 | 11.604 |
| `compl_fi_inf` | `ComplFiInfReader` | 6 | 25.292 |
| `compl_fi_inf_cotst` | `ComplFiInfCotstReader` | 7 | 21.235 |
| `compl_fi_prest` | `ComplFiPrestReader` | 5 | 39.592 |

Os membros compartilham só o bloco-chave `TP_FUNDO`/`CNPJ_FUNDO`/`DT_COMPTC`; o resto difere. O
membro é escolhido por **nome exato** — `compl_fi_AAAAMM.csv` é prefixo dos outros três. Um `date_ref`
fora de `201801`–`201904` levanta `ValueError` antes de qualquer download; o padrão é o último mês.

## Tipagem

Só `DT_COMPTC` vira `datetime.date` (ISO, 100% preenchida). **Todo o resto é texto exato**, vazio
volta vazio (textos de política chegam a ~4.000 caracteres e várias colunas são parcialmente vazias).

- `CNPJ_FUNDO` é coluna de CNPJ nos 4 membros (100% bem formada); `CNPJ_AG_RISCO` (agência de
  rating, só em `compl_fi`) também, vazia em 188 linhas. Nenhuma coluna guarda CPF.
- `TP_FUNDO`: `FI`, `FAPI`, `FIIM`, `FMP-FGTS`, `FMP-FGTS CL` — grafia da CVM preservada.
- Contratos gerados dos headers publicados e pinados a `tests/fixtures/compl_fi/*_header.csv`.

## Política de retry

Padrão do repo: 5 tentativas com espera exponencial limitada (~2, 4, 8, 10 s) em `_RETRY_POLICY`;
`retry_policy=` por instância sobrescreve.

## META

`meta_compl_fi_txt.zip` (infixo `_txt`), 4 membros `meta_compl_fi*.txt`; lido por
`MetaComplFiReader`. URL constante, nunca derivada.

## Exemplos

```python
from datetime import date
from pathlib import Path

from filings_cvm.ingestion.fi import ComplFiPrestReader, ComplFiReader

df_ = ComplFiReader(date_ref=date(2018, 6, 15)).read()
print(df_[["CNPJ_FUNDO", "AG_RISCO", "GRAU_RISCO"]].head())

# Guardar o ZIP bruto para a bronze de um datalake
df_ = ComplFiPrestReader(date_ref=date(2018, 6, 15), path_raw=Path("/data/bronze")).read()
```
