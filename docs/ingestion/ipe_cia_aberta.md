# **IPE Companhias Abertas — leitura**

Leitura (← CVM) do **índice das Informações Periódicas e Eventuais das companhias abertas**
(`ipe_cia_aberta_AAAA.zip`), publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md) ·
> o [Cadastro de Companhias Abertas](cia_aberta_cad.md), que inaugura o portal root `cia_aberta/`.

---

## ⚠️ Isto é um **índice**, não o documento

Cada linha descreve **um documento** que a companhia entregou à CVM no ano — a data de referência,
a data de entrega, a taxonomia do documento (`Categoria` / `Tipo` / `Especie` / `Assunto`), o
protocolo e a versão, e um **`Link_Download`** apontando para o documento em si, no portal RAD da
CVM. O reader **devolve o link como texto e não o segue**: baixar o documento apontado é trabalho
de camada superior, e o reader continua fino (o mesmo princípio de todos os readers aqui — fazer o
*parse* do artefato que a CVM publica, nada além).

Três notas de forma:

- **Particionado por ano** (`ipe_cia_aberta_2025.zip`) — o `date_ref` seleciona o **ano**.
- É um **ZIP de 1 membro** (`ipe_cia_aberta_AAAA.csv`) — ao contrário do
  [DFIN FII](dfin_fii.md), que é CSV solto. O membro é selecionado por **nome exato**.
- O `CIA_ABERTA/DOC` tem **7 datasets** e o número de membros varia muito entre eles (IPE tem 1,
  VLMO 2, FCA 10) — nenhum deles pode ser escrito presumindo a forma do vizinho.

---

## Descrição

`ipe_cia_aberta_AAAA.csv` tem **13 colunas** (~49,3 mil linhas em 2025):

| Coluna | Conteúdo |
|--------|----------|
| `CNPJ_Companhia` | CNPJ da companhia — ⚠️ veja o placeholder abaixo. |
| `Nome_Companhia` | Denominação. |
| `Codigo_CVM` | Código CVM (**texto exato**, nunca inteiro). |
| `Data_Referencia` | Data de referência do documento. |
| `Categoria` | Categoria (ex.: `Assembleia`, `Comunicado ao Mercado`). |
| `Tipo` | Tipo dentro da categoria (ex.: `AGE`) — **parcialmente preenchido**. |
| `Especie` | Espécie (ex.: `Ata`) — **parcialmente preenchido**. |
| `Assunto` | Assunto livre — **parcialmente preenchido**. |
| `Data_Entrega` | Data de entrega/recebimento. |
| `Tipo_Apresentacao` | Ex.: `AP - Apresentação`. |
| `Protocolo_Entrega` | Protocolo — **parcialmente preenchido**. |
| `Versao` | Versão do documento (texto exato — nunca inteiro). |
| `Link_Download` | URL do documento no RAD da CVM — **devolvido como texto, não seguido**. |

Apenas `Data_Referencia` e `Data_Entrega` são coagidas para `date` (ambas 100% ISO `AAAA-MM-DD` no
arquivo real, e declaradas `date` no META). Todo o resto é **texto exato da fonte**.

**Sem chave única.** Uma companhia entrega muitos documentos por ano; nenhum reader deduplica — o
grão natural é companhia × protocolo × versão.

---

## ⚠️ O CNPJ placeholder `00.000.000/0000-00`

A CVM usa esse valor para **emissores estrangeiros sem CNPJ brasileiro** (ex.: `JBS FOODS
INTERNATIONAL DESIGNATED ACTIVITY COMPANY`). Em 2025 são **44 linhas de 49.277**, e **nenhum CNPJ
malformado**.

O reader **devolve o valor exatamente como publicado** — nunca o "conserta" nem o transforma em
nulo. `CNPJ_Companhia` segue declarado como coluna de CNPJ no contrato porque a checagem exige
**ao menos um** CNPJ válido na coluna, não todos. A consequência (pinada por teste) é uma aresta
conhecida: uma partição hipotética composta **só** de emissores estrangeiros seria rejeitada com
`ContractError`. As partições reais não se aproximam disso.

---

## Uso

```python
from datetime import date
from pathlib import Path

from filings_cvm import IpeCiaAbertaReader

# O ano do date_ref seleciona o dump anual.
df = IpeCiaAbertaReader(date_ref=date(2025, 6, 15)).read()

# Guardar o .zip cru (camada bronze de um datalake) além de devolver o frame:
df = IpeCiaAbertaReader(
    date_ref=date(2025, 6, 15),
    path_raw=Path("/data/bronze/cvm/ipe"),
).read()
```

O frame devolvido carrega, além das 13 colunas da fonte, as seis colunas de
[proveniência](../api.md) (`url`, `updated_at`, `source_key`, `package_version`,
`ingestion_run_id`, `content_hash`).

---

## META

A especificação publicada pela CVM sai em `MetaIpeCiaAbertaReader` (o **38º** Meta reader) — veja
[META](meta.md).

⚠️ A META do IPE é um **`.txt` solto**, quebrando o padrão `.zip` dos seis irmãos do `DOC`. Entre os
7 datasets do `CIA_ABERTA/DOC` a CVM usa **quatro** grafias diferentes de META
(`meta_<ds>_cia_aberta.zip`, `meta_<ds>_cia_aberta_txt.zip` com infixo `_txt`,
**`fca_cia_aberta.zip` sem o prefixo `meta_`**, e este `.txt`). A URL é **constante por dataset e
jamais derivada**: uma regra "derive o nome" daria 404 ou traria a especificação do dataset errado.
