# **Exemplos**

Receitas curtas e autocontidas para tarefas comuns. Cada uma funciona sozinha: copie e ajuste.

> **Veja também:** [Uso](usage.md) para a instalação e o conceito geral · [Referência da API](api.md)
> para cada símbolo público.

---

## Receita: ler um dump da CVM e manter o artefato bruto

Sem `path_raw` o arquivo baixado vive num diretório temporário e é descartado. Informando um
caminho, os bytes originais da CVM ficam gravados antes de qualquer parsing, e uma quebra futura de
contrato pode ser reproduzida a partir deles.

```python
from datetime import date
from pathlib import Path

from filings_cvm.ingestion.fi import InformeDiarioReader

df_ = InformeDiarioReader(
    date_ref=date(2025, 1, 15),
    path_raw=Path("bronze/inf_diario"),
).read()

print(df_.shape)
```

---

## Receita: somar valores monetários sem perder precisão

As colunas monetárias chegam como texto exato. Converta para `Decimal` no ponto do cálculo, nunca
para `float`.

```python
from decimal import Decimal

total = sum((Decimal(valor) for valor in df_["VL_PATRIM_LIQ"].dropna()), Decimal("0"))
```

---

## Receita: gerar o XML de envio direto em arquivo

Veja o modelo completo, com todos os campos obrigatórios, em [Uso](usage.md#uso-basico). O
último passo é sempre o mesmo: `export(doc, output_path=...)` grava o arquivo na codificação que a
CVM exige.

```python
from filings_cvm.submission import PerfilMensal

PerfilMensal().export(doc, output_path="perfil_202501.xml")
```
