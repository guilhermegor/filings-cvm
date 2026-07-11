# **DFIN FII — leitura**

Leitura (← CVM) do **índice das demonstrações financeiras dos FII** (`dfin_fii_AAAA.csv`),
publicado no [portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/FII/DOC/DFIN/DADOS/).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md) ·
> o [Informe Mensal FII](inf_mensal_fii.md), que inaugura o portal root `fii/`.

---

## ⚠️ Isto é um **índice**, não uma demonstração financeira

Cada linha descreve **um documento** que o fundo entregou no ano — a data de referência, a data de
entrega, o parecer do auditor, e um **`Link_Download`** apontando para a demonstração em si, no
portal fnet da B3. O reader **devolve o link como texto e não o segue**: baixar o documento
apontado é trabalho de camada superior, e o reader continua fino (o mesmo princípio de todos os
readers aqui — fazer o *parse* do artefato que a CVM publica, nada além).

Duas notas de forma:

- **Particionado por ano** (`dfin_fii_2025.csv`) — o `date_ref` seleciona o **ano**.
- É um **CSV solto, não um ZIP** — não há membro a extrair; o arquivo baixado é lido direto (como
  o snapshot do CAD/FI).

---

## Descrição

`dfin_fii_AAAA.csv` tem **8 colunas**, chaveado na prática por `CNPJ_Fundo_Classe` +
`Data_Referencia` + `Versao` (o mesmo documento reenviado repete com `Versao` maior):

| Coluna | Conteúdo |
|--------|----------|
| `Tipo_Fundo_Classe` | Tipo (ex.: `CLASSES - FII`). |
| `CNPJ_Fundo_Classe` | CNPJ do fundo/classe. |
| `Nome_Fundo_Classe` | Denominação. |
| `Data_Referencia` | Data de referência do documento (fim de trimestre/exercício). |
| `Versao` | Versão do documento (texto exato — nunca inteiro). |
| `Data_Entrega` | Data de entrega/recebimento. |
| `Link_Download` | URL do documento no fnet da B3 — **devolvido como texto, não seguido**. |
| `Parecer_Auditor` | Opinião do auditor (ex.: `Sem ressalva e sem ênfase`). |

**Sem chave única.** Um fundo entrega muitos documentos por ano; nenhum reader deduplica — filtre
por `Versao` se quiser apenas a última versão de cada documento.

### Tipagem

`Data_Referencia` e `Data_Entrega` viram `date` puro; toda outra coluna — incluindo
`Link_Download` e `Versao` — é texto exato da CVM.

---

## Política de retry

Como todo leitor da biblioteca, o `DfinFiiReader` segue o padrão de **`_RETRY_POLICY` por módulo**:
declara a sua paciência (padrão: 5 tentativas, *backoff* exponencial limitado) e aceita um
`retry_policy=` por instância que a sobrescreve. Veja
[a visão geral da leitura](index.md#política-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Listar as demonstrações entregues por um fundo num ano

```python
from datetime import date
from filings_cvm import DfinFiiReader

df_ = DfinFiiReader(date_ref=date(2025, 6, 15)).read()   # o ANO de 2025
fundo = df_[df_["CNPJ_Fundo_Classe"] == "00.332.266/0001-31"]
# fundo[["Data_Referencia", "Versao", "Parecer_Auditor", "Link_Download"]]
```

### Só a última versão de cada documento

```python
mais_recente = (
    df_.sort_values("Versao")
    .groupby(["CNPJ_Fundo_Classe", "Data_Referencia"], as_index=False)
    .last()
)
```

### Persistir o CSV bruto (camada *bronze*)

```python
from datetime import date
from pathlib import Path
from filings_cvm import DfinFiiReader

DfinFiiReader(
    date_ref=date(2025, 6, 15),
    path_raw=Path("/data/bronze/cvm/dfin_fii/2025"),
).read()
```

Cada `read` levanta `OSError` (falha de download) ou `ContractError` (CSV viola o contrato) —
falha cedo, sem devolver dados corrompidos.
