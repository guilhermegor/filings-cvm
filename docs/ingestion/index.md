# **Leitura (← CVM)**

A seção `filings_cvm.ingestion` analisa e interpreta arquivos **recebidos/baixados** da CVM de
volta para modelos tipados — a contraparte do [Envio](../submission/perfil_mensal.md).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Padrões implementados

- **[Informe Diário FIF](informe_diario.md)** — `InformeDiarioReader`: lê o dump mensal de
  *open-data* (`inf_diario_fi_AAAAMM`) e devolve um `DataFrame` tipado e validado por contrato.
- **[CDA FIF](cda.md)** — `CdaReader`: lê o dump mensal (`cda_fi_AAAAMM`), consolida os blocos de
  ativos `BLC_1`…`BLC_8` e traz o patrimônio líquido do fundo junto de cada posição.
- **[Lâmina carteira FIF](lamina_carteira.md)** — `LaminaCarteiraReader`: lê o membro
  `lamina_fi_carteira_AAAAMM` do dump da Lâmina e devolve a alocação de cada fundo por **tipo de
  ativo** (`PR_PL_ATIVO`, percentual sinalizado do patrimônio líquido).
- **[Lâmina FIF](lamina.md)** — `LaminaReader`: lê o membro `lamina_fi_AAAAMM` do **mesmo** dump —
  a lâmina propriamente dita, uma linha por classe de fundo com as suas 78 colunas.
- **[Cadastro de Fundos (CAD/FI)](cadastro_fi.md)** — `CadastroFiReader`: lê `cad_fi.csv`, o
  **retrato do estado atual** do cadastro. Sem `date_ref` e **sem chave única** — o CNPJ se repete
  entre regimes regulatórios.
- **[Registro RCVM 175](registro.md)** — `RegistroFundoReader`, `RegistroClasseReader`,
  `RegistroSubclasseReader`: lêem os três membros de `registro_fundo_classe.zip` (hierarquia
  `fundo → classe → subclasse`), o cadastro **atual** onde estão os fundos vivos.
- **[CAD/FI histórico](cad_fi_hist.md)** — 19 readers `CadastroFiHist*Reader`: o **log de
  alterações** de cada atributo mutável do cadastro legado (situação, denominação, taxas, gestor,
  …), um por membro de `cad_fi_hist.zip`.
- **[Informe Mensal FIDC](inf_mensal_fidc.md)** — 17 readers `InfMensalFidcTab*Reader`: as tabelas
  do informe mensal dos FIDC (`inf_mensal_fidc_AAAAMM.zip`, Tabelas I–X + sub-tabelas de X), um por
  membro. Inaugura o *portal root* `fidc/`. Cada reader declara a sua **política de retry por
  tabela** (`_RETRY_POLICY`).
- **[Informe Mensal FII](inf_mensal_fii.md)** — 3 readers `InfMensalFii*Reader` (`geral`,
  `ativo_passivo`, `complemento`): o informe mensal dos fundos imobiliários. Inaugura o *portal
  root* `fii/`. ⚠️ O dump é **particionado por ano** (`inf_mensal_fii_AAAA.zip`), apesar de mensal —
  o `date_ref` seleciona o **ano**.
- **[DFIN FII](dfin_fii.md)** — `DfinFiiReader`: o **índice** das demonstrações financeiras dos FII
  (`dfin_fii_AAAA.csv`, um CSV solto). Uma linha por documento entregue, com um `Link_Download` que
  o reader **devolve como texto e não segue**. Particionado por ano.
- **[Informe Trimestral FII](inf_trimestral_fii.md)** — 16 readers `InfTrimestralFii*Reader`: as
  tabelas do informe trimestral dos FII (`inf_trimestral_fii_AAAA.zip`) — cadastro, ativos,
  imóveis/terrenos e suas transações, rentabilidade e resultado contábil/financeiro. ⚠️
  Particionado por **ano** (o `date_ref` seleciona o ano, não o trimestre).
- **[Informe Anual FII](inf_anual_fii.md)** — 12 readers `InfAnualFii*Reader`: as tabelas do informe
  anual dos FII (`inf_anual_fii_AAAA.zip`) — cadastro, ativos, distribuição de cotistas, diretor e
  prestadores, processos, representante. ⚠️ Contém **CPF** (dado pessoal, texto exato) e um
  `Link_Download_Anexo` **não seguido**. Com ele o portal root `fii/` fica **completo (4/4)**.

Cada padrão de leitura ganha a sua própria página, com **Descrição** e **Exemplos**, no mesmo
formato das páginas de [Envio](../submission/informe_diario.md).

## Forma de um leitor

Todo leitor implementa o **port** `read() -> pd.DataFrame` (o contrato compartilhado, privado, em
`_internal/config/ports`) e devolve um `DataFrame` cujas colunas são tipadas explicitamente — nunca pela
inferência do pandas. Leitores de *open-data* (CSV) declaram o seu próprio contrato de colunas e
**não** reaproveitam o schema Pydantic de submissão, pois consomem um artefato distinto do XML.
Consulte o catálogo completo de padrões (implementados e pendentes) no `CLAUDE.md` do repositório.

## Colunas de proveniência

Todo `DataFrame` devolvido por um leitor carrega, **ao lado** das colunas de origem, seis colunas
de **proveniência**, para que a camada *bronze* de um *datalake* seja autodescritiva e rastreável:

| Coluna | Conteúdo |
|--------|----------|
| `url` | URL exata de onde o dado foi baixado. |
| `updated_at` | *Timestamp* de coleta (quando esta leitura buscou o dado), **UTC, tz-aware**. |
| `source_key` | Identificador do dataset (do contrato) — distingue leitores que compartilham a mesma `url` (ex.: os 19 membros de um mesmo ZIP). |
| `package_version` | Versão do pacote que produziu a linha (para re-ingestão após correção de bug). |
| `ingestion_run_id` | UUID gerado uma vez por `read()`, comum a todas as linhas daquela leitura. |
| `content_hash` | `sha256` dos bytes do artefato baixado — detecta se a fonte mudou desde a última coleta. |

Os nomes vivem em `FileContract.PROVENANCE_COLUMNS`; o seam `stamp_provenance` as acrescenta
**depois** da validação de contrato (elas não fazem parte do artefato de origem). `updated_at`
permanece *tz-aware* — um destino SQL que precise de *naive* normaliza no carregamento do *warehouse*,
nunca aqui.

## Política de retry — `retry_policy` e `_RETRY_POLICY`

Todo leitor aceita um `retry_policy: RetryPolicy | None = None` no construtor, repassado ao *seam*
de download como a sua agenda de novas tentativas / *backoff*. **Cada leitor declara a sua própria
paciência** por meio do atributo de classe `_RETRY_POLICY`, então a política fica **junto do
dataset** e é ajustável **por leitor** — sem tocar nos demais.

A resolução é em duas camadas:

1. **Argumento `retry_policy` no construtor** — se informado, vence para *aquela instância*.
2. **Atributo de classe `_RETRY_POLICY` do próprio leitor** — o padrão quando nada é passado. O
   padrão de fábrica é paciente (o portal da CVM aplica *throttle* sob carga): **5 tentativas**,
   *backoff* exponencial limitado (~2, 4, 8, 10 s).

```python
from filings_cvm import CdaReader, RetryPolicy

# 1. Padrão — o leitor usa a política do seu próprio módulo. Nada a passar:
df_ = CdaReader().read()

# 2. Sobrescrever numa chamada — o argumento vence o padrão do módulo:
cls_retry_policy = RetryPolicy(int_max_attempts=10, float_max_wait_s=30.0)
df_ = CdaReader(retry_policy=cls_retry_policy).read()

# 3. Inspecionar o padrão de um leitor sem construir:
CdaReader._RETRY_POLICY   # → RetryPolicy(int_max_attempts=5, …)
```

Para tornar a diferença **permanente** para um dataset, ajuste o `_RETRY_POLICY` na classe daquele
leitor — o `RetryPolicy` é um *value object* imutável, então declarar um por leitor é seguro. O
padrão é **estrutural**: um teste percorre toda a API pública e falha se um leitor novo não
declarar o seu `_RETRY_POLICY`.

## Artefato bruto — `path_raw`

Todo leitor aceita um `path_raw: Path | None = None` no construtor:

- **`None` (padrão)** — o artefato é baixado num diretório temporário, lido e **descartado** na
  saída. Nada **persiste**, e a leitura devolve apenas o `DataFrame`. Atenção: isso *não* é uma
  leitura sem disco — o arquivo é gravado transitoriamente e é preciso um diretório temporário
  gravável.
- **Um caminho** — o artefato **bruto e intacto** (`.zip`, `.csv`, `.html`, `.xlsx`, …) é gravado
  ali e **mantido**, *antes* de qualquer parsing. O diretório é criado junto com os pais.

É o espelho, na leitura, do `output_path` dos serializadores de [Envio](../submission/perfil_mensal.md):
`None` mantém tudo em memória, um caminho grava em disco.

Guardar o artefato bruto é o que torna a camada *bronze* de um *datalake* autoritativa: quando a
fonte muda o contrato dos dados e a transformação quebra, os bytes exatos que causaram a falha
continuam reproduzíveis em disco, em vez de perdidos num novo *download* de uma fonte já alterada.
