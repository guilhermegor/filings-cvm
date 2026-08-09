# **Extrato FI — leitura**

Leitura (← CVM) do **Extrato das Informações sobre o Fundo**: as condições cadastrais e a política
de investimento declaradas por fundo/classe — prazos de conversão e pagamento, taxas (administração,
performance, ingresso, saída), uso de derivativos e os **limites mínimo/máximo por tipo de ativo**
(as ~60 colunas `PR_*_MIN`/`PR_*_MAX`). Fonte: dataset
[`FI/DOC/EXTRATO`](https://dados.cvm.gov.br/dataset/fi-doc-extrato).

> **Veja também:** [Referência da API](../api.md) · [META](meta.md) · [Proveniência](index.md).

---

## ⚠️⚠️ O dataset publica DOIS artefatos, não uma série

A listagem do diretório entrega o que os nomes escondem:

| artefato | forma | grão | reader |
|---|---|---|---|
| `extrato_fi_AAAA.csv` | CSV solto, **anual** (2015–2026) | **toda** entrega do ano | `ExtratoFiReader` · `ExtratoFiPre2020Reader` |
| `extrato_fi.csv` | CSV solto, **URL fixa, sem ano** | **o último extrato de cada fundo** | `ExtratoFiSnapshotReader` |

### O `extrato_fi.csv` é um SNAPSHOT, não o acumulado

É a leitura que o nome sem partição convida — e está errada. **Medido:**

- **38.454 linhas / 38.454 `CNPJ_FUNDO_CLASSE` distintos** ⇒ exatamente **uma linha por
  fundo/classe**.
- O `DT_COMPTC` cobre 2015–2026 porque cada fundo carrega a data do *seu* último extrato — não
  porque o arquivo seja a série acumulada.
- **Toda** linha dele existe também no arquivo anual correspondente (`0` linhas exclusivas do
  snapshot, conferido em 2025 e 2026), enquanto os anuais têm muito mais (2025: **13.590** linhas
  contra **8.455** datadas de 2025 no snapshot).
- "É o **mais recente**" foi **verificado**: nos **2.469** fundos com mais de uma entrega em 2025, a
  data do snapshot é o máximo do ano ou posterior — **zero** contraexemplos.

> ⚠️ **É o único artefato do acervo com chave única — e ela é DOCUMENTADA, não imposta.** Todos os
> outros readers dizem "nenhuma chave única é afirmada"; aqui *uma linha por `CNPJ_FUNDO_CLASSE`* é
> propriedade **medida da fonte**. O `read()` **não** valida: uma duplicata futura seria mudança na
> CVM, que é trabalho do job de deriva detectar, não motivo para engordar o reader. E **não** vale
> para o `ExtratoFiReader`, cujo grão é a entrega.

A CVM sobrescreve o snapshot no lugar, então só um `path_raw` persistido guarda o que ele dizia
naquele dia.

## ⚠️⚠️ A série anual tem dois schemas — e o corte NÃO é a RCVM 175

| regime | anos | colunas | bloco-chave |
|---|---|---|---|
| pré-2020 | 2015–**2019** | **116** | `CNPJ_FUNDO` |
| 2020 em diante | **2020**–2026 | **117** | `TP_FUNDO_CLASSE` + `CNPJ_FUNDO_CLASSE` |

É **a mesma troca de colunas** do [Perfil Mensal](perfil_mensal_fi.md) — mas lá o corte é `202312` e
aqui é **2020**, enquanto a **Resolução CVM 175 é de dezembro de 2022**. Logo a norma **não pode**
ser a causa aqui: a CVM chegou às mesmas colunas duas vezes, por caminhos e datas diferentes.

> ⚠️ **Por isso o reader se chama `ExtratoFiPre2020Reader`, e não `Pre175`.** Nome é afirmação;
> copiar o nome do dataset vizinho afirmaria uma causa que as datas desmentem. O corte se **mede nos
> headers publicados**, jamais se deduz da data da norma — e um teste fixa isso.

As outras **115 colunas são idênticas**, posição por posição, então derivar um contrato do outro
acerta 115 de 116 nomes. Cada um é gerado do **seu próprio** header e pinado a
`tests/fixtures/extrato_fi/`, com a divergência afirmada nas duas direções.

Pedir a um reader um ano do outro regime levanta `ValueError` **nomeando o irmão**, antes do
download. O `date_ref` padrão é **hoje** no regime aberto e **2019** no encerrado — um reader cujo
único comportamento sem argumentos é levantar não é construtível por chamador genérico nenhum.

## Tipagem

**Só `DT_COMPTC` vira `datetime.date`** — a META declara exatamente **um** campo `date` entre os
117. Todo o resto é **texto exato**: são **74 `numeric` + 4 `decimal` + 4 `int`**, e algumas chegam
com **12 casas decimais** (`TAXA_PERFM` = `0.010000000000`), escala que um `float` destrói em
silêncio.

> ⚠️ **`PRAZO` parece data e não é.** É `varchar` na META e traz valores como `01/03/2033` —
> `DD/MM/YYYY`. Coagir misparsearia dia/mês; fica texto, como publicado.

> ⚠️ `INF_TAXA_PERFM` é prosa livre com `%` e vírgula decimal
> (`% a superar: 35% CDI + 65 % IBrX + 0,755%`). Os arquivos contêm aspas, lidas **literalmente**
> (`QUOTE_NONE`) — nenhuma linha ragged nos três artefatos, medido.

## META

`meta_extrato_fi.txt` — `.txt` solto e **único arquivo do `META/`** (medido pela listagem). Os
**117 campos batem exatamente** com o header atual (zero de cada lado), então ele descreve o anual
de 2020+ e o snapshot, mas **não** o contrato pré-2020 de 116 colunas — esse é pinado ao seu próprio
header, e o job de deriva registra a exclusão para não repetir a mesma linha explicada toda semana.

## Uso

```python
from datetime import date
from pathlib import Path

from filings_cvm.ingestion.fi import (
    ExtratoFiPre2020Reader,
    ExtratoFiReader,
    ExtratoFiSnapshotReader,
)

# Uma linha por fundo: o extrato mais recente de cada um
df_ = ExtratoFiSnapshotReader().read()
print(df_[["CNPJ_FUNDO_CLASSE", "DT_COMPTC", "TAXA_ADM", "TAXA_PERFM"]].head())

# Todas as entregas de um ano (2020+)
df_2025 = ExtratoFiReader(date_ref=date(2025, 6, 15)).read()

# Série histórica (2015–2019)
df_2019 = ExtratoFiPre2020Reader(date_ref=date(2019, 6, 15)).read()
print(df_2019[["CNPJ_FUNDO", "DT_COMPTC"]].head())

# Guardar os bytes brutos para a bronze de um datalake
df_ = ExtratoFiSnapshotReader(path_raw=Path("/data/bronze")).read()
```
