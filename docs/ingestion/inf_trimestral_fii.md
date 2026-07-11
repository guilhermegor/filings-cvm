# **Informe Trimestral FII — leitura**

Leitura (← CVM) do **Informe Trimestral dos FII** (`inf_trimestral_fii_AAAA.zip`), publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/FII/DOC/INF_TRIMESTRAL/DADOS/).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md) ·
> o [Informe Mensal FII](inf_mensal_fii.md) e o [DFIN FII](dfin_fii.md).

---

## ⚠️ Particionado por **ano**, não por trimestre

Apesar de ser o informe **trimestral**, o artefato é anual: `inf_trimestral_fii_2025.zip` traz os
quatro trimestres de 2025 (`Data_Referencia` é o fim do trimestre). O `date_ref` do reader
seleciona o **ano** — o mês e o dia são ignorados. Para um único trimestre, filtre o `DataFrame`
por `Data_Referencia`.

---

## Descrição

`inf_trimestral_fii_AAAA.zip` traz **16 membros**, cada um com o seu reader. Todos são chaveados por
`CNPJ_Fundo_Classe` + `Data_Referencia` + `Versao`:

| Reader | Membro | Conteúdo |
|--------|--------|----------|
| `InfTrimestralFiiGeralReader` | `geral` | Cadastro do fundo e administrador. |
| `InfTrimestralFiiComplementoReader` | `complemento` | Vencimentos e indexadores da carteira, seguros, ativos de liquidez. |
| `InfTrimestralFiiAtivoReader` | `ativo` | Valores mobiliários e outros ativos (um por linha). |
| `InfTrimestralFiiAtivoGarantiaRentabilidadeReader` | `ativo_garantia_rentabilidade` | Ativos com garantia de rentabilidade. |
| `InfTrimestralFiiDireitoReader` | `direito` | Direitos reais sobre imóveis. |
| `InfTrimestralFiiImovelReader` | `imovel` | Imóveis do fundo (área, vacância, locação, obras). |
| `InfTrimestralFiiImovelDesempenhoReader` | `imovel_desempenho` | Justificativas de desempenho abaixo do previsto. |
| `InfTrimestralFiiImovelRendaAcabadoContratoReader` | `imovel_renda_acabado_contrato` | Contratos de imóveis de renda acabados. |
| `InfTrimestralFiiImovelRendaAcabadoInquilinoReader` | `imovel_renda_acabado_inquilino` | Inquilinos (o maior membro). |
| `InfTrimestralFiiTerrenoReader` | `terreno` | Terrenos do fundo. |
| `InfTrimestralFiiAquisicaoImovelReader` | `aquisicao_imovel` | Imóveis adquiridos no trimestre. |
| `InfTrimestralFiiAquisicaoTerrenoReader` | `aquisicao_terreno` | Terrenos adquiridos no trimestre. |
| `InfTrimestralFiiAlienacaoImovelReader` | `alienacao_imovel` | Imóveis alienados (com `Data_Alienacao`). |
| `InfTrimestralFiiAlienacaoTerrenoReader` | `alienacao_terreno` | Terrenos alienados (com `Data_Alienacao`). |
| `InfTrimestralFiiRentabilidadeEfetivaReader` | `rentabilidade_efetiva` | Rentabilidade efetiva por mês do trimestre. |
| `InfTrimestralFiiResultadoContabilFinanceiroReader` | `resultado_contabil_financeiro` | Demonstração de resultado (contábil × financeiro, ~95 colunas). |

Os 16 baixam o **mesmo** ZIP anual, então um `path_raw` gravado por qualquer um serve aos outros.

**Sem chave única.** A maioria dos membros é **longa** — uma linha por ativo / imóvel / contrato /
inquilino / transação —, então um fundo aparece muitas vezes; nenhum reader deduplica.

### Tipagem

Toda coluna é texto (`str`) exceto as `Data_*`, convertidas para `date` puro (vazios viram `NaT`).
Valores, áreas, quantidades e percentuais mantêm o **texto exato da CVM** — **nunca `float`**.
`CNPJ_Fundo_Classe` é a única coluna validada como CNPJ; `CNPJ_Emissor` (em `ativo`) e
`CNPJ_Administrador` (em `geral`) são identificadores de contraparte, lidos como texto.

### Peculiaridade da CVM (reproduzida *verbatim*)

Em `resultado_contabil_financeiro`, `Outras_Receitas_Depesas_Contabil` /
`Outras_Receitas_Depesas_Financeiro` são **erro de grafia da própria CVM** (de *Despesas*) —
"corrigir" faz o contrato deixar de casar com o arquivo.

---

## Política de retry

Como todo leitor da biblioteca, os 16 seguem o padrão de **`_RETRY_POLICY` por módulo**. Veja
[a visão geral da leitura](index.md#política-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Resultado contábil e financeiro de um trimestre

```python
from datetime import date
from filings_cvm import InfTrimestralFiiResultadoContabilFinanceiroReader

df_ = InfTrimestralFiiResultadoContabilFinanceiroReader(date_ref=date(2025, 6, 15)).read()
df_ = df_[df_["Data_Referencia"] == date(2025, 3, 31)]   # o 1º trimestre
```

### Inquilinos dos imóveis (membro longo)

```python
from datetime import date
from filings_cvm import InfTrimestralFiiImovelRendaAcabadoInquilinoReader

df_ = InfTrimestralFiiImovelRendaAcabadoInquilinoReader(date_ref=date(2025, 6, 15)).read()
# muitas linhas por fundo — um inquilino por linha.
```

### Persistir o dump bruto (camada *bronze*) uma vez para os 16

```python
from datetime import date
from pathlib import Path
from filings_cvm import InfTrimestralFiiGeralReader

InfTrimestralFiiGeralReader(
    date_ref=date(2025, 6, 15),
    path_raw=Path("/data/bronze/cvm/inf_trimestral_fii/2025"),
).read()
```

Cada `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou
`ValueError` (o ZIP não contém o membro daquele ano) — falha cedo, sem devolver dados corrompidos.
