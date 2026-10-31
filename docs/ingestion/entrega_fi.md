# **Entrega FI — leitura**

Leitura (← CVM) do **índice de entregas** de documentos dos fundos de investimento: uma linha por
entrega (e reapresentação) de um documento por fundo/classe. É o registro do que foi entregue, **não
o documento**. Fonte: `fi_entrega_documento_AAAAMM.zip`, do dataset
[`FI/DOC/ENTREGA`](https://dados.cvm.gov.br/dataset/fi-doc-entrega).

> **Veja também:** [Referência da API](../api.md) · [META](meta.md) · [Proveniência](index.md).

---

## Descrição

| | |
|---|---|
| formato | **ZIP de 2 membros**, `;`, ISO-8859-1, CRLF, sem aspas, 0 linhas irregulares |
| membros | `fi_entrega_documento_AAAAMM.csv` (todos os tipos, 32 tipos em 202609) e `fi_entrega_documento_diario_AAAAMM.csv` (só `DIÁRIO FUNDOS`) |
| partição | **por mês** (`_AAAAMM`) — o `date_ref` seleciona ano **e** mês |
| série | `202501` … `202610` (22 meses medidos; `202412` e anteriores dão 404) |
| tamanho | 202609: 20,7 MB zip · 102.555 linhas (todos) e 1.423.692 linhas / 178 MB (diário) |
| chave única | **nenhuma é afirmada** (uma reapresentação é uma nova linha) |

### Um schema só — sem corte, mas dois readers

Os 22 meses têm o **mesmo header de 11 colunas, byte a byte, nos dois membros**; não há regime
antigo, logo não há reader `Pre*`. Cada membro tem seu reader, seu contract e seu `source_key`
(`entrega_fi`, `entrega_fi_diario`), cada contract pinado ao seu header em
`tests/fixtures/entrega_fi/*_header.csv`. Pedir um mês anterior a `202501` levanta `ValueError`
antes de baixar ~20 MB.

## Tipagem

Só `Data_Inicio_Competencia` e `Data_Fim_Competencia` viram `datetime.date` (ISO, 100%
preenchidas). **O resto é texto exato**:

- `Data_Hora_Entrega` é `datetime` com milissegundos (`2025-01-03 14:57:33.537`); a coerção do repo
  só produz `date`, então fica texto.
- `ID_Documento` é `int` na META mas fica texto (identificador).
- `ID_Subclasse` é 99,3% vazia (todos) / 95,9% (diário); vazio volta vazio.
- `CNPJ_Fundo_Classe` é a única coluna de CNPJ (`tuple_cnpj_cols`): 14 dígitos **sem máscara**, 100%
  preenchida. Sem dado pessoal.
- `Tipo_Fundo_Classe` mistura grafias da CVM (`CLASSES - FIF`, `FI`, `CLASSE FIF/FAPI`, …),
  preservadas verbatim.

## Política de retry

Padrão do repo: 5 tentativas com espera exponencial limitada (~2, 4, 8, 10 s) em `_RETRY_POLICY`;
`retry_policy=` por instância sobrescreve. Cada leitura baixa o ZIP inteiro (~20 MB), mesmo que só
um membro seja lido.

## META

`meta_fi_entrega_documento.txt` — `.txt` solto, **com prefixo `fi_`** (o slug do dataset é
`entrega`), 11 campos = o header dos dois membros. Declara `ID_Documento` `int` e
`Data_Hora_Entrega` `datetime`.

## Exemplos

```python
from datetime import date
from pathlib import Path

from filings_cvm.ingestion.fi import EntregaFiDiarioReader, EntregaFiReader

df_ = EntregaFiReader(date_ref=date(2025, 6, 15)).read()
print(df_[["CNPJ_Fundo_Classe", "Tipo_Documento", "Data_Hora_Entrega"]].head())

# Só o relatório diário (~1,4M linhas por mês)
df_diario = EntregaFiDiarioReader(date_ref=date(2025, 6, 15)).read()

# Guardar o ZIP bruto para a bronze de um datalake
df_ = EntregaFiReader(date_ref=date(2025, 6, 15), path_raw=Path("/data/bronze")).read()
```
