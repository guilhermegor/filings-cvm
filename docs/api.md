# **Referência da API**

Interface pública da biblioteca. Os serializadores e modelos abaixo são importáveis de
`filings_cvm.submission`, e os leitores de `filings_cvm.ingestion`; os nomes principais também
são reexportados no topo de `filings_cvm`.

> **Veja também:** [Uso](usage.md) · Envio: [Perfil Mensal](submission/perfil_mensal.md), [Informe Diário](submission/informe_diario.md) · Leitura: [Informe Diário FIF](ingestion/informe_diario.md), [CDA FIF](ingestion/cda.md), [Lâmina carteira FIF](ingestion/lamina_carteira.md), [Lâmina FIF](ingestion/lamina.md), [CAD/FI](ingestion/cadastro_fi.md), [Registro RCVM 175](ingestion/registro.md), [CAD/FI histórico](ingestion/cad_fi_hist.md), [Informe Mensal FIDC](ingestion/inf_mensal_fidc.md), [Informe Mensal FII](ingestion/inf_mensal_fii.md), [DFIN FII](ingestion/dfin_fii.md), [Informe Trimestral FII](ingestion/inf_trimestral_fii.md), [Informe Anual FII](ingestion/inf_anual_fii.md), [Informes periódicos FIP](ingestion/inf_fip.md)

---

## Serializador

### `PerfilMensal`

`filings_cvm.submission.PerfilMensal`

Serializa um documento validado para XML compatível com a CVM (padrão Perfil Mensal V4).

#### `export(doc, output_path=None, versao="4.0") -> str | None`

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `doc` | `PerfilMensalDocument` | Documento totalmente validado. |
| `output_path` | `str \| None` | Se informado, grava o arquivo em `windows-1252` e retorna `None`. Caso contrário, retorna a `str` XML (UTF-8 em memória). |
| `versao` | `str` | Versão do formato colocada na tag `VERSAO`. Padrão `"4.0"`. |

```python
from filings_cvm.submission import PerfilMensal

xml = PerfilMensal().export(doc)                       # retorna str
PerfilMensal().export(doc, output_path="perfil.xml")   # grava arquivo, retorna None
```

Não há acesso à rede — apenas lógica pura e I/O de arquivo na borda.

### `InformeDiario`

`filings_cvm.submission.InformeDiario`

Serializa um documento validado para XML compatível com a CVM (padrão Informe Diário V4).

#### `export(doc, output_path=None, versao="4.0") -> str | None`

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `doc` | `InformeDiarioDocument` | Documento totalmente validado. |
| `output_path` | `str \| None` | Se informado, grava o arquivo em `windows-1252` e retorna `None`. Caso contrário, retorna a `str` XML (UTF-8 em memória). |
| `versao` | `str` | Versão do formato colocada na tag `VERSAO`. Padrão `"4.0"`. |

```python
from filings_cvm.submission import InformeDiario

xml = InformeDiario().export(doc)                          # retorna str
InformeDiario().export(doc, output_path="informe.xml")     # grava arquivo, retorna None
```

O XML usa o namespace `urn:infdiario` e `COD_DOC=1`. Mesma borda de I/O do `PerfilMensal`.

---

## Leitor (ingestion)

### `InformeDiarioReader`

`filings_cvm.ingestion.InformeDiarioReader`

Lê o dump mensal de *open-data* do Informe Diário de fundos (`inf_diario_fi_AAAAMM`) e o devolve
como um `DataFrame` tipado e validado por contrato.

#### `InformeDiarioReader(date_ref=None, path_raw=None, retry_policy=None, cls_logger=None)`

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `date_ref` | `datetime.date \| None` | Qualquer dia do mês de referência (só ano/mês selecionam o dump). Padrão: hoje. O mês corrente pode ainda não estar publicado — use um mês passado para dados completos. |
| `path_raw` | `pathlib.Path \| None` | Diretório onde **persistir** o artefato bruto (o `.zip` baixado e o CSV extraído), para a camada *bronze* de um *datalake*. Criado junto com os pais. Padrão `None`: usa um diretório temporário e descarta tudo. |
| `retry_policy` | `RetryPolicy \| None` | Agenda de retry/backoff do download. Se `None`, usa o `_RETRY_POLICY` do próprio reader (padrão paciente: 5 tentativas). **Ajustável por reader.** |
| `cls_logger` | `LogEmitter \| None` | Emissor de log injetável (`log_message(msg, level)`). Padrão: um `LogEmitter` sobre a stdlib. |

#### `read(int_timeout_s=30) -> pd.DataFrame`

Baixa, descompacta e faz o parse do mês de referência. Valida o contrato (colunas obrigatórias +
coluna de CNPJ coercível) antes de aplicar os tipos declarados. Colunas monetárias são mantidas
como **texto exato** (nunca `float`); `DT_COMPTC` vira `date`; `NR_COTST` usa `Int64` (nulável).

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `int_timeout_s` | `int` | Timeout de socket do download, em segundos. Padrão `30`. |

Levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou `ValueError`
(o ZIP não contém CSV).

```python
from datetime import date

from filings_cvm.ingestion import InformeDiarioReader

df_ = InformeDiarioReader(date_ref=date(2025, 1, 15)).read()
```

### `CdaReader`

`filings_cvm.ingestion.CdaReader`

Lê o dump mensal de *open-data* do CDA (`cda_fi_AAAAMM`), consolida os blocos de ativos
`BLC_1`…`BLC_8` numa única granularidade (fundo × data × ativo) e traz o `VL_PATRIM_LIQ` do fundo
junto de cada posição, via *left join* do membro `PL`.

#### `CdaReader(date_ref=None, path_raw=None, retry_policy=None, cls_logger=None)`

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `date_ref` | `datetime.date \| None` | Qualquer dia do mês de referência. Padrão: hoje. |
| `path_raw` | `pathlib.Path \| None` | Diretório onde **persistir** o artefato bruto (o `.zip` e todos os CSVs extraídos). Padrão `None`: diretório temporário, descartado. |
| `retry_policy` | `RetryPolicy \| None` | Agenda de retry/backoff do download. Se `None`, usa o `_RETRY_POLICY` do próprio reader (padrão paciente: 5 tentativas). **Ajustável por reader.** |
| `cls_logger` | `LogEmitter \| None` | Emissor de log injetável. Recebe o `warning` de cobertura do `PL`. |

#### `read(int_timeout_s=30) -> pd.DataFrame`

Devolve uma linha por posição em carteira, com a coluna sintética `BLOCO` (`BLC_1`…`BLC_8`) e a
coluna `VL_PATRIM_LIQ`. As colunas específicas de um bloco ficam nulas nas linhas dos demais. O
membro `cda_fie` é ignorado — é um *layout* distinto.

Se um fundo da carteira não constar de `PL`, o `VL_PATRIM_LIQ` fica nulo e o leitor **emite um
`warning` nomeando os CNPJs** em vez de falhar — você não perde as demais linhas boas do mês.

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `int_timeout_s` | `int` | Timeout de socket do download, em segundos. Padrão `30`. |

Levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato), `ValueError` (o ZIP
não contém bloco `BLC_*` ou membro `PL`) ou `pandas.errors.MergeError` (o `PL` não tem uma linha
por fundo/data).

```python
from datetime import date
from decimal import Decimal

from filings_cvm.ingestion import CdaReader

df_ = CdaReader(date_ref=date(2025, 4, 15)).read()
df_["PCT_PL"] = df_["VL_MERC_POS_FINAL"].map(Decimal) / df_["VL_PATRIM_LIQ"].map(Decimal)
```

### `LaminaCarteiraReader`

`filings_cvm.ingestion.LaminaCarteiraReader`

Lê o membro `lamina_fi_carteira_AAAAMM` do dump mensal da Lâmina (`lamina_fi_AAAAMM.zip`) e devolve
a alocação de cada fundo **por tipo de ativo**. Complementa o `CdaReader`: este traz o percentual
por classe de ativo, aquele a posição título a título.

#### `LaminaCarteiraReader(date_ref=None, path_raw=None, retry_policy=None, cls_logger=None)`

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `date_ref` | `datetime.date \| None` | Qualquer dia do mês de referência. Padrão: hoje. |
| `path_raw` | `pathlib.Path \| None` | Diretório onde **persistir** o artefato bruto (o `.zip` e todos os CSVs extraídos, não só o membro lido). Padrão `None`: diretório temporário, descartado. |
| `retry_policy` | `RetryPolicy \| None` | Agenda de retry/backoff do download. Se `None`, usa o `_RETRY_POLICY` do próprio reader (padrão paciente: 5 tentativas). **Ajustável por reader.** |
| `cls_logger` | `LogEmitter \| None` | Emissor de log injetável. |

#### `read(int_timeout_s=30) -> pd.DataFrame`

Devolve uma linha por fundo × `TP_ATIVO`, com `PR_PL_ATIVO` — o percentual **sinalizado** do
patrimônio líquido, como texto exato da CVM. Os totais por fundo **não** somam 100: alavancagem e
posições vendidas são comuns (em 2025-04, de -37,08 a 1123,00). Os membros irmãos do ZIP
(`lamina_fi_*`, `lamina_fi_rentab_*`) são ignorados.

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `int_timeout_s` | `int` | Timeout de socket do download, em segundos. Padrão `30`. |

Levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou `ValueError` (o ZIP
não contém o membro `lamina_fi_carteira_*`).

```python
from datetime import date
from decimal import Decimal

from filings_cvm.ingestion import LaminaCarteiraReader

df_ = LaminaCarteiraReader(date_ref=date(2025, 4, 15)).read()
df_["PCT"] = df_["PR_PL_ATIVO"].map(Decimal)
```

### `LaminaReader`

`filings_cvm.ingestion.LaminaReader`

Lê o membro `lamina_fi_AAAAMM` do dump mensal da Lâmina (`lamina_fi_AAAAMM.zip`) — a lâmina
propriamente dita — e devolve uma linha por classe de fundo, com as suas **78 colunas**. Lê um
membro **diferente** do mesmo ZIP que o `LaminaCarteiraReader`.

#### `LaminaReader(date_ref=None, path_raw=None, retry_policy=None, cls_logger=None)`

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `date_ref` | `datetime.date \| None` | Qualquer dia do mês de referência. Padrão: hoje. |
| `path_raw` | `pathlib.Path \| None` | Diretório onde **persistir** o artefato bruto (o `.zip` e todos os CSVs extraídos). Padrão `None`: diretório temporário, descartado. |
| `retry_policy` | `RetryPolicy \| None` | Agenda de retry/backoff do download. Se `None`, usa o `_RETRY_POLICY` do próprio reader (padrão paciente: 5 tentativas). **Ajustável por reader.** |
| `cls_logger` | `LogEmitter \| None` | Emissor de log injetável. |

#### `read(int_timeout_s=30) -> pd.DataFrame`

Devolve uma linha por classe de fundo. As quatro colunas `DT_*` viram `datetime.date` (vazio →
`NaT`); as outras 74 são texto exato da CVM. O arquivo é lido com `QUOTE_NONE`: os campos de texto
livre contêm aspas soltas que, com o *quoting* padrão, fundem dois registros.

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `int_timeout_s` | `int` | Timeout de socket do download, em segundos. Padrão `30`. |

Levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou `ValueError` (o ZIP
não contém o membro `lamina_fi_AAAAMM.csv`).

```python
from datetime import date

from filings_cvm.ingestion import LaminaReader

df_ = LaminaReader(date_ref=date(2025, 4, 15)).read()
print(df_[["DENOM_SOCIAL", "TAXA_ADM", "VL_PATRIM_LIQ"]].head())
```

### `CadastroFiReader`

`filings_cvm.ingestion.CadastroFiReader`

Lê `cad_fi.csv`, o **retrato do estado atual** do cadastro de fundos. É o único leitor **sem
`date_ref`**: o artefato não é particionado por mês.

#### `CadastroFiReader(path_raw=None, retry_policy=None, cls_logger=None)`

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `path_raw` | `pathlib.Path \| None` | Diretório onde **persistir** o retrato. A CVM sobrescreve o arquivo no lugar, então o que não for gravado **não pode ser recuperado**. |
| `retry_policy` | `RetryPolicy \| None` | Agenda de retry/backoff do download. Se `None`, usa o `_RETRY_POLICY` do próprio reader (padrão paciente: 5 tentativas). **Ajustável por reader.** |
| `cls_logger` | `LogEmitter \| None` | Emissor de log injetável. |

#### `read(int_timeout_s=60) -> pd.DataFrame`

Devolve uma linha por entrada do cadastro (46.809 × 41 hoje). **Não é indexado por
`CNPJ_FUNDO`**: um fundo mantém o CNPJ ao migrar de regime e reaparece com novo `TP_FUNDO` e
`CD_CVM`, então um `merge` só por essa coluna multiplica linhas. As nove colunas `DT_*` viram
`datetime.date` (vazio → `NaT`); as demais são texto exato. `SIT` é `CANCELADA` na maioria das
linhas — filtre antes de tratar como fundos vivos.

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `int_timeout_s` | `int` | Timeout de socket, em segundos. Padrão `60` (o arquivo tem ~18 MB e não é zipado). |

Levanta `OSError` (falha de download) ou `ContractError` (CSV viola o contrato).

```python
from filings_cvm.ingestion import CadastroFiReader

df_ = CadastroFiReader().read()
ativos = df_[df_["SIT"] == "EM FUNCIONAMENTO NORMAL"]
```

### `RegistroFundoReader` · `RegistroClasseReader` · `RegistroSubclasseReader`

`filings_cvm.ingestion.RegistroFundoReader` · `…RegistroClasseReader` · `…RegistroSubclasseReader`

Lêem os três membros de `registro_fundo_classe.zip` — o cadastro pós-**Resolução CVM 175**, na
hierarquia `fundo → classe → subclasse`. É onde estão os fundos **vivos** (o `registro_fundo` tinha
~34 mil `Em Funcionamento Normal`, contra 22 no `cad_fi.csv`). Página completa:
[Registro RCVM 175](ingestion/registro.md).

#### `RegistroFundoReader(path_raw=None, retry_policy=None, cls_logger=None)` (idem para Classe e Subclasse)

Como o `CadastroFiReader`, **sem `date_ref`** (retrato do estado atual). Os três baixam o **mesmo**
ZIP, então um `path_raw` gravado por qualquer um serve aos outros.

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `path_raw` | `pathlib.Path \| None` | Diretório onde **persistir** o ZIP e os três CSVs. A CVM sobrescreve o arquivo no lugar. |
| `retry_policy` | `RetryPolicy \| None` | Agenda de retry/backoff do download. Se `None`, usa o `_RETRY_POLICY` do próprio reader (padrão paciente: 5 tentativas). **Ajustável por reader.** |
| `cls_logger` | `LogEmitter \| None` | Emissor de log injetável. |

#### `read(int_timeout_s=60) -> pd.DataFrame`

| Leitor | Membro | Colunas | FK |
|--------|--------|---------|-----|
| `RegistroFundoReader` | `registro_fundo.csv` | 21 | — |
| `RegistroClasseReader` | `registro_classe.csv` | 30 | `ID_Registro_Fundo` |
| `RegistroSubclasseReader` | `registro_subclasse.csv` | 14 | `ID_Registro_Classe` |

Os três **não** são unidos num único frame — a hierarquia é um-para-muitos, então um `join`
multiplicaria linhas; junte nas chaves substitutas você mesmo. As colunas `Data_*` viram
`datetime.date`; as demais são texto exato. `ID_Registro_Fundo` **não** é estritamente único
(re-registro entre regimes). Cada `read` levanta `OSError`, `ContractError` ou `ValueError` (membro
ausente).

```python
from filings_cvm.ingestion import RegistroFundoReader, RegistroClasseReader

fundos = RegistroFundoReader().read()
classes = RegistroClasseReader().read()
fc = classes.merge(fundos, on="ID_Registro_Fundo", suffixes=("_classe", "_fundo"))
```

### `CadastroFiHist*Reader` (19 readers)

`filings_cvm.ingestion.CadastroFiHist{Admin,Auditor,Classe,Condom,Controlador,Custodiante,DenomComerc,DenomSocial,DiretorResp,Exclusivo,ExercSocial,Fic,Gestor,PublicoAlvo,Rentab,Sit,TaxaAdm,TaxaPerfm,TribLprazo}Reader`

Os 19 membros de `cad_fi_hist.zip` — o **log de alterações** de cada atributo mutável do cadastro
CAD/FI legado (situação, denominação, taxas, gestor, …), um reader por membro. Página completa:
[CAD/FI histórico](ingestion/cad_fi_hist.md).

Todos têm a mesma assinatura, sem `date_ref` (retrato do estado atual), e baixam o **mesmo** ZIP:

#### `CadastroFiHistSitReader(path_raw=None, retry_policy=None, cls_logger=None)` (idem para os outros 18)

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `path_raw` | `pathlib.Path \| None` | Diretório onde **persistir** o ZIP e os 19 CSVs. Um `path_raw` de qualquer reader serve aos outros. |
| `retry_policy` | `RetryPolicy \| None` | Agenda de retry/backoff do download. Se `None`, usa o `_RETRY_POLICY` do próprio reader (padrão paciente: 5 tentativas). **Ajustável por reader.** |
| `cls_logger` | `LogEmitter \| None` | Emissor de log injetável. |

#### `read(int_timeout_s=60) -> pd.DataFrame`

Devolve o log daquele atributo — muitas linhas por fundo (uma por período de vigência), **sem grão
único**. As colunas `DT_*` viram `datetime.date`; as demais são texto exato. Levanta `OSError`,
`ContractError` ou `ValueError` (membro ausente).

```python
from filings_cvm.ingestion import CadastroFiHistSitReader

sit = CadastroFiHistSitReader().read()
janelas = sit[sit["SIT"] == "EM FUNCIONAMENTO NORMAL"]   # DT_INI_SIT / DT_FIM_SIT
```

### `InfMensalFidcTab*Reader` (17 readers)

`filings_cvm.ingestion.InfMensalFidcTab{I,II,III,IV,V,VI,VII,IX,X,X1,X11,X2,X3,X4,X5,X6,X7}Reader`

Os 17 membros de `inf_mensal_fidc_AAAAMM.zip` — as tabelas do **Informe Mensal FIDC** (Tabelas I–X
mais as sub-tabelas de X), um reader por membro. Inaugura o *portal root* `fidc/`. Página completa:
[Informe Mensal FIDC](ingestion/inf_mensal_fidc.md).

Todos têm a mesma assinatura, **com `date_ref`** (dump particionado por mês), e baixam o **mesmo**
ZIP mensal:

#### `InfMensalFidcTabIReader(date_ref=None, path_raw=None, retry_policy=None, cls_logger=None)` (idem para os outros 16)

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `date_ref` | `datetime.date \| None` | Qualquer dia do mês de referência seleciona o dump `AAAAMM`. Padrão: hoje. |
| `path_raw` | `pathlib.Path \| None` | Diretório onde **persistir** o ZIP e os 17 CSVs. Um `path_raw` de qualquer reader serve aos outros. |
| `retry_policy` | `RetryPolicy \| None` | Agenda de retry/backoff do download. Se `None`, usa o `_RETRY_POLICY` do próprio reader (padrão paciente: 5 tentativas). **Ajustável por tabela** — veja a página. |
| `cls_logger` | `LogEmitter \| None` | Emissor de log injetável. |

#### `read(int_timeout_s=60) -> pd.DataFrame`

Devolve as linhas daquela tabela no mês. `DT_COMPTC` vira `datetime.date`; as demais são texto
exato (monetários/quantidades/percentuais/contagens **nunca `float`**). As sub-tabelas são longas
(muitas linhas por fundo), **sem grão único**. Levanta `OSError`, `ContractError` ou `ValueError`
(membro do mês ausente).

```python
from datetime import date
from filings_cvm import InfMensalFidcTabIVReader, RetryPolicy

pl = InfMensalFidcTabIVReader(date_ref=date(2025, 6, 1)).read()          # padrão do módulo
cls_retry_policy = RetryPolicy(int_max_attempts=10, float_max_wait_s=30.0)
pl = InfMensalFidcTabIVReader(date_ref=date(2025, 6, 1), retry_policy=cls_retry_policy).read()  # override
```

### `InfMensalFii*Reader` (3 readers)

`filings_cvm.ingestion.InfMensalFii{Geral,AtivoPassivo,Complemento}Reader`

Os 3 membros de `inf_mensal_fii_AAAA.zip` — o **Informe Mensal FII**, um reader por membro.
Inaugura o *portal root* `fii/`. Página completa: [Informe Mensal FII](ingestion/inf_mensal_fii.md).

⚠️ **O dump é particionado por ANO, não por mês**, apesar de ser o informe mensal: um
`inf_mensal_fii_2025.zip` traz os doze meses de 2025. O `date_ref` seleciona o **ano** (mês e dia
são ignorados); filtre `Data_Referencia` no frame para um único mês.

#### `InfMensalFiiGeralReader(date_ref=None, path_raw=None, retry_policy=None, cls_logger=None)` (idem para os outros 2)

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `date_ref` | `datetime.date \| None` | Qualquer dia do **ano** de referência — só o ano é lido. Padrão: hoje. O ano corrente é parcial por definição. |
| `path_raw` | `pathlib.Path \| None` | Diretório onde **persistir** o ZIP e os 3 CSVs. Um `path_raw` de qualquer reader serve aos outros. |
| `retry_policy` | `RetryPolicy \| None` | Agenda de retry/backoff do download. Se `None`, usa o `_RETRY_POLICY` do próprio reader (padrão paciente: 5 tentativas). **Ajustável por reader.** |
| `cls_logger` | `LogEmitter \| None` | Emissor de log injetável. |

#### `read(int_timeout_s=60) -> pd.DataFrame`

Devolve as linhas daquele membro no **ano** — todos os doze meses, uma linha por (fundo, mês,
versão). **Sem chave única:** um mês reenviado repete (filtre por `Versao`). As colunas `Data_*`
viram `datetime.date` (vazios → `NaT`); as demais são texto exato. Levanta `OSError`,
`ContractError` ou `ValueError` (membro do ano ausente).

```python
from datetime import date
from filings_cvm import InfMensalFiiComplementoReader

df_ = InfMensalFiiComplementoReader(date_ref=date(2025, 6, 15)).read()   # o ANO de 2025
junho = df_[df_["Data_Referencia"] == date(2025, 6, 1)]
```

### `DfinFiiReader`

`filings_cvm.ingestion.DfinFiiReader`

O **índice** das demonstrações financeiras dos FII (`dfin_fii_AAAA.csv`) — uma linha por documento
entregue. Página completa: [DFIN FII](ingestion/dfin_fii.md).

⚠️ **É um índice, não uma demonstração.** A coluna `Link_Download` aponta para o documento no fnet
da B3; o reader a **devolve como texto e não a segue**. É um **CSV solto** (não ZIP), particionado
por **ano** (`date_ref` seleciona o ano).

#### `DfinFiiReader(date_ref=None, path_raw=None, retry_policy=None, cls_logger=None)`

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `date_ref` | `datetime.date \| None` | Qualquer dia do **ano** de referência — só o ano é lido. Padrão: hoje. |
| `path_raw` | `pathlib.Path \| None` | Diretório onde **persistir** o `.csv` baixado. Padrão `None`: diretório temporário, descartado. |
| `retry_policy` | `RetryPolicy \| None` | Agenda de retry/backoff do download. Se `None`, usa o `_RETRY_POLICY` do próprio reader (padrão paciente: 5 tentativas). |
| `cls_logger` | `LogEmitter \| None` | Emissor de log injetável. |

#### `read(int_timeout_s=60) -> pd.DataFrame`

Devolve uma linha por documento entregue no ano. `Data_Referencia` e `Data_Entrega` viram
`datetime.date`; as demais colunas — incluindo `Link_Download` e `Versao` — são texto exato.
**Sem chave única:** um fundo entrega muitos documentos, e um reenvio repete com `Versao` maior.
Levanta `OSError` ou `ContractError`.

```python
from datetime import date
from filings_cvm import DfinFiiReader

df_ = DfinFiiReader(date_ref=date(2025, 6, 15)).read()   # o ANO de 2025
# df_[["CNPJ_Fundo_Classe", "Data_Referencia", "Versao", "Link_Download"]]
```

### `InfTrimestralFii*Reader` (16 readers)

`filings_cvm.ingestion.InfTrimestralFii{Geral,Complemento,Ativo,AtivoGarantiaRentabilidade,Direito,Imovel,ImovelDesempenho,ImovelRendaAcabadoContrato,ImovelRendaAcabadoInquilino,Terreno,AquisicaoImovel,AquisicaoTerreno,AlienacaoImovel,AlienacaoTerreno,RentabilidadeEfetiva,ResultadoContabilFinanceiro}Reader`

Os 16 membros de `inf_trimestral_fii_AAAA.zip` — o **Informe Trimestral FII**, um reader por membro.
Página completa: [Informe Trimestral FII](ingestion/inf_trimestral_fii.md).

⚠️ **Particionado por ANO, não por trimestre.** O `date_ref` seleciona o **ano**; filtre
`Data_Referencia` no frame para um único trimestre. `CNPJ_Fundo_Classe` é a única coluna validada
como CNPJ.

#### `InfTrimestralFiiGeralReader(date_ref=None, path_raw=None, retry_policy=None, cls_logger=None)` (idem para os outros 15)

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `date_ref` | `datetime.date \| None` | Qualquer dia do **ano** de referência — só o ano é lido. Padrão: hoje. |
| `path_raw` | `pathlib.Path \| None` | Diretório onde **persistir** o ZIP e os 16 CSVs. Um `path_raw` de qualquer reader serve aos outros. |
| `retry_policy` | `RetryPolicy \| None` | Agenda de retry/backoff do download. Se `None`, usa o `_RETRY_POLICY` do próprio reader (padrão paciente: 5 tentativas). |
| `cls_logger` | `LogEmitter \| None` | Emissor de log injetável. |

#### `read(int_timeout_s=60) -> pd.DataFrame`

Devolve as linhas daquele membro no **ano** — todos os quatro trimestres. **Sem chave única:** a
maioria dos membros é longa (um ativo/imóvel/contrato/inquilino/transação por linha). As `Data_*`
viram `datetime.date` (vazios → `NaT`); as demais são texto exato. Levanta `OSError`,
`ContractError` ou `ValueError` (membro do ano ausente).

```python
from datetime import date
from filings_cvm import InfTrimestralFiiImovelReader

df_ = InfTrimestralFiiImovelReader(date_ref=date(2025, 6, 15)).read()   # o ANO de 2025
primeiro_tri = df_[df_["Data_Referencia"] == date(2025, 3, 31)]
```

### `InfAnualFii*Reader` (12 readers)

`filings_cvm.ingestion.InfAnualFii{Geral,Complemento,AtivoAdquirido,AtivoTransacao,AtivoValorContabil,DistribuicaoCotistas,DiretorResponsavel,ExperienciaProfissional,PrestadorServico,Processo,ProcessoSemelhante,RepresentanteCotista}Reader`

Os 12 membros de `inf_anual_fii_AAAA.zip` — o **Informe Anual FII**, um reader por membro. **Com ele
o portal root `fii/` fica completo (4/4).** Página completa:
[Informe Anual FII](ingestion/inf_anual_fii.md).

Particionado por **ano** — aqui a partição é natural (é o informe *anual*). ⚠️ Dois pontos:
`Link_Download_Anexo` (em `complemento`) é **devolvido como texto e não seguido**; e o **`CPF`** (em
`diretor_responsavel` / `representante_cotista`) é **dado pessoal**, lido como texto exato e nunca
validado como CNPJ.

#### `InfAnualFiiGeralReader(date_ref=None, path_raw=None, retry_policy=None, cls_logger=None)` (idem para os outros 11)

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `date_ref` | `datetime.date \| None` | Qualquer dia do **ano** de referência — só o ano é lido. Padrão: hoje. |
| `path_raw` | `pathlib.Path \| None` | Diretório onde **persistir** o ZIP e os 12 CSVs. Um `path_raw` de qualquer reader serve aos outros. |
| `retry_policy` | `RetryPolicy \| None` | Agenda de retry/backoff do download. Se `None`, usa o `_RETRY_POLICY` do próprio reader (padrão paciente: 5 tentativas). |
| `cls_logger` | `LogEmitter \| None` | Emissor de log injetável. |

#### `read(int_timeout_s=60) -> pd.DataFrame`

Devolve as linhas daquele membro no ano. **Sem chave única:** a maioria dos membros é longa (um
ativo/transação/processo/prestador/diretor por linha). As `Data_*` viram `datetime.date` (vazios →
`NaT`); as demais são texto exato. Levanta `OSError`, `ContractError` ou `ValueError` (membro do ano
ausente).

```python
from datetime import date
from filings_cvm import InfAnualFiiProcessoReader

df_ = InfAnualFiiProcessoReader(date_ref=date(2025, 6, 15)).read()   # o ANO de 2025
# uma linha por processo: Juizo, Instancia, Data_Instauracao, Valor_Causa, Chance_Perda…
```

### `InfTrimestralFipReader` · `InfQuadrimestralFipReader` (2 readers)

`filings_cvm.ingestion.InfTrimestralFipReader` · `filings_cvm.ingestion.InfQuadrimestralFipReader`

Os dois informes periódicos dos **FIP** (`inf_trimestral_fip_AAAA.csv`, `inf_quadrimestral_fip_AAAA.csv`),
que **inauguram o portal root `fip/`**. O trimestral é o regime **pré-RCVM 175** (2010–2023); o
quadrimestral o substituiu no **pós-175** (a partir de 2024). Conteúdo quase idêntico — a única
diferença estrutural é o identificador do fundo (`CNPJ_FUNDO` vs `TP_FUNDO_CLASSE` +
`CNPJ_FUNDO_CLASSE`). Página completa: [Informes periódicos FIP](ingestion/inf_fip.md).

CSVs soltos (não ZIP), particionados por **ano** — o `date_ref` seleciona o ano. Apenas `DT_COMPTC`
vira `date`; dinheiro e cota ficam texto exato.

#### `InfTrimestralFipReader(date_ref=None, path_raw=None, retry_policy=None, cls_logger=None)` (idem para o quadrimestral)

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `date_ref` | `datetime.date \| None` | Qualquer dia do **ano** de referência — só o ano é lido. Padrão: hoje. |
| `path_raw` | `pathlib.Path \| None` | Diretório onde **persistir** o CSV bruto (camada *bronze*). |
| `retry_policy` | `RetryPolicy \| None` | Agenda de retry/backoff do download. Se `None`, usa o `_RETRY_POLICY` do próprio reader (padrão paciente: 5 tentativas). |
| `cls_logger` | `LogEmitter \| None` | Emissor de log injetável. |

#### `read(int_timeout_s=60) -> pd.DataFrame`

Devolve uma linha por fundo (ou fundo/classe) por período de competência. **Sem chave única.**
Levanta `OSError` ou `ContractError`.

```python
from datetime import date
from filings_cvm import InfQuadrimestralFipReader

df_ = InfQuadrimestralFipReader(date_ref=date(2024, 8, 15)).read()   # o ANO de 2024
# df_[["CNPJ_FUNDO_CLASSE", "DT_COMPTC", "VL_PATRIM_LIQ", "VL_CAP_INTEGR"]]
```

### `InfMensalFiagroReader` · `InfMensalFiagroSubclasseReader` (2 readers)

`filings_cvm.ingestion.InfMensalFiagroReader` · `filings_cvm.ingestion.InfMensalFiagroSubclasseReader`

Os dois membros do Informe Mensal dos **FIAGRO** (`inf_mensal_fiagro_AAAAMM.zip`), que
**inauguram o portal root `fiagro/`**. `InfMensalFiagroReader` lê o informe proper (133 colunas,
uma linha por classe por mês); `InfMensalFiagroSubclasseReader` lê o desdobramento por subclasse
(6 colunas, longo). Página completa: [Informe Mensal FIAGRO](ingestion/inf_mensal_fiagro.md).

ZIP **particionado por mês** (`AAAAMM`, série a partir de `202505`) — o `date_ref` seleciona o
mês; o membro é escolhido por **nome exato**. Nomenclatura pós-RCVM 175 (chave `CNPJ_Classe`).

#### `InfMensalFiagroReader(date_ref=None, path_raw=None, retry_policy=None, cls_logger=None)` (idem para a subclasse)

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `date_ref` | `datetime.date \| None` | Qualquer dia do **mês** de referência — só ano e mês são lidos. Padrão: hoje. |
| `path_raw` | `pathlib.Path \| None` | Diretório onde **persistir** o ZIP bruto e os CSVs (camada *bronze*). |
| `retry_policy` | `RetryPolicy \| None` | Agenda de retry/backoff do download. Se `None`, usa o `_RETRY_POLICY` do próprio reader (padrão paciente: 5 tentativas). |
| `cls_logger` | `LogEmitter \| None` | Emissor de log injetável. |

#### `read(int_timeout_s=60) -> pd.DataFrame`

Devolve as linhas do mês para o membro. **Sem chave única** (a subclasse é naturalmente longa).
Datas viram `date` (três colunas no informe, uma na subclasse); dinheiro/quantidade/percentual
ficam texto exato. Levanta `OSError`, `ContractError` ou `ValueError`.

```python
from datetime import date
from filings_cvm import InfMensalFiagroReader

df_ = InfMensalFiagroReader(date_ref=date(2025, 6, 1)).read()   # o MÊS 2025-06
# df_[["CNPJ_Classe", "Data_Referencia", "Patrimonio_Liquido", "Valor_Patrimonial_Cotas"]]
```

### `BalanceteFieReader` · `BalancoFieReader` · `MedidasMesFieReader` (3 readers)

`filings_cvm.ingestion.BalanceteFieReader` · `filings_cvm.ingestion.BalancoFieReader` ·
`filings_cvm.ingestion.MedidasMesFieReader`

Os três datasets dos **FIE** (Fundos de Investimento Especialmente constituídos), que **completam o
portal root `fie/`**. Página completa: [FIE](ingestion/fie.md). Não há `FIE/CAD`.

- `BalanceteFieReader` — `balancete_fie_AAAAMM.zip` (ZIP de 1 membro), **mensal** (202401→), balancete
  contábil. Pós-RCVM 175 (`CNPJ_FUNDO_CLASSE`).
- `BalancoFieReader` — `balanco_fie_AAAA.zip` (ZIP de 1 membro), **anual**, balanço patrimonial.
  **Descontinuado em 2020**; pré-175 (`CNPJ_FUNDO`).
- `MedidasMesFieReader` — `medidas_mes_fie_AAAAMM.csv` (CSV solto), **mensal**, patrimônio líquido e
  número de cotistas. `FIE/MEDIDAS` é irmão de `FIE/DOC`.

#### `BalanceteFieReader(date_ref=None, path_raw=None, retry_policy=None, cls_logger=None)` (idem para os outros dois)

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `date_ref` | `datetime.date \| None` | Balancete/medidas: qualquer dia do **mês**; balanço: qualquer dia do **ano**. Padrão: hoje. |
| `path_raw` | `pathlib.Path \| None` | Diretório onde **persistir** o artefato bruto (ZIP ou CSV) da camada *bronze*. |
| `retry_policy` | `RetryPolicy \| None` | Agenda de retry/backoff do download. Se `None`, usa o `_RETRY_POLICY` do próprio reader. |
| `cls_logger` | `LogEmitter \| None` | Emissor de log injetável. |

#### `read(int_timeout_s=60) -> pd.DataFrame`

Devolve as linhas do período. Só `DT_COMPTC` vira `date`; saldos, contagens e códigos ficam texto
exato. Levanta `OSError`, `ContractError` ou (nos balanços) `ValueError` se o membro do ZIP faltar.

```python
from datetime import date
from filings_cvm import BalanceteFieReader

df_ = BalanceteFieReader(date_ref=date(2026, 6, 1)).read()   # o MÊS 2026-06
# df_[["CNPJ_FUNDO_CLASSE", "DT_COMPTC", "CD_CONTA_BALCTE", "VL_SALDO_BALCTE"]]
```

---

## Modelos de schema (Pydantic)

Todos são modelos [Pydantic v2](https://docs.pydantic.dev/) — a validação acontece na
construção. Cada grupo espelha um padrão CVM: `PadrãoXMLPerfil` (V4) e
`PadrãoXMLInfoDiarioNet` (V4).

### Perfil Mensal — documento e cabeçalho

| Modelo | Tag XML | Papel |
|--------|---------|-------|
| `PerfilMensalDocument` | `DOC_ARQ` | Documento completo: `header` + `rows`. |
| `DocumentHeader` | `CAB_INFORM` | Cabeçalho. `dt_compt` no formato `MM/AAAA`; `dt_gerac_arq` no formato `DD/MM/AAAA`. |
| `PerfilMensalRow` | `ROW_PERFIL` | Uma entrada de perfil mensal por classe de fundo. |

**Campos obrigatórios de `PerfilMensalRow`:** `cnpj_fdo` (validado por dígito verificador,
armazenado sem máscara), `nr_client`, `total_recurs_exter`, `total_recurs_br`,
`tot_ativos_p_relac`, `tot_ativos_cred_priv`. Os demais são opcionais.

### Perfil Mensal — blocos e listas

| Modelo | Tag XML | Papel |
|--------|---------|-------|
| `ClientCount` | `NR_CLIENT` | Contagem de clientes por tipo de investidor (16 campos, obrigatórios, ≥ 0). |
| `PatrimonyDistribution` | `DISTR_PATRIM` | Percentual de patrimônio por tipo de cliente (bloco opcional). |
| `VarPercValCota` | `VARIACAO_PERC_VAL_COTA` | Cenário de estresse com fatores primitivos de risco. |
| `PrimitiveRiskFactor` | `FATOR_PRIMIT_RISCO` | Um fator primitivo de risco (IBOVESPA, JUROS-PRE, CUPOM CAMBIAL, DOLAR, OUTROS). |
| `VarOutros` | `VARIACAO_..._N_OUTROS` | Sensibilidade a um fator de risco não padronizado. |
| `NominalRiskBlock` | `VALOR_NOC_TOT_CONTRAT_DERIV_MANT_FDO` | Exposição nocional em derivativos de balcão. |
| `NominalRiskFactor` | `FATOR_RISCO_NOC` | Um fator de risco nocional (pernas long e short). |
| `OtcOperation` | `OPER_CURS_MERC_BALCAO` | Contraparte de balcão sem contraparte central (até 3). |
| `PrivateCreditIssuer` | `EMISSORES_TIT_CRED_PRIV` | Emissor de título de crédito privado (até 3). |
| `PerformanceFeeDetails` | `RESP_VED_REGUL_COBR_TAXA_PERFORM` | Data e valor da cota na última cobrança de taxa de performance. |

### Informe Diário — documento e blocos

| Modelo | Tag XML | Papel |
|--------|---------|-------|
| `InformeDiarioDocument` | `DOC_ARQ` | Documento completo: `header` + `informs` (até 100 fundos). |
| `InformeDiarioHeader` | `CAB_INFORM` | Cabeçalho. `dt_compt` e `dt_gerac_arq` no formato `DD/MM/AAAA`; `COD_DOC=1`. |
| `InformeDiarioInform` | `INFORM` | O informe diário de um fundo. |
| `SignificantShareholder` | `COTST_SIGNIF` | Um cotista com participação ≥ 20% do PL (bloco opcional). |

**Campos de `InformeDiarioInform`:** identifique o fundo por **exatamente um** de `cnpj_fdo`
(classe, validado por dígito verificador) **ou** `cod_subclasse` (subclasse) — informar ambos ou
nenhum levanta `ValidationError`. Obrigatórios: `data_prox_pl` (`DD/MM/AAAA`), `vl_total`,
`vl_quota` (até 12 casas), `patrim_liq`, `captc_dia`, `resg_dia`, `vl_total_sai`, `vl_total_atv`
(monetários, 2 casas) e `nr_cotst` (inteiro ≥ 0). `lista_cotst_signif` é opcional; `pr_cotst`
tem até 4 casas.

---

## Validação e precisão

- **Datas** são validadas por regex (`MM/AAAA` ou `DD/MM/AAAA`).
- **CNPJ/CPF** passam pelos validadores de dígito verificador próprios da biblioteca
  (`_internal.utils.br_identifiers`, cientes do CNPJ alfanumérico de 2026) e são armazenados
  na forma nua, sem máscara — como a CVM espera no XML.
- **Decimais** têm a escala fixada por campo conforme o padrão CVM; precisão excedente é
  **truncada em direção a zero** (`ROUND_DOWN`), nunca arredondada. Passe valores como `str`
  ou `Decimal`, nunca `float`.
- Na serialização, decimais saem com **vírgula** como separador (`10,99`).

---

## Estendendo

Novos padrões da CVM entram como novos módulos:

- O schema compartilhado (neutro em relação à direção) vai em
  `src/filings_cvm/_internal/config/schemas/<padrao>.py`.
- O escritor de envio vai em `src/filings_cvm/submission/<padrao>.py` (uma classe pública por
  arquivo, nomeada como o arquivo).
- Reexporte os símbolos públicos em `filings_cvm/submission/__init__.py` e, quando fizer sentido,
  no `filings_cvm/__init__.py`.

O catálogo completo de padrões (implementados e pendentes) está no `CLAUDE.md` do repositório.
