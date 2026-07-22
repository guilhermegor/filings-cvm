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

### `DfinCraReader` · `DfinCriReader` · `CadastroEmissorCepacReader` (3 readers)

`filings_cvm.ingestion.DfinCraReader` · `filings_cvm.ingestion.DfinCriReader` ·
`filings_cvm.ingestion.CadastroEmissorCepacReader`

Os três datasets de **CSV solto** da Securitização + emissores de CEPAC, que **inauguram** os portal
roots `securit/` e `emissor_cepac/`. Página completa:
[DFIN Securit + Emissor CEPAC](ingestion/securit_cepac_flat.md).

- `DfinCraReader` / `DfinCriReader` — `dfin_{cra,cri}_AAAA.csv`, índices anuais das demonstrações
  financeiras dos CRA/CRI. `date_ref` seleciona o **ano**; `Link_Download` devolvido como texto,
  **não seguido**.
- `CadastroEmissorCepacReader` — `cad_emissor_cepac.csv`, **snapshot** de URL fixa dos emissores de
  CEPAC (municípios). **Sem `date_ref`** (a CVM sobrescreve no lugar).

#### `DfinCraReader(date_ref=None, path_raw=None, retry_policy=None, cls_logger=None)` · `CadastroEmissorCepacReader(path_raw=None, retry_policy=None, cls_logger=None)`

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `date_ref` | `datetime.date \| None` | DFIN: qualquer dia do **ano**. **Ausente** no CEPAC (snapshot). |
| `path_raw` | `pathlib.Path \| None` | Diretório onde **persistir** o CSV bruto (camada *bronze*). |
| `retry_policy` | `RetryPolicy \| None` | Agenda de retry/backoff. Se `None`, usa o `_RETRY_POLICY` do reader. |
| `cls_logger` | `LogEmitter \| None` | Emissor de log injetável. |

#### `read(int_timeout_s=60) -> pd.DataFrame`

Só as colunas de data viram `date`; o restante fica texto exato. Levanta `OSError` ou `ContractError`.

```python
from datetime import date
from filings_cvm import DfinCraReader, CadastroEmissorCepacReader

df_ = DfinCraReader(date_ref=date(2025, 6, 1)).read()   # índice de DF dos CRA de 2025
cad = CadastroEmissorCepacReader().read()               # snapshot dos emissores de CEPAC
```

### `InfMensalOts*Reader` (8 readers)

`filings_cvm.ingestion.InfMensalOts{Geral,AtivoPassivo,Classe,DireitosCreditorios,Desembolso,FluxoCaixa,Derivativos,CedenteDevedor}Reader`

As 8 seções do Informe Mensal das operações de securitização não-CRA/CRI
(`inf_mensal_ots_AAAA.zip`). Página completa:
[Informe Mensal OTS](ingestion/inf_mensal_ots.md). Todos partilham a base privada
`_base_inf_mensal_ots_reader` e o prefixo-chave `CNPJ_Securitizadora`,
`Codigo_Identificacao_Certificado`, `Data_Referencia`, `Versao`. ⚠️ Particionado por **ano** apesar
de mensal (o `date_ref` seleciona o ano). `cedente_devedor.CNPJ` guarda CPF (não validado como
CNPJ); `Indice_Subordinacao_Data_Base` não é data.

#### `InfMensalOtsGeralReader(date_ref=None, path_raw=None, retry_policy=None, cls_logger=None)` (idem para os outros 7)

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `date_ref` | `datetime.date \| None` | Qualquer dia do **ano** de referência — só o ano é lido. Padrão: hoje. |
| `path_raw` | `pathlib.Path \| None` | Diretório onde **persistir** o ZIP bruto e os 8 CSVs (camada *bronze*). |
| `retry_policy` | `RetryPolicy \| None` | Agenda de retry/backoff. Se `None`, usa o `_RETRY_POLICY` do reader. |
| `cls_logger` | `LogEmitter \| None` | Emissor de log injetável. |

#### `read(int_timeout_s=60) -> pd.DataFrame`

Devolve as linhas do ano para a seção. Datas viram `date` (por membro); o restante fica texto exato.
Levanta `OSError`, `ContractError` ou `ValueError` (membro ausente).

```python
from datetime import date
from filings_cvm import InfMensalOtsClasseReader

df_ = InfMensalOtsClasseReader(date_ref=date(2025, 6, 1)).read()   # o ANO de 2025
# muitas linhas por certificado — uma por classe/série.
```

### `InfMensalCra*Reader` (8 readers)

`filings_cvm.ingestion.InfMensalCra{Geral,AtivoPassivo,Classe,DireitosCreditorios,Desembolso,FluxoCaixa,Derivativos,CedenteDevedor}Reader`

As 8 seções do Informe Mensal das operações de **CRA** (*Certificado de Recebíveis do Agronegócio*,
`inf_mensal_cra_AAAA.zip`). Página completa:
[Informe Mensal CRA](ingestion/inf_mensal_cra.md). Todos partilham a base privada
`_base_inf_mensal_cra_reader` e o prefixo-chave `CNPJ_Emissora`,
`Codigo_Identificacao_Certificado`, `Data_Referencia`, `Versao`. ⚠️ Particionado por **ano** apesar
de mensal (o `date_ref` seleciona o ano).

⚠️ **Mesmas 8 seções do OTS, nenhuma lista de colunas igual** (o CRA é agro): `CNPJ_Emissora` no
lugar de `CNPJ_Securitizadora` nos 8, `direitos_creditorios` com **56** colunas contra 43,
`*_Commodities_Agricolas` em `derivativos`. `cedente_devedor.CNPJ` guarda CPF e texto sujo (não
validado como CNPJ); `Indice_Subordinacao_Data_Base` não é data.

#### `InfMensalCraGeralReader(date_ref=None, path_raw=None, retry_policy=None, cls_logger=None)` (idem para os outros 7)

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `date_ref` | `datetime.date \| None` | Qualquer dia do **ano** de referência — só o ano é lido. Padrão: hoje. |
| `path_raw` | `pathlib.Path \| None` | Diretório onde **persistir** o ZIP bruto e os 8 CSVs (camada *bronze*). |
| `retry_policy` | `RetryPolicy \| None` | Agenda de retry/backoff. Se `None`, usa o `_RETRY_POLICY` do reader. |
| `cls_logger` | `LogEmitter \| None` | Emissor de log injetável. |

#### `read(int_timeout_s=60) -> pd.DataFrame`

Devolve as linhas do ano para a seção. Datas viram `date` (por membro); o restante fica texto exato.
Levanta `OSError`, `ContractError` ou `ValueError` (membro ausente).

```python
from datetime import date
from filings_cvm import InfMensalCraDireitosCreditoriosReader

df_ = InfMensalCraDireitosCreditoriosReader(date_ref=date(2025, 6, 1)).read()   # o ANO de 2025
# 56 colunas — inclui os baldes agro (produção, comercialização, beneficiamento, industrialização).
```

---

### `InfMensalCri*Reader` (11 readers)

`filings_cvm.ingestion.InfMensalCri{Geral,AtivoPassivo,Classe,Creditos,Carteira,CarteiraModificacao,Desembolso,FluxoCaixa,Derivativos,CedenteDevedor,Responsavel}Reader`

As 11 seções do Informe Mensal das operações de **CRI** (*Certificado de Recebíveis Imobiliários*,
`inf_mensal_cri_AAAA.zip`). Página completa:
[Informe Mensal CRI](ingestion/inf_mensal_cri.md). Todos partilham a base privada
`_base_inf_mensal_cri_reader` e o prefixo-chave `CNPJ_Emissora`,
`Codigo_Identificacao_Certificado`, `Data_Referencia`, `Versao`. ⚠️ Particionado por **ano** apesar
de mensal (o `date_ref` seleciona o ano). **Fecha o portal root `securit/` (4/4).**

⚠️ **Compartilha 7 nomes de seção com CRA/OTS mas o CRI é imobiliário**: não tem
`direitos_creditorios` (a seção de recebíveis é `creditos`, 51 colunas) e acrescenta `carteira`,
`carteira_modificacao`, `creditos` e `responsavel`. Cada contract é **gerado do header** e **pinado**
a um fixture verbatim. `cedente_devedor.CNPJ` pode guardar CPF (não validado como CNPJ);
`Indice_Subordinacao_Data_Base` e `Data_LTV` (varchar no META) não são datas;
`carteira_modificacao`/`responsavel` são header-only (sem coluna de CNPJ validada).

#### `InfMensalCriGeralReader(date_ref=None, path_raw=None, retry_policy=None, cls_logger=None)` (idem para os outros 10)

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `date_ref` | `datetime.date \| None` | Qualquer dia do **ano** de referência — só o ano é lido. Padrão: hoje. |
| `path_raw` | `pathlib.Path \| None` | Diretório onde **persistir** o ZIP bruto e os 11 CSVs (camada *bronze*). |
| `retry_policy` | `RetryPolicy \| None` | Agenda de retry/backoff. Se `None`, usa o `_RETRY_POLICY` do reader. |
| `cls_logger` | `LogEmitter \| None` | Emissor de log injetável. |

#### `read(int_timeout_s=60) -> pd.DataFrame`

Devolve as linhas do ano para a seção. Datas viram `date` (por membro); o restante fica texto exato.
Levanta `OSError`, `ContractError` ou `ValueError` (membro ausente).

```python
from datetime import date
from filings_cvm import InfMensalCriCreditosReader

df_ = InfMensalCriCreditosReader(date_ref=date(2025, 6, 1)).read()   # o ANO de 2025
# 51 colunas — a carteira de recebíveis imobiliários (incorporação, aluguéis, aquisição, …).
```

---

### `AuditorPfReader` · `AuditorPjReader` (2 readers)

`filings_cvm.ingestion.auditor`

O cadastro dos **auditores independentes** (`AUDITOR/CAD`, `cad_auditor.zip`) — **snapshot** de URL
fixa, sem `date_ref`. Inaugura o *portal root* `auditor/` e a **Wave 3** do #41. Página completa em
[Cadastro de Auditores (AUDITOR)](ingestion/auditor.md).

- `AuditorPfReader` — `cad_auditor_pf.csv`, auditores pessoa física (4 colunas; **sem CNPJ/CPF**).
- `AuditorPjReader` — `cad_auditor_pj.csv`, firmas de auditoria (12 colunas; `CNPJ` mascarado).

#### `__init__(path_raw=None, retry_policy=None, cls_logger=None)`

**Sem `date_ref`** — retrato do estado atual numa URL fixa que a CVM sobrescreve no lugar. Os dois
readers baixam o mesmo `cad_auditor.zip`, então um `path_raw` de qualquer um serve o outro.

#### `read(int_timeout_s=60) -> pd.DataFrame`

Uma linha por auditor. `DT_INI_SIT` vira `date`; o restante fica texto exato (`CEP`/`CD_CVM`
preservam zeros à esquerda). Levanta `OSError`, `ContractError` ou `ValueError` (membro ausente).

```python
from filings_cvm import AuditorPjReader

df_ = AuditorPjReader().read()
# df_[["CD_CVM", "CNPJ", "DENOM_SOCIAL", "SIT", "UF"]]
```

---

### `AgenteFiducPfReader` · `AgenteFiducPjReader` (2 readers)

`filings_cvm.ingestion.agente_fiduc`

O cadastro dos **agentes fiduciários** (`AGENTE_FIDUC/CAD`, `cad_agente_fiduc.zip`) — **snapshot** de
URL fixa, sem `date_ref`. Inaugura o *portal root* `agente_fiduc/` (2ª fatia da Wave 3 do #41).
Página completa em [Cadastro de Agentes Fiduciários](ingestion/agente_fiduc.md).

- `AgenteFiducPfReader` — `cad_agente_fiduc_pf.csv`, agentes pessoa física (5 colunas; **sem
  CNPJ/CPF/`CD_CVM`**, identifica só pelo nome).
- `AgenteFiducPjReader` — `cad_agente_fiduc_pj.csv`, firmas (15 colunas; `CNPJ` mascarado + endereço/telefone).

#### `__init__(path_raw=None, retry_policy=None, cls_logger=None)`

**Sem `date_ref`** — retrato do estado atual numa URL fixa que a CVM sobrescreve no lugar. Os dois
readers baixam o mesmo `cad_agente_fiduc.zip`, então um `path_raw` de qualquer um serve o outro.

#### `read(int_timeout_s=60) -> pd.DataFrame`

Uma linha por agente. `DT_REG`/`DT_CANCEL`/`DT_INI_SIT` viram `date`; o restante fica texto exato
(`CEP`/`DDD_TEL`/`TEL` preservam zeros à esquerda). Levanta `OSError`, `ContractError` ou `ValueError`
(membro ausente).

```python
from filings_cvm import AgenteFiducPjReader

df_ = AgenteFiducPjReader().read()
# df_[["CNPJ", "DENOM_SOCIAL", "SIT", "MUN", "UF"]]
```

---

### `AgenteAutonPfReader` · `AgenteAutonPjReader` (2 readers)

`filings_cvm.ingestion.agente_auton`

O cadastro dos **agentes autônomos de investimento** (`AGENTE_AUTON/CAD`, `cad_agente_auton.zip`) —
**snapshot** de URL fixa, sem `date_ref`. Inaugura o *portal root* `agente_auton/` (3ª fatia da Wave
3 do #41). Página completa em [Cadastro de Agentes Autônomos](ingestion/agente_auton.md).

- `AgenteAutonPfReader` — `cad_agente_auton_pf.csv`, agentes pessoa física (6 colunas; **sem
  CNPJ/CPF**, identifica pelo `NOME`, que pode vir em branco).
- `AgenteAutonPjReader` — `cad_agente_auton_pj.csv`, firmas (19 colunas; `CNPJ` mascarado +
  denom. comercial/endereço/telefone/e-mail/site).

#### `__init__(path_raw=None, retry_policy=None, cls_logger=None)`

**Sem `date_ref`** — retrato do estado atual numa URL fixa que a CVM sobrescreve no lugar. Os dois
readers baixam o mesmo `cad_agente_auton.zip`, então um `path_raw` de qualquer um serve o outro.

#### `read(int_timeout_s=60) -> pd.DataFrame`

Uma linha por agente. `DT_REG`/`DT_CANCEL`/`DT_INI_SIT` viram `date`; o restante fica texto exato
(`CEP`/`DDD`/`TEL` preservam zeros à esquerda). Levanta `OSError`, `ContractError` ou `ValueError`
(membro ausente).

```python
from filings_cvm import AgenteAutonPjReader

df_ = AgenteAutonPjReader().read()
# df_[["CNPJ", "DENOM_SOCIAL", "SIT", "MUN", "UF", "EMAIL"]]
```

---

### `InvnrRepresPfReader` · `InvnrRepresPjReader` (2 readers)

`filings_cvm.ingestion.invnr`

O cadastro dos **representantes de investidores não residentes** (`INVNR/CAD`,
`cad_invnr_repres.zip`) — **snapshot** de URL fixa, sem `date_ref`. Inaugura o *portal root*
`invnr/` (4ª fatia da Wave 3 do #41). Página completa em
[Cadastro de Repres. de Inv. Não Residentes](ingestion/invnr.md).

- `InvnrRepresPfReader` — `cad_invnr_repres_pf.csv`, representantes pessoa física (6 colunas; **sem
  CNPJ/CPF**, identifica pelo `NOME`).
- `InvnrRepresPjReader` — `cad_invnr_repres_pj.csv`, firmas (23 colunas; `CNPJ` mascarado +
  controle acionário/patrimônio líquido/endereço/telefone/fax/e-mail).

#### `__init__(path_raw=None, retry_policy=None, cls_logger=None)`

**Sem `date_ref`** — retrato do estado atual numa URL fixa que a CVM sobrescreve no lugar. Os dois
readers baixam o mesmo `cad_invnr_repres.zip`, então um `path_raw` de qualquer um serve o outro.

#### `read(int_timeout_s=60) -> pd.DataFrame`

Uma linha por representante. `DT_REG`/`DT_CANCEL`/`DT_INI_SIT` (e `DT_PATRIM_LIQ` no `pj`) viram
`date`; o restante fica texto exato (`CEP`/`TEL`/`FAX`, `numeric` no META, preservam zeros à
esquerda). Levanta `OSError`, `ContractError` ou `ValueError` (membro ausente).

```python
from filings_cvm import InvnrRepresPjReader

df_ = InvnrRepresPjReader().read()
# df_[["CNPJ", "DENOM_SOCIAL", "SIT", "MUN", "UF", "VL_PATRIM_LIQ"]]
```

---

### `IntermedReader` · `IntermedRespReader` (2 readers)

`filings_cvm.ingestion.intermed`

O cadastro dos **intermediários de mercado** (`INTERMED/CAD`, `cad_intermed.zip`) — **snapshot** de
URL fixa, sem `date_ref`. Inaugura o *portal root* `intermed/` (5ª fatia da Wave 3 do #41). Página
completa em [Cadastro de Intermediários](ingestion/intermed.md).

⚠️ **Os dois membros NÃO são um split `pf`/`pj`** — são o registro do intermediário e a tabela de
responsáveis, ambos chaveados pelo `CNPJ` do intermediário:

- `IntermedReader` — `cad_intermed.csv`, registro do intermediário (28 colunas; `CNPJ` mascarado +
  código CVM/setor/patrimônio/endereço/contato).
- `IntermedRespReader` — `cad_intermed_resp.csv`, responsáveis (8 colunas; dado pessoal
  `RESP`/`EMAIL_RESP`, **sem CPF** — o único `CNPJ` é o do intermediário).

#### `__init__(path_raw=None, retry_policy=None, cls_logger=None)`

**Sem `date_ref`** — retrato do estado atual numa URL fixa que a CVM sobrescreve no lugar. Os dois
readers baixam o mesmo `cad_intermed.zip`, então um `path_raw` de qualquer um serve o outro.

#### `read(int_timeout_s=60) -> pd.DataFrame`

Uma linha por intermediário (ou responsável). As colunas `DT_*` viram `date`; o restante fica texto
exato (`CEP`/`TEL`/`FAX`/`CD_CVM`, `numeric` no META, preservam zeros à esquerda). Levanta `OSError`,
`ContractError` ou `ValueError` (membro ausente).

```python
from filings_cvm import IntermedReader

df_ = IntermedReader().read()
# df_[["CNPJ", "DENOM_SOCIAL", "TP_PARTIC", "SIT", "MUN", "UF"]]
```

---

### `AdmCartPfReader` · `AdmCartPjReader` · `AdmCartDiretorReader` · `AdmCartRespReader` · `AdmCartSociosReader` (5 readers)

`filings_cvm.ingestion.adm_cart`

O cadastro dos **administradores de carteira** (`ADM_CART/CAD`, `cad_adm_cart.zip`) — **snapshot** de
URL fixa, sem `date_ref`. Inaugura o *portal root* `adm_cart/` e é o **primeiro root de 5 membros**
(6ª fatia da Wave 3 do #41). Página completa em
[Cadastro de Administradores de Carteira](ingestion/adm_cart.md).

- `AdmCartPfReader` — `cad_adm_cart_pf.csv`, administradores pessoa física (7 colunas; **sem
  CNPJ/CPF**, identifica pelo `ADMIN`).
- `AdmCartPjReader` — `cad_adm_cart_pj.csv`, firmas (24 colunas; `CNPJ` mascarado + categoria/
  patrimônio/endereço/contato).
- `AdmCartDiretorReader` / `AdmCartRespReader` / `AdmCartSociosReader` — as tabelas de diretores (3
  cols), responsáveis (3) e sócios (2), todas chaveadas pelo `CNPJ` do administrador. ⚠️ **Nenhuma
  tem coluna de data** (`_DATE_COLS = ()`), e carregam dado pessoal (`DIRETOR`/`RESP`/`SOCIOS`) mas
  **sem CPF**.

#### `__init__(path_raw=None, retry_policy=None, cls_logger=None)`

**Sem `date_ref`** — retrato do estado atual numa URL fixa que a CVM sobrescreve no lugar. Os cinco
readers baixam o mesmo `cad_adm_cart.zip`, então um `path_raw` de qualquer um serve os outros.

#### `read(int_timeout_s=60) -> pd.DataFrame`

Uma linha por administrador (ou diretor/responsável/sócio). As colunas `DT_*` viram `date` (nos três
membros sem data, nada é convertido); o restante fica texto exato (`CEP`/`TEL`, `numeric` no META,
preservam zeros à esquerda). Um CNPJ malformado da fonte (`00.010.354/1901-72`) é **devolvido como
publicado**. Levanta `OSError`, `ContractError` ou `ValueError` (membro ausente).

```python
from filings_cvm import AdmCartPjReader

df_ = AdmCartPjReader().read()
# df_[["CNPJ", "DENOM_SOCIAL", "CATEG_REG", "SIT", "MUN", "UF"]]
```

---

### `ConsultorVlmobPfReader` · `ConsultorVlmobPjReader` · `ConsultorVlmobDiretorReader` · `ConsultorVlmobRespReader` · `ConsultorVlmobSociosReader` (5 readers)

`filings_cvm.ingestion.consultor_vlmob`

O cadastro dos **consultores de valores mobiliários** (`CONSULTOR_VLMOB/CAD`,
`cad_consultor_vlmob.zip`) — **snapshot** de URL fixa, sem `date_ref`. Inaugura o *portal root*
`consultor_vlmob/` (7ª fatia da Wave 3 do #41), na mesma forma de 5 membros do ADM_CART. Página
completa em [Cadastro de Consultores de Valores Mobiliários](ingestion/consultor_vlmob.md).

- `ConsultorVlmobPfReader` — `cad_consultor_vlmob_pf.csv`, consultores pessoa física (7 colunas;
  **sem CNPJ/CPF**, identifica pelo `NOME`).
- `ConsultorVlmobPjReader` — `cad_consultor_vlmob_pj.csv`, firmas (20 colunas; `CNPJ` mascarado +
  endereço/contato). ⚠️ **3 date cols** — sem `DT_PATRIM_LIQ`, ao contrário do ADM_CART.
- `ConsultorVlmobDiretorReader` / `ConsultorVlmobRespReader` / `ConsultorVlmobSociosReader` — as
  tabelas de diretores (3 cols), responsáveis (3) e sócios (2), todas chaveadas pelo `CNPJ` do
  consultor. ⚠️ **Nenhuma tem coluna de data** (`_DATE_COLS = ()`), e carregam dado pessoal
  (`DIRETOR`/`RESP`/`SOCIOS`) mas **sem CPF**.

#### `__init__(path_raw=None, retry_policy=None, cls_logger=None)`

**Sem `date_ref`** — retrato do estado atual numa URL fixa que a CVM sobrescreve no lugar. Os cinco
readers baixam o mesmo `cad_consultor_vlmob.zip`, então um `path_raw` de qualquer um serve os outros.

#### `read(int_timeout_s=60) -> pd.DataFrame`

Uma linha por consultor (ou diretor/responsável/sócio). As colunas `DT_*` viram `date` (nos três
membros sem data, nada é convertido); o restante fica texto exato (`CEP`/`TEL`, `numeric` no META,
preservam zeros à esquerda). Levanta `OSError`, `ContractError` ou `ValueError` (membro ausente).

```python
from filings_cvm import ConsultorVlmobPjReader

df_ = ConsultorVlmobPjReader().read()
# df_[["CNPJ", "DENOM_SOCIAL", "SIT", "MUN", "UF", "EMAIL"]]
```

---

### `CadastroAdmFiiReader` (1 reader)

`filings_cvm.ingestion.adm_fii`

O cadastro das entidades registradas para **administrar FII** (`ADM_FII/CAD`, `cad_adm_fii.csv`) —
**snapshot** de URL fixa, sem `date_ref`. Inaugura o *portal root* `adm_fii/` e **encerra a Wave 3
do #41** (8ª e última fatia). Único membro da Wave 3 num **CSV solto** (não ZIP), no molde do
`CadastroFiReader` / Emissor CEPAC. Página completa em
[Cadastro de Administradores de FII](ingestion/adm_fii.md).

- `CadastroAdmFiiReader` — `cad_adm_fii.csv`, uma linha por administrador de FII (18 colunas; `CNPJ`
  mascarado, **sem coluna de CPF**; `MOTIVO_CANCEL` é texto, não data).

#### `__init__(path_raw=None, retry_policy=None, cls_logger=None)`

**Sem `date_ref`** — retrato do estado atual numa URL fixa que a CVM sobrescreve no lugar; um
`path_raw` persistido é o único registro do snapshot.

#### `read(int_timeout_s=60) -> pd.DataFrame`

Uma linha por administrador. As colunas `DT_REG` / `DT_CANCEL` / `DT_INI_SIT` viram `date`; o
restante fica texto exato (`CEP`/`DDD`/`TEL`, `numeric` no META, preservam zeros à esquerda).
Levanta `OSError` ou `ContractError`.

```python
from filings_cvm import CadastroAdmFiiReader

df_ = CadastroAdmFiiReader().read()
# df_[["CNPJ", "DENOM_SOCIAL", "DENOM_COMERC", "SIT", "MUN", "UF"]]
```

---

### `CadastroCiaEstrangReader` (1 reader)

`filings_cvm.ingestion.cia_estrang`

O cadastro das **companhias estrangeiras** registradas na CVM (`CIA_ESTRANG/CAD`,
`cad_cia_estrang.csv`) — **snapshot** de URL fixa, sem `date_ref`. Inaugura o *portal root*
`cia_estrang/` e **abre a Wave 4 do #41**. **CSV solto** de 1 reader, no molde do
`CadastroAdmFiiReader`. Página completa em
[Cadastro de Companhias Estrangeiras](ingestion/cia_estrang.md).

- `CadastroCiaEstrangReader` — `cad_cia_estrang.csv`, uma linha por companhia estrangeira (49
  colunas; **duas colunas de CNPJ**: `CNPJ` da companhia + `CNPJ_AUDITOR`; `RESP` tem nome de
  pessoa mas **sem CPF**; `MOTIVO_CANCEL` é texto, não data).

#### `__init__(path_raw=None, retry_policy=None, cls_logger=None)`

**Sem `date_ref`** — retrato do estado atual numa URL fixa que a CVM sobrescreve no lugar; um
`path_raw` persistido é o único registro do snapshot.

#### `read(int_timeout_s=60) -> pd.DataFrame`

Uma linha por companhia. As **sete** colunas `DT_*` viram `date`; o restante fica texto exato
(`CD_CVM`/`CEP`/`TEL`/`DDD_*`, `numeric`/`char` no META, preservam zeros à esquerda). Levanta
`OSError` ou `ContractError`. O contract é **pinado** ao header verbatim (49 cols).

```python
from filings_cvm import CadastroCiaEstrangReader

df_ = CadastroCiaEstrangReader().read()
# df_[["CNPJ", "DENOM_SOCIAL", "PAIS_ORIGEM", "SIT", "CNPJ_AUDITOR", "AUDITOR"]]
```

---

### `CadastroCiaIncentReader` (1 reader)

`filings_cvm.ingestion.cia_incent`

O cadastro das **companhias incentivadas** registradas na CVM (`CIA_INCENT/CAD`,
`cad_cia_incent.csv`) — **snapshot** de URL fixa, sem `date_ref`. Inaugura o *portal root*
`cia_incent/` (2ª fatia da Wave 4 do #41). **CSV solto** de 1 reader, no molde do
`CadastroCiaEstrangReader`. Página completa em
[Cadastro de Companhias Incentivadas](ingestion/cia_incent.md).

- `CadastroCiaIncentReader` — `cad_cia_incent.csv`, uma linha por companhia incentivada (47 colunas,
  ~3.570 linhas). ⚠️ **Não é cópia do CIA_ESTRANG** (tem `ST_CIA_INCENT_REG`, usa `MUN`/`UF`). Duas
  colunas de CNPJ (`CNPJ` + `CNPJ_AUDITOR`); `RESP` sem CPF; `MOTIVO_CANCEL` é texto.

#### `__init__(path_raw=None, retry_policy=None, cls_logger=None)`

**Sem `date_ref`** — retrato do estado atual numa URL fixa que a CVM sobrescreve no lugar; um
`path_raw` persistido é o único registro do snapshot.

#### `read(int_timeout_s=60) -> pd.DataFrame`

Uma linha por companhia. As **sete** colunas `DT_*` viram `date` (`DT_INI_CATEG` chega vazia →
`NaT`); o restante fica texto exato. Levanta `OSError` ou `ContractError`. O contract é **pinado**
ao header verbatim (47 cols).

```python
from filings_cvm import CadastroCiaIncentReader

df_ = CadastroCiaIncentReader().read()
# df_[["CNPJ", "DENOM_SOCIAL", "SIT", "MUN", "UF", "CNPJ_AUDITOR", "AUDITOR"]]
```

---

### `CoordOfertaReader` · `CoordOfertaRespReader` (2 readers)

`filings_cvm.ingestion.coord_oferta`

O cadastro dos **coordenadores de oferta** (`COORD_OFERTA/CAD`, `cad_coord_oferta.zip`) —
**snapshot** de URL fixa, sem `date_ref`. Inaugura o *portal root* `coord_oferta/` (3ª fatia da
Wave 4 do #41) e é o **primeiro ZIP multi-membro da Wave 4**, no molde do INTERMED. Página completa
em [Cadastro de Coordenadores de Oferta](ingestion/coord_oferta.md).

- `CoordOfertaReader` — `cad_coord_oferta.csv`, o registro (25 colunas, 4 date cols: `DT_REG`,
  `DT_CANCEL`, `DT_INI_SIT`, `DT_PATRIM_LIQ`).
- `CoordOfertaRespReader` — `cad_coord_oferta_resp.csv`, os responsáveis (6 colunas, 2 date cols).
  ⚠️ **Não é um split `pf`/`pj`**: é chaveado pelo **`CNPJ` do coordenador**; tem dado pessoal
  (`RESP`) mas **sem coluna de CPF**.

#### `__init__(path_raw=None, retry_policy=None, cls_logger=None)`

**Sem `date_ref`** — retrato do estado atual numa URL fixa que a CVM sobrescreve no lugar. Os dois
readers baixam o mesmo `cad_coord_oferta.zip`, então um `path_raw` de qualquer um serve o outro.

#### `read(int_timeout_s=60) -> pd.DataFrame`

Uma linha por coordenador (ou responsável). As colunas `DT_*` viram `date`; o restante fica texto
exato (`CD_CVM`/`CEP`/`TEL`/`FAX`/`DDD_*`, `numeric`/`char` no META, preservam zeros à esquerda).
Levanta `OSError`, `ContractError` ou `ValueError` (membro ausente).

```python
from filings_cvm import CoordOfertaReader

df_ = CoordOfertaReader().read()
# df_[["CNPJ", "DENOM_SOCIAL", "SIT", "MUN", "UF", "VL_PATRIM_LIQ"]]
```

---

### `CrowdfundingReader` · `CrowdfundingAdmRespReader` · `CrowdfundingSociosReader` (3 readers)

`filings_cvm.ingestion.crowdfunding`

O cadastro das **plataformas de crowdfunding** (`CROWDFUNDING/CAD`, `cad_crowdfunding.zip`) —
**snapshot** de URL fixa, sem `date_ref`. Inaugura o *portal root* `crowdfunding/` (4ª fatia da
Wave 4 do #41). Página completa em
[Cadastro de Plataformas de Crowdfunding](ingestion/crowdfunding.md).

- `CrowdfundingReader` — `cad_crowdfunding.csv`, o registro (17 colunas, 2 date cols). ⚠️ **Mais
  enxuto que os irmãos**: sem `DT_CANCEL`/`MOTIVO_CANCEL`/`CD_CVM`; usa `WEBSITE` (não `SITE_WEB`)
  e `DDD` (não `DDD_TEL`).
- `CrowdfundingAdmRespReader` / `CrowdfundingSociosReader` — os administradores responsáveis e os
  sócios (2 colunas cada). ⚠️ **Nenhuma coluna de data** (`_DATE_COLS = ()`); carregam dado pessoal
  (`ADM_RESP`, `SOCIO`) mas **sem CPF**, chaveados pelo `CNPJ` da plataforma.

#### `__init__(path_raw=None, retry_policy=None, cls_logger=None)`

**Sem `date_ref`** — retrato do estado atual numa URL fixa que a CVM sobrescreve no lugar. Os três
readers baixam o mesmo `cad_crowdfunding.zip`, então um `path_raw` de qualquer um serve os outros.

#### `read(int_timeout_s=60) -> pd.DataFrame`

Uma linha por plataforma (ou administrador/sócio). As colunas `DT_*` viram `date` (nos satélites
nada é convertido); o restante fica texto exato (`CEP`/`TEL`/`DDD`, `numeric` no META, preservam
zeros à esquerda). Levanta `OSError`, `ContractError` ou `ValueError` (membro ausente).

```python
from filings_cvm import CrowdfundingReader

df_ = CrowdfundingReader().read()
# df_[["CNPJ", "DENOM_SOCIAL", "SIT", "WEBSITE", "MUN", "UF"]]
```

---

### `Meta*Reader` (35 readers)

Os **META** — a spec que a própria CVM publica para cada dataset (`.../<DATASET>/META/`). Um reader
por dataset; página completa em [META (metadados da CVM)](ingestion/meta.md).

`MetaInformeDiarioReader` · `MetaCdaReader` · `MetaLaminaReader` · `MetaCadastroFiReader` ·
`MetaCadFiHistReader` · `MetaRegistroReader` · `MetaInfMensalFidcReader` · `MetaInfMensalFiiReader` ·
`MetaDfinFiiReader` · `MetaInfTrimestralFiiReader` · `MetaInfAnualFiiReader` ·
`MetaInfTrimestralFipReader` · `MetaInfQuadrimestralFipReader` · `MetaInfMensalFiagroReader` ·
`MetaBalanceteFieReader` · `MetaBalancoFieReader` · `MetaMedidasMesFieReader` · `MetaDfinCraReader` ·
`MetaDfinCriReader` · `MetaInfMensalOtsReader` · `MetaInfMensalCraReader` ·
`MetaInfMensalCriReader` · `MetaCadEmissorCepacReader` · `MetaAuditorReader` · `MetaAgenteFiducReader`
· `MetaAgenteAutonReader` · `MetaInvnrRepresReader` · `MetaIntermedReader` · `MetaAdmCartReader` ·
`MetaConsultorVlmobReader` · `MetaCadAdmFiiReader` · `MetaCadCiaEstrangReader` ·
`MetaCadCiaIncentReader` · `MetaCoordOfertaReader` · `MetaCrowdfundingReader`

#### `__init__(path_raw=None, retry_policy=None, cls_logger=None)`

**Sem `date_ref`** — o META fica numa URL fixa que a CVM sobrescreve no lugar (o precedente do
`CadastroFiReader`), então um `path_raw` gravado é o **único** registro do que a spec dizia naquele
dia.

#### `read(int_timeout_s=60) -> pd.DataFrame`

Uma linha por campo declarado, colunas `section`, `field`, `description`, `domain`, `data_type`,
`size`, `precision`, `scale` (+ as seis de proveniência). Um META `.zip` multi-membro volta como
**um único frame longo**, com o membro em `section`. Levanta `OSError` (download).

```python
from filings_cvm import MetaInfMensalCraReader

df_meta = MetaInfMensalCraReader().read()
# 8 seções; os nomes de campo vêm VERBATIM — inclusive truncados em 50 caracteres.
```

> ⚠️ **A CVM trunca o nome do campo em 50 caracteres** (o header real vai até 60) e a **ordem do
> META nunca é a do arquivo real**. O reader devolve os dois fatos como estão: o header real segue
> sendo a fonte da ordem e dos nomes longos; a reconciliação é do consumidor e precisa ser
> *truncation-aware* (`header[:50] == meta`).

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
