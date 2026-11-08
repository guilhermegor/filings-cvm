# **Exemplos**

Receitas autocontidas para tarefas comuns com a biblioteca. Cada receita é independente — copie e
ajuste.

> **Veja também:** [Uso](usage.md) para o básico · [Referência da API](api/index.md) para cada
> símbolo público.

---

## Receita: ler o Informe Diário de um mês

Baixa o dump aberto da CVM para o mês e devolve um `DataFrame` tipado. Qualquer dia do mês
seleciona o dump; prefira um mês passado, pois o corrente pode ainda não estar publicado.

```python
from datetime import date

from filings_cvm.ingestion.fi import InformeDiarioReader

df_ = InformeDiarioReader(date_ref=date(2025, 1, 15)).read()

print(df_.dtypes)
print(df_.head())
```

## Receita: guardar o arquivo bruto baixado

Com `path_raw`, o artefato original (`.zip`, `.csv`, …) é gravado e **mantido** antes de qualquer
parse — assim, se a CVM mudar o contrato, os bytes que quebraram a transformação continuam em
disco para reprocessamento. Sem `path_raw`, nada persiste.

```python
from datetime import date
from pathlib import Path

from filings_cvm.ingestion.fi import InformeDiarioReader

df_ = InformeDiarioReader(date_ref=date(2025, 1, 15), path_raw=Path("raw")).read()
```
