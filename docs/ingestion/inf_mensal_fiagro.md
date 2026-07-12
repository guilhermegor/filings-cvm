# **Informe Mensal FIAGRO — leitura**

Leitura (← CVM) do **Informe Mensal dos FIAGRO** (`inf_mensal_fiagro_AAAAMM.zip`), publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/FIAGRO/DOC/INF_MENSAL/DADOS/).
Inaugura o *portal root* `fiagro/` da biblioteca (irmão de `fi/`, `fidc/`, `fii/`, `fip/`).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

`inf_mensal_fiagro_AAAAMM.zip` traz **2 membros** — o informe mensal e o desdobramento por
subclasse. Cada membro tem o seu reader:

| Reader | Membro | Conteúdo |
|--------|--------|----------|
| `InfMensalFiagroReader` | `inf_mensal_fiagro` | Informe mensal (133 colunas) — cadastro da classe, cotistas por tipo, patrimônio, carteira (agronegócio, securitização, direitos creditórios), prazos a vencer/vencidos, passivo. Uma linha por classe por mês. |
| `InfMensalFiagroSubclasseReader` | `inf_mensal_fiagro_subclasse` | Desdobramento por subclasse (6 colunas) — `Numero_Cotas` e `Valor_Patrimonial_Cota` por `Nome_Subclasse`. Naturalmente **longo** (uma linha por subclasse). |

Os dois baixam o **mesmo** ZIP mensal, então um `path_raw` gravado por qualquer um serve ao outro.
O dump é **particionado por mês** (`AAAAMM`, série a partir de `202505`): os readers aceitam
`date_ref` (qualquer dia do mês de referência seleciona o dump e, dentro dele, o membro
`…_AAAAMM.csv`). A seleção do membro é por **nome exato** — o stem `inf_mensal_fiagro` é prefixo
estrito de `inf_mensal_fiagro_subclasse`, então a igualdade exata é o que os distingue.

O FIAGRO usa a nomenclatura **pós-RCVM 175** (Classe / Subclasse); a chave é `CNPJ_Classe`.

### Tipagem

Toda coluna é texto (`str`) exceto as colunas de data, convertidas para `date` puro — o informe
tem três (`Data_Referencia`, `Data_Entrega`, `Data_Registro`), a subclasse apenas
`Data_Referencia`. Colunas monetárias, de quantidade, de contagem e de percentual mantêm o **texto
exato da CVM** — **nunca `float`** —, para que um consumidor converta para `Decimal` no ponto em
que calcula. O mapa de tipos é derivado do contrato, então os dois não podem divergir.

> **Grafias da CVM preservadas verbatim:** `Provisoes_Contigencias` (falta o *n* de
> *Contingências*) e a assimetria `A_Vencer_Acima1080_Dias` (com `_` antes de `Dias`) contra
> `Vencidos_Acima1080Dias` (sem). O contrato reproduz os nomes como publicados, não como
> "deveriam" ser.

---

## Política de retry

Todo reader aceita `retry_policy: RetryPolicy | None = None` e declara o seu padrão em
`_RETRY_POLICY` (padrão de fábrica paciente: **5 tentativas**, *backoff* exponencial limitado
~2, 4, 8, 10 s). O argumento do construtor vence o padrão do módulo para aquela instância. Veja a
[visão geral da leitura](index.md#politica-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Ler o patrimônio líquido de um mês

```python
from decimal import Decimal
from datetime import date
from filings_cvm import InfMensalFiagroReader

df_ = InfMensalFiagroReader(date_ref=date(2025, 6, 1)).read()
df_["PL"] = df_["Patrimonio_Liquido"].dropna().map(Decimal)   # texto exato → Decimal
```

### Cotas por subclasse (membro longo)

```python
from datetime import date
from filings_cvm import InfMensalFiagroSubclasseReader

df_ = InfMensalFiagroSubclasseReader(date_ref=date(2025, 6, 1)).read()
# muitas linhas por classe — uma por Nome_Subclasse.
```

### Persistir o dump bruto (camada *bronze*) uma vez para os dois

```python
from datetime import date
from pathlib import Path
from filings_cvm import InfMensalFiagroReader

# Um download; o ZIP e os dois CSVs ficam em disco para o outro reader.
InfMensalFiagroReader(
    date_ref=date(2025, 6, 1),
    path_raw=Path("/data/bronze/cvm/inf_mensal_fiagro/202506"),
).read()
```

Cada `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou
`ValueError` (o ZIP não contém o membro esperado do mês) — falha cedo, sem devolver dados
corrompidos.
