# **FCA Companhias Abertas — leitura**

Leitura (← CVM) do **Formulário Cadastral** das companhias abertas (`fca_cia_aberta_AAAA.zip`),
publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md) ·
> o [IPE](ipe_cia_aberta.md) e o [VLMO](vlmo_cia_aberta.md), as outras fatias do `CIA_ABERTA/DOC`.

---

## Os 10 membros

| reader | membro | cols | linhas (2025) |
|---|---|---|---|
| `FcaCiaAbertaReader` | índice | 9 | 1.301 |
| `FcaCiaAbertaAuditorReader` | `auditor` | 15 | 1.069 |
| `FcaCiaAbertaCanalDivulgacaoReader` | `canal_divulgacao` | 7 | 1.350 |
| `FcaCiaAbertaDepartamentoAcionistasReader` | `departamento_acionistas` | 23 | **0** |
| `FcaCiaAbertaDriReader` | `dri` | 26 | 1.007 |
| `FcaCiaAbertaEnderecoReader` | `endereco` | 21 | 1.436 |
| `FcaCiaAbertaEscrituradorReader` | `escriturador` | 24 | 552 |
| `FcaCiaAbertaGeralReader` | `geral` | 26 | 715 |
| `FcaCiaAbertaPaisEstrangeiroNegociacaoReader` | `pais_estrangeiro_negociacao` | 7 | 83 |
| `FcaCiaAbertaValorMobiliarioReader` | `valor_mobiliario` | 18 | 995 |

**Particionado por ano** — o `date_ref` seleciona o **ano**. Os 10 readers baixam o **mesmo**
arquivo, então um `path_raw` escrito por um serve os outros.

---

## ⚠️ O índice não segue a convenção de nomes dos próprios satélites

| | índice | os 9 satélites |
|---|---|---|
| CNPJ | `CNPJ_CIA` | `CNPJ_Companhia` |
| data de referência | `DT_REFER` | `Data_Referencia` |
| entrega | `DT_RECEB` | — |
| denominação | `DENOM_CIA` | `Nome_Empresarial` |
| id do documento | `ID_DOC` | `ID_Documento` |
| versão | `VERSAO` | `Versao` |

O índice usa **maiúsculas abreviadas** (o estilo do `cad_cia_aberta.csv`); os satélites usam
**CamelCase por extenso**. Gerar os 10 membros a partir de um molde único **quebra o índice em
silêncio** — os contracts são gerados dos headers reais, um por membro, e a divergência é **pinada
por teste** nas duas direções.

---

## ⚠️ `departamento_acionistas` é header-only

Em 2025 esse membro vem com **cabeçalho e nenhuma linha**. Por isso seu contract declara
**nenhuma coluna de CNPJ**: o check de CNPJ exige um valor **presente** e válido, então num quadro
vazio ele falharia com `ContractError`.

Provado por mutação: acrescentando `("CNPJ_Companhia",)` ao contract, a leitura do membro vazio
levanta `Column 'CNPJ_Companhia' … holds no valid CNPJ`. É a mesma classe de falha dos membros
header-only do CRI — desta vez pega no grounding, não em produção.

---

## ⚠️ Dado pessoal (LGPD)

Estes são os **primeiros CPF do root `cia_aberta/`**:

| coluna | membro | composição em 2025 |
|---|---|---|
| `CPF_Responsavel` | `dri` | **1.003 CPF + 4 CNPJ** (coluna mista) |
| `CPF_Responsavel_Tecnico` | `auditor` | 49 CPF, 1.020 em branco |
| `CPF_CNPJ_Auditor` | `auditor` | 1.069 CNPJ válidos — mas **misto por definição** |

Todos são devolvidos como **texto exato** e **nenhum** é declarado coluna de CNPJ: um CPF não
satisfaz o check de CNPJ, então declarar `CPF_CNPJ_Auditor` quebraria em qualquer ano que traga um
CPF (precedente `cedente_devedor.CNPJ` do CRA/CRI). As **fixtures são header-only** por isso.

O `escriturador` é o único membro com **duas** colunas de CNPJ de fato — `CNPJ_Companhia` e
`CNPJ_Escriturador`, ambas 100% válidas — e as duas são declaradas.

---

## Tipagem

Cada reader coage **as suas próprias** colunas de data — de 1 (`canal_divulgacao`, `endereco`) a
**9** (`geral`). Todas chegam 100% ISO ou em branco, e **branco vira `NaT`** (não levanta):
`auditor.Data_Fim_Atuacao_Responsavel_Tecnico` é 100% vazia, e a maioria das 9 do `geral` é
parcialmente vazia. Todo o restante é **texto exato da fonte**.

---

## Uso

```python
from datetime import date
from pathlib import Path

from filings_cvm import FcaCiaAbertaGeralReader, FcaCiaAbertaValorMobiliarioReader

# Dados gerais de registro (9 colunas de data):
df_geral = FcaCiaAbertaGeralReader(date_ref=date(2025, 6, 15)).read()

# Valores mobiliários emitidos, guardando o .zip cru na camada bronze:
df_vm = FcaCiaAbertaValorMobiliarioReader(
    date_ref=date(2025, 6, 15),
    path_raw=Path("/data/bronze/cvm/fca"),
).read()
```

O frame devolvido carrega, além das colunas da fonte, as seis colunas de
[proveniência](../api.md).

---

## META

A especificação da CVM sai em `MetaFcaCiaAbertaReader` (o **40º** Meta reader) — veja
[META](meta.md). Seus 10 contadores de campo (9/15/7/23/26/21/24/26/7/18) batem exatamente com os
headers reais, então a META confirma a forma de cada membro de forma independente.

⚠️ **É o caso mais forte do portal para "a URL da META é constante por dataset e jamais derivada":**
o arquivo é **`fca_cia_aberta.zip`** — o único META do portal publicado **sem o prefixo `meta_`** —
enquanto os 10 membros internos *são* prefixados `meta_fca_cia_aberta*`. As duas derivações óbvias
dão **404** (`meta_fca_cia_aberta.zip` e `meta_fca_cia_aberta.txt`), enquanto o dataset vizinho
`CIA_ABERTA/CAD` **serve** `meta_cad_cia_aberta.txt` normalmente. O prefixo não é política do
portal: varia por dataset.
