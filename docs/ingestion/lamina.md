# **Lâmina FIF — leitura**

Leitura (← CVM) do membro `lamina_fi_AAAAMM.csv` do dump mensal da **Lâmina**
(`lamina_fi_AAAAMM.zip`), publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/FI/DOC/LAMINA/DADOS/).

> **Veja também:** [Referência da API](../api.md) para cada símbolo público · [Uso](../usage.md)
> para instalação e o conceito geral.

---

## Descrição

`LaminaReader` baixa o ZIP mensal, extrai **todos** os membros, lê a **lâmina propriamente dita**,
valida o **contrato** (as 78 colunas obrigatórias + coluna de CNPJ coercível), aplica os **tipos
declarados** — nunca a inferência do pandas — e devolve uma linha por classe de fundo.

É o *fact sheet* que a CVM publica: objetivo, política de investimento, taxas, condições de
resgate, rentabilidade de cinco anos, exemplos de custo e contatos do SAC.

### Dois leitores, o mesmo ZIP

[`LaminaCarteiraReader`](lamina_carteira.md) lê um **membro diferente do mesmo arquivo** — a
alocação por tipo de ativo. Ambos são baixados juntos, então um `path_raw` gravado por qualquer um
dos dois serve ao outro sem novo *download*.

### Por que `QUOTE_NONE` é essencial aqui

Os campos de texto livre (`OBJETIVO`, `POLIT_INVEST`, `TAXA_ADM_OBS`, …) contêm aspas `"` soltas e
desbalanceadas. Com o *quoting* padrão do pandas, uma dessas aspas abre um campo que engole o
delimitador e o fim da linha, **fundindo dois registros em um** — no `lamina_fi_202504.csv` real
isso produz uma linha de 142 campos e um `ParserError`. Com `QUOTE_NONE`, as 1.325 linhas são lidas
com exatamente 78 campos cada. A CVM não emite *quoting* algum, e o delimitador nunca aparece
dentro de um campo.

| Coluna | Tipo | Observação |
|--------|------|-----------|
| `DT_COMPTC`, `DT_INI_DESPESA`, `DT_FIM_DESPESA`, `DT_INI_ATIV_5ANO` | `date` | Vazios viram `NaT`. |
| `ID_SUBCLASSE` | `str` | Preenchido em apenas 5 das 1.324 linhas de 2025-04; vazio permanece nulo. |
| `CNPJ_FUNDO_CLASSE` | `str` | Mascarado na origem; deve ter ao menos um CNPJ válido. |
| Todas as demais (74) | `str` | Texto exato da CVM — **nunca `float`**. Inclui `VL_PATRIM_LIQ`, `TAXA_ADM`, `PR_*`. |

O mapa de tipos é **derivado do contrato**, não redigitado, de modo que os dois não podem divergir.

---

## Exemplos

### Ler o mês de referência

```python
from datetime import date

from filings_cvm.ingestion import LaminaReader

df_ = LaminaReader(date_ref=date(2025, 4, 15)).read()

print(df_[["DENOM_SOCIAL", "TAXA_ADM", "VL_PATRIM_LIQ"]].head())
```

### Converter valores no ponto de cálculo

```python
from decimal import Decimal

# As colunas monetárias vêm como texto exato; converta apenas onde for calcular.
df_["PL"] = df_["VL_PATRIM_LIQ"].dropna().map(Decimal)
```

### Persistir o artefato bruto (camada *bronze*)

```python
from pathlib import Path

df_ = LaminaReader(
    date_ref=date(2025, 4, 15),
    path_raw=Path("/data/bronze/cvm/lamina/202504"),
).read()
```

O ZIP e **todos** os CSVs extraídos são mantidos — não só o membro lido — para que a
[carteira](lamina_carteira.md) reproduza os mesmos bytes.

### Timeout

```python
df_ = LaminaReader(date_ref=date(2025, 4, 15)).read(int_timeout_s=60)
```

O `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou
`ValueError` (o ZIP não contém o membro `lamina_fi_AAAAMM.csv`) — falha cedo, sem devolver dados
corrompidos.
