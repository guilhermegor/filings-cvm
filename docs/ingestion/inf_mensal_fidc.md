# **Informe Mensal FIDC — leitura**

Leitura (← CVM) do **Informe Mensal dos FIDC** (`inf_mensal_fidc_AAAAMM.zip`), publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/FIDC/DOC/INF_MENSAL/DADOS/).
Inaugura o *portal root* `fidc/` da biblioteca (irmão de `fi/`).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

`inf_mensal_fidc_AAAAMM.zip` traz **17 membros** — as tabelas do informe mensal (Tabelas I–X mais
as sub-tabelas de X). Cada membro compartilha o mesmo prefixo-chave de quatro colunas —
`TP_FUNDO_CLASSE`, `CNPJ_FUNDO_CLASSE`, `DENOM_SOCIAL`, `DT_COMPTC` — e então carrega as colunas
específicas da sua tabela. Cada membro tem o seu reader:

| Reader | Membro | Tabela |
|--------|--------|--------|
| `InfMensalFidcTabIReader` | `inf_mensal_fidc_tab_I` | I — composição do ativo |
| `InfMensalFidcTabIIReader` | `inf_mensal_fidc_tab_II` | II — carteira de direitos creditórios por segmento |
| `InfMensalFidcTabIIIReader` | `inf_mensal_fidc_tab_III` | III — composição do passivo |
| `InfMensalFidcTabIVReader` | `inf_mensal_fidc_tab_IV` | IV — patrimônio líquido |
| `InfMensalFidcTabVReader` | `inf_mensal_fidc_tab_V` | V — prazos dos direitos creditórios a adquirir |
| `InfMensalFidcTabVIReader` | `inf_mensal_fidc_tab_VI` | VI — prazos dos direitos creditórios da carteira |
| `InfMensalFidcTabVIIReader` | `inf_mensal_fidc_tab_VII` | VII — direitos creditórios por origem |
| `InfMensalFidcTabIXReader` | `inf_mensal_fidc_tab_IX` | IX — taxas de negociação (compra/venda) |
| `InfMensalFidcTabXReader` | `inf_mensal_fidc_tab_X` | X — classificação de risco (SCR) e débito tributário |
| `InfMensalFidcTabX1Reader` | `inf_mensal_fidc_tab_X_1` | X.1 — nº de cotistas por classe/série |
| `InfMensalFidcTabX11Reader` | `inf_mensal_fidc_tab_X_1_1` | X.1.1 — nº de cotistas por tipo de investidor |
| `InfMensalFidcTabX2Reader` | `inf_mensal_fidc_tab_X_2` | X.2 — cotas por classe/série (qtd. e valor) |
| `InfMensalFidcTabX3Reader` | `inf_mensal_fidc_tab_X_3` | X.3 — rentabilidade no mês |
| `InfMensalFidcTabX4Reader` | `inf_mensal_fidc_tab_X_4` | X.4 — movimentações de cotas por tipo de operação |
| `InfMensalFidcTabX5Reader` | `inf_mensal_fidc_tab_X_5` | X.5 — liquidez por faixa de prazo |
| `InfMensalFidcTabX6Reader` | `inf_mensal_fidc_tab_X_6` | X.6 — desempenho esperado × realizado |
| `InfMensalFidcTabX7Reader` | `inf_mensal_fidc_tab_X_7` | X.7 — garantias dos direitos creditórios |

Os 17 baixam o **mesmo** ZIP mensal, então um `path_raw` gravado por qualquer um serve aos outros.
O dump é **particionado por mês** (`AAAAMM`): os readers aceitam `date_ref` (qualquer dia do mês de
referência seleciona o dump e, dentro dele, o membro `…_AAAAMM.csv`). As sub-tabelas (X.1, X.2, …)
são naturalmente **longas** — muitas linhas por fundo, uma por série/subclasse —, então nenhum
reader declara granularidade única.

### Tipagem

Toda coluna é texto (`str`) exceto `DT_COMPTC`, convertida para `date` puro. Colunas monetárias
(`VL`), de quantidade (`QT`), de contagem (`NR`) e de percentual (`PR`) mantêm o **texto exato da
CVM** — **nunca `float`** —, para que um consumidor converta para `Decimal` no ponto em que calcula.
O mapa de tipos é derivado do contrato, então os dois não podem divergir.

---

## Política de retry — paciência por tabela

Todo reader aceita um `retry_policy: RetryPolicy | None = None` no construtor, repassado ao *seam*
de download como a sua agenda de novas tentativas / *backoff*. Cada reader **declara a sua própria
paciência** por meio do atributo de classe `_RETRY_POLICY`, então a política fica **junto da
tabela** e é ajustável **por tabela** — sem tocar na base nem nos outros 16 readers.

A resolução é em duas camadas:

1. **Argumento `retry_policy` no construtor** — se informado, vence para *aquela instância*.
2. **Atributo de classe `_RETRY_POLICY` do próprio reader** — o padrão quando nada é passado. O
   padrão de fábrica é paciente (o portal da CVM aplica *throttle* sob carga): **5 tentativas**,
   *backoff* exponencial limitado (~2, 4, 8, 10 s).

```python
from datetime import date
from filings_cvm import InfMensalFidcTabIReader, RetryPolicy

# 1. Padrão — o reader usa a política do seu próprio módulo (5 tentativas). Nada a passar:
df_ = InfMensalFidcTabIReader(date_ref=date(2025, 6, 1)).read()

# 2. Sobrescrever numa chamada — o argumento vence o padrão do módulo:
cls_retry_policy = RetryPolicy(int_max_attempts=8, float_base_wait_s=1.0)
df_ = InfMensalFidcTabIReader(date_ref=date(2025, 6, 1), retry_policy=cls_retry_policy).read()

# 3. Inspecionar o padrão de um módulo sem construir (co-localizado, por tabela):
InfMensalFidcTabIReader._RETRY_POLICY   # → RetryPolicy(int_max_attempts=5, …)
```

### Paciência diferente por tabela

As tabelas têm tamanhos bem diferentes — a `tab_X_4` (movimentações) tem dezenas de milhares de
linhas, enquanto a `tab_IV` (patrimônio líquido) tem uma linha por fundo. Como cada reader carrega
o **mesmo** ZIP, o *download* é idêntico; mas se um cenário exigir mais (ou menos) paciência para
uma tabela específica, basta uma política diferente — por instância:

```python
from datetime import date
from filings_cvm import InfMensalFidcTabX4Reader, RetryPolicy

# Mais tentativas e teto de espera maior só para esta tabela, nesta execução:
cls_retry_policy = RetryPolicy(int_max_attempts=10, float_base_wait_s=2.0, float_max_wait_s=30.0)
df_ = InfMensalFidcTabX4Reader(date_ref=date(2025, 6, 1), retry_policy=cls_retry_policy).read()
```

Para tornar a diferença **permanente** para uma tabela, ajuste o `_RETRY_POLICY` na classe daquele
reader — o `RetryPolicy` é um *value object* imutável, então declarar um por tabela é seguro e
explícito.

---

## Exemplos

### Ler o patrimônio líquido de um mês

```python
from decimal import Decimal
from datetime import date
from filings_cvm import InfMensalFidcTabIVReader

pl = InfMensalFidcTabIVReader(date_ref=date(2025, 6, 1)).read()
pl["PL"] = pl["TAB_IV_A_VL_PL"].dropna().map(Decimal)   # texto exato → Decimal
```

### Número de cotistas por classe/série (tabela longa)

```python
from datetime import date
from filings_cvm import InfMensalFidcTabX1Reader

cotistas = InfMensalFidcTabX1Reader(date_ref=date(2025, 6, 1)).read()
# muitas linhas por fundo — uma por TAB_X_CLASSE_SERIE / ID_SUBCLASSE.
```

### Persistir o dump bruto (camada *bronze*) uma vez para os 17

```python
from datetime import date
from pathlib import Path
from filings_cvm import InfMensalFidcTabIReader

# Um download; o ZIP e os 17 CSVs ficam em disco para os outros readers.
InfMensalFidcTabIReader(
    date_ref=date(2025, 6, 1),
    path_raw=Path("/data/bronze/cvm/inf_mensal_fidc/202506"),
).read()
```

Cada `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou
`ValueError` (o ZIP não contém o membro esperado do mês) — falha cedo, sem devolver dados
corrompidos.
