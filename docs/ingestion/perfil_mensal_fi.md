# **Perfil Mensal FI — leitura**

Leitura (← CVM) do **perfil mensal** dos fundos e classes: composição de cotistas por categoria,
VaR e cenários de estresse, nocionais de derivativos e os blocos de concentração por **comitente** e
por **emissor**. Fonte: `perfil_mensal_fi_AAAAMM.csv`, do dataset
[`FI/DOC/PERFIL_MENSAL`](https://dados.cvm.gov.br/dataset/fi-doc-perfil_mensal).

É o lado da **leitura** do writer [`PerfilMensal`](../api.md) (envio, V4): mesmo padrão regulatório,
**artefato diferente** — o dump aberto, não o XML de envio —, então declara o seu próprio
`FileContract` em vez de reusar o schema Pydantic do writer.

> **Veja também:** [Referência da API](../api.md) · [META](meta.md) · [Proveniência](index.md).

---

## Forma do artefato

| | |
|---|---|
| formato | **CSV solto** (não ZIP), `;`, ISO-8859-1 |
| partição | **por mês** (`_AAAAMM`) — o `date_ref` seleciona ano **e** mês |
| série | `201901` … em diante |
| tamanho | 13,19 MB / 107 colunas / 24.832 linhas em `202506` |
| chave única | **nenhuma é afirmada** |

## ⚠️⚠️ Um padrão de nome, dois schemas

A RCVM 175 trocou o bloco-chave **no meio da série**, sem mudar o nome do arquivo:

| regime | meses | colunas | bloco-chave | reader |
|---|---|---|---|---|
| pré-RCVM 175 | `201901`–**`202311`** | **106** | `CNPJ_FUNDO` | `PerfilMensalPre175Reader` |
| pós-RCVM 175 | **`202312`**– | **107** | `TP_FUNDO_CLASSE` + `CNPJ_FUNDO_CLASSE` | `PerfilMensalReader` |

O corte foi **medido** por busca binária sobre os headers publicados, não deduzido da data da
norma.

**As outras 105 colunas são idênticas** — `pré[1:] == pós[2:]`, posição por posição. É a armadilha
de cópia mais apertada do acervo: escrever um contrato a partir do outro "só arrumando a primeira
coluna" acerta 105 de 106 nomes e passaria em tudo **menos** no header pinado. Por isso são **dois
contracts**, cada um gerado do seu próprio header publicado e pinado a
`tests/fixtures/perfil_mensal_fi/*_header.csv`, com a divergência afirmada nas **duas** direções.

Pedir a um reader um mês do outro regime levanta `ValueError` **nomeando o irmão**, antes de baixar
os 13 MB — um `ContractError` sobre coluna faltando nunca contaria que existe um segundo reader.

```python
>>> PerfilMensalReader(date(2023, 11, 30))
ValueError: PerfilMensalReader covers post-RCVM 175 months 202312-...; 202311 is
outside it — use PerfilMensalPre175Reader for that month
```

O `date_ref` padrão é **hoje** no regime aberto e o **último mês coberto** (`202311`) no encerrado:
um reader cujo único comportamento sem argumentos é levantar não é construtível por chamador
genérico nenhum.

## Tipagem

Só **duas** colunas viram `datetime.date` — `DT_COMPTC` e `DT_COTA_TAXA_PERFM`, ambas `date` na META
e 100% ISO onde preenchidas. **Todo o resto é texto exato**: as **53** colunas `numeric` (escalas
1, 2 e 4) e as **17** `int` preservam o decimal que a CVM publicou, para um `Decimal` decidir a
escala a jusante.

> ⚠️ **As 5 colunas `CENARIO_FPR_*` parecem numéricas e não são.** Trazem valores como `-0,0004` —
> com **vírgula** decimal — misturados a texto livre (`pessimista`, `-`, `n/a`) na mesma coluna, e a
> META as declara `varchar(150)`. Qualquer coerção numérica ou levanta ou corrompe em silêncio.

> ⚠️ **`NR_DIA_CEM_PERC` e `NR_DIA_CINQU_PERC` são `numeric(14,4)`** apesar do prefixo `NR_`, que em
> toda coluna vizinha (`NR_COTST_*`) marca contagem. O prefixo não é o tipo — a META é.

## Dado pessoal: as 6 colunas `CPF_CNPJ_*`

`CPF_CNPJ_COMITENTE_1..3` e `CPF_CNPJ_EMISSOR_1..3` guardam **um CPF ou um CNPJ**. Quem diz qual é a
coluna irmã `PF_PJ_*`, de domínio `PF`/`PJ` — e o caso `PF` **ocorre na fonte** (medido em
`PF_PJ_COMITENTE_2`).

Logo elas ficam **fora de `tuple_cnpj_cols`**: declarar uma passaria num mês todo-PJ e levantaria no
primeiro mês com pessoa física, num ambiente de consumidor. A única coluna de CNPJ é
`CNPJ_FUNDO_CLASSE` (ou `CNPJ_FUNDO`, no regime pré-175). As fixtures de teste são **header-only**.

## Colunas vazias são propriedade do mês

Em `202506`, **seis** colunas chegam 100% vazias — `NR_COTST_ENTID_PREVID_COMPL`,
`PR_COTST_ENTID_PREVID_COMPL`, `NR_DIA_CINQU_PERC`, `NR_DIA_CEM_PERC`, `ST_LIQDEZ`,
`PR_PATRIM_LIQ_CONVTD_CAIXA` — e `DT_COTA_TAXA_PERFM` chega ~84% vazia. **Vazio volta vazio**, sem
placeholder, e a coluna segue com o tipo que o contrato declara: um mês em que ela venha preenchida
não muda nada.

`DT_COTA_TAXA_PERFM` também traz sentinelas **`1900-01-01`/`1901-01-01`**, devolvidas **como
publicadas** — a biblioteca não decide que uma data-sentinela da fonte é nula.

## META

A URL é **`meta_perfil_mensal_fi.txt`** — um `.txt` solto, e o **único arquivo** do `META/` do
dataset (medido pela listagem). As outras três grafias que este portal usa em outros datasets dão
**404** aqui: a URL é constante por dataset e **nunca derivada**.

> ⚠️ **Os 107 campos da META são o header pós-175, exatamente** (zero de cada lado) — não há
> `CNPJ_FUNDO`. Ou seja, **a META não é oráculo do contrato pré-175**; aquele é pinado ao seu
> próprio header publicado. O job de deriva de contrato sabe disso e não compara o reader pré-175
> contra a META, senão reportaria a mesma linha explicada toda semana.

## Uso

```python
from datetime import date

from filings_cvm.ingestion.fi import PerfilMensalPre175Reader, PerfilMensalReader

# Regime atual (202312 em diante)
df_ = PerfilMensalReader(date_ref=date(2025, 6, 15)).read()
print(df_[["CNPJ_FUNDO_CLASSE", "DT_COMPTC", "PR_VAR_CARTEIRA"]].head())

# Série histórica (201901–202311)
df_pre = PerfilMensalPre175Reader(date_ref=date(2023, 6, 15)).read()
print(df_pre[["CNPJ_FUNDO", "DT_COMPTC", "PR_VAR_CARTEIRA"]].head())

# Guardar os bytes brutos para a bronze de um datalake
df_ = PerfilMensalReader(date_ref=date(2025, 6, 15), path_raw=Path("/data/bronze")).read()
```
