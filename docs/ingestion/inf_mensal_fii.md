# **Informe Mensal FII — leitura**

Leitura (← CVM) do **Informe Mensal dos FII** (`inf_mensal_fii_AAAA.zip`), publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/FII/DOC/INF_MENSAL/DADOS/).
Inaugura o *portal root* `fii/` da biblioteca (irmão de `fi/` e `fidc/`).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## ⚠️ O dump é particionado por **ano**, não por mês

Apesar de ser o informe **mensal**, o artefato é anual: `inf_mensal_fii_2025.zip` traz **os doze
meses de 2025** (uma linha por fundo por mês, com `Data_Referencia` no primeiro dia do mês). O
`date_ref` do reader seleciona portanto o **ano** — o mês e o dia são ignorados.

É a pegadinha que o nome convida: os dumps mensais de FI e FIDC são particionados por `AAAAMM`,
este **não**. Para um único mês, filtre o `DataFrame` devolvido por `Data_Referencia`.

```python
from datetime import date
from filings_cvm import InfMensalFiiComplementoReader

df_ = InfMensalFiiComplementoReader(date_ref=date(2025, 6, 15)).read()   # baixa o ANO de 2025
junho = df_[df_["Data_Referencia"] == date(2025, 6, 1)]                  # filtre o mês aqui
```

---

## Descrição

`inf_mensal_fii_AAAA.zip` traz **3 membros**, cada um com o seu reader. Todos são chaveados por
`CNPJ_Fundo_Classe` + `Data_Referencia` + `Versao`:

| Reader | Membro | Conteúdo |
|--------|--------|----------|
| `InfMensalFiiGeralReader` | `inf_mensal_fii_geral` | Cadastro do fundo: mandato, segmento, gestão, mercados de negociação, e o administrador (nome, CNPJ, endereço, contatos). 37 colunas. |
| `InfMensalFiiAtivoPassivoReader` | `inf_mensal_fii_ativo_passivo` | Balanço do mês: necessidades de liquidez, ativos investidos (imóveis, valores mobiliários, cotas de fundos), valores a receber e o passivo. 52 colunas. |
| `InfMensalFiiComplementoReader` | `inf_mensal_fii_complemento` | Cotistas por tipo de investidor, patrimônio líquido, valor patrimonial da cota e os percentuais do mês (rentabilidade efetiva/patrimonial, *dividend yield*, amortização). 30 colunas. |

Os 3 baixam o **mesmo** ZIP anual, então um `path_raw` gravado por qualquer um serve aos outros.

**Sem chave única.** O grão é (fundo, mês, versão): um fundo que **reenviou** um mês aparece mais de
uma vez para ele. Nenhum reader deduplica — filtre por `Versao` se quiser apenas o último envio.

### Tipagem

Toda coluna é texto (`str`) exceto as `Data_*`, convertidas para `date` puro (vazios viram `NaT` —
`Data_Prazo_Duracao` é vazia na maioria dos fundos). Valores monetários, quantidades e percentuais
mantêm o **texto exato da CVM** — **nunca `float`** —, para conversão a `Decimal` no ponto de cálculo.

### Peculiaridades das colunas da CVM (reproduzidas *verbatim*)

Os contratos reproduzem os nomes **exatamente** como a CVM publica, com os defeitos dela — "corrigir"
faz o contrato deixar de casar com o arquivo:

- `Numero_Cotistas_Entidade_Fechada_Previdência_Complementar` — **acentuado** (`ê`), ao contrário
  das colunas irmãs.
- `Outros_Valores_Mobliarios` e `Provisoes_Contigencias` — **erros de grafia da própria CVM**
  (de *Mobiliários* / *Contingências*).

---

## Política de retry

Como todo leitor da biblioteca, os 3 seguem o padrão de **`_RETRY_POLICY` por módulo**: cada um
declara a sua paciência (padrão: 5 tentativas, *backoff* exponencial limitado) e aceita um
`retry_policy=` por instância que a sobrescreve. Veja
[a visão geral da leitura](index.md#política-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Patrimônio líquido e rentabilidade de um mês

```python
from decimal import Decimal
from datetime import date
from filings_cvm import InfMensalFiiComplementoReader

df_ = InfMensalFiiComplementoReader(date_ref=date(2025, 6, 15)).read()
df_ = df_[df_["Data_Referencia"] == date(2025, 6, 1)]
df_["PL"] = df_["Patrimonio_Liquido"].dropna().map(Decimal)   # texto exato → Decimal
```

### Composição do ativo

```python
from datetime import date
from filings_cvm import InfMensalFiiAtivoPassivoReader

df_ = InfMensalFiiAtivoPassivoReader(date_ref=date(2025, 6, 15)).read()
# Imoveis_Renda_Acabados, CRI, LCI, Total_Investido, Total_Passivo, …
```

### Persistir o dump bruto (camada *bronze*) uma vez para os 3

```python
from datetime import date
from pathlib import Path
from filings_cvm import InfMensalFiiGeralReader

# Um download; o ZIP e os 3 CSVs ficam em disco para os outros readers.
InfMensalFiiGeralReader(
    date_ref=date(2025, 6, 15),
    path_raw=Path("/data/bronze/cvm/inf_mensal_fii/2025"),
).read()
```

Cada `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou
`ValueError` (o ZIP não contém o membro daquele ano) — falha cedo, sem devolver dados corrompidos.
