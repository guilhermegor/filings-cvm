# **EVENTUAL FI — leitura**

Leitura (← CVM) do **índice dos documentos eventuais** entregues por fundos e classes
(`eventual_fi_AAAA.csv`), publicado no [portal de dados abertos](https://dados.cvm.gov.br).

> **Ver também:** [Referência da API](../api.md) · [Uso](../usage.md) · o irmão
> [DFIN FII](dfin_fii.md), que é o mesmo *tipo* de artefato e **não compartilha um só nome de
> coluna**.

---

## O que é

Uma linha por **documento entregue** — não o documento. Cada linha traz a identidade do fundo ou
classe, o tipo do documento (`TP_DOC`), as datas de competência e recebimento, o resultado da
auditoria quando existe, e um `LINK_ARQ` apontando para o arquivo.

| | |
|---|---|
| artefato | `eventual_fi_AAAA.csv` — **CSV solto**, não ZIP |
| partição | **por ano** (o `date_ref` seleciona o ano) |
| colunas | **11** |
| linhas (2025) | **186.453** (50,91 MB) |
| série medida | ao menos **2020–2026** |
| coluna de CNPJ | `CNPJ_FUNDO_CLASSE` (100% válido) |
| colunas de data | `DT_COMPTC`, `DT_RECEB` (100% ISO) |
| META | `meta_eventual_fi.txt` — **`.txt` solto** |

Nomenclatura **pós-RCVM 175** (`TP_FUNDO_CLASSE` / `CNPJ_FUNDO_CLASSE` + `ID_SUBCLASSE`), como o
FIAGRO e o FIE — **não** o `CNPJ_FUNDO` pré-175 dos datasets mais antigos deste root.

## As 11 colunas

| coluna | o que é | observação (2025) |
|---|---|---|
| `TP_FUNDO_CLASSE` | tipo do fundo/classe | ex. `CLASSE FIF/FAPI` |
| `CNPJ_FUNDO_CLASSE` | CNPJ | **100% válido**, mascarado |
| `DENOM_SOCIAL` | razão social | |
| `ID_SUBCLASSE` | identificador da subclasse | **96,8% vazia** |
| `DT_COMPTC` | data de competência | data |
| `DT_RECEB` | data de recebimento | data |
| `TP_DOC` | tipo do documento | ex. `SGF ANEXO` |
| `NM_ARQ` | nome do arquivo | **24,4% vazia** |
| `ID_DOC` | identificador do documento | **75,6% vazia**; `int` na META, **fica texto** |
| `LINK_ARQ` | URL do arquivo | devolvida **como texto, não seguida** |
| `RESULTADO_AUDITORIA` | parecer | **83,5% vazia**; ex. `Sem Ressalva` |

---

## ⚠️ Não é cópia do índice irmão — 7 colunas iguais, 0 nomes iguais

`dfin_fii_AAAA.csv` e `eventual_fi_AAAA.csv` são **o mesmo tipo de artefato**: índice anual, em CSV
solto, dos documentos que um fundo entregou. Sete colunas significam exatamente a mesma coisa — e
**nenhuma se chama igual**:

| significado | EVENTUAL | DFIN FII |
|---|---|---|
| tipo do fundo/classe | `TP_FUNDO_CLASSE` | `Tipo_Fundo_Classe` |
| CNPJ | `CNPJ_FUNDO_CLASSE` | `CNPJ_Fundo_Classe` |
| denominação | `DENOM_SOCIAL` | `Nome_Fundo_Classe` |
| data de referência | `DT_COMPTC` | `Data_Referencia` |
| data de entrega | `DT_RECEB` | `Data_Entrega` |
| link do documento | `LINK_ARQ` | `Link_Download` |
| parecer do auditor | `RESULTADO_AUDITORIA` | `Parecer_Auditor` |

Um contrato escrito **por analogia** com o irmão erraria **as 11 colunas** parecendo perfeitamente
razoável. **Paralelismo semântico não é regra de nomenclatura em lugar nenhum deste portal** — a
divergência é pinada por teste **nas duas direções**, e o contrato vem do header real deste
dataset.

---

## ⚠️ `ID_DOC` é `int` na META e fica texto

Identificador não é quantidade. Um tipo numérico apaga **zero à esquerda** em silêncio — o repo já
encontrou exatamente isso no `Codigo_CVM` do CGVN, publicado como `001023`. O teste afirma sobre um
valor com zero à esquerda, porque é justamente o que um `int64` destrói sem erro.

## ⚠️ Vazio é vazio — quatro colunas dependem do tipo de documento

`ID_SUBCLASSE`, `RESULTADO_AUDITORIA`, `ID_DOC` e `NM_ARQ` chegam parcialmente vazias porque cada
uma depende do que foi entregue: um documento só-link não tem nome de arquivo, um fundo sem
subclasse não tem `ID_SUBCLASSE`, e só documento auditado tem parecer. Voltam **vazias**, nunca com
placeholder ou zero — preencher inventaria um fato que a fonte não afirmou.

## ⚠️ A META é `.txt` solto, e a URL não é derivável

`meta_eventual_fi.txt` responde 200; as outras três grafias que este portal usa em outros datasets
(`meta_eventual_fi.zip`, `eventual_fi.zip`, `meta_eventual_fi_txt.zip`) dão **404**. A URL é
constante por dataset e **medida**, jamais construída a partir do nome.

Os 11 campos da META vêm em **ordem alfabética**, que não é a ordem do arquivo real — o **header
segue sendo a fonte da ordem**, e a META a fonte do tipo declarado.

---

## Uso

```python
from datetime import date
from pathlib import Path

from filings_cvm.ingestion.fi import EventualFiReader

# O índice do ano:
df_ = EventualFiReader(date_ref=date(2025, 6, 15)).read()

# Guardando o CSV cru na bronze:
df_ = EventualFiReader(
    date_ref=date(2025, 6, 15),
    path_raw=Path("/data/bronze/cvm/eventual_fi"),
).read()

# Só os documentos auditados sem ressalva:
df_auditados = df_[df_["RESULTADO_AUDITORIA"].notna()]
```
