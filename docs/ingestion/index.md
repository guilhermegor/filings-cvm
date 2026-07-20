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
- **[Informes periódicos FIP](inf_fip.md)** — `InfTrimestralFipReader` + `InfQuadrimestralFipReader`:
  os dois informes dos FIP (CSVs soltos, particionados por ano), que **inauguram o portal root
  `fip/`**. O trimestral é o regime pré-RCVM 175 (2010–2023); o quadrimestral o substituiu no pós-175
  (2024→). Quase idênticos — só muda o identificador do fundo (`CNPJ_FUNDO` vs `TP_FUNDO_CLASSE` +
  `CNPJ_FUNDO_CLASSE`).
- **[Informe Mensal FIAGRO](inf_mensal_fiagro.md)** — 2 readers `InfMensalFiagroReader` +
  `InfMensalFiagroSubclasseReader`: o informe mensal dos FIAGRO (`inf_mensal_fiagro_AAAAMM.zip`,
  membros `inf_mensal_fiagro` + `inf_mensal_fiagro_subclasse`), que **inauguram o portal root
  `fiagro/`**. Particionado por **mês** (série a partir de `202505`); nomenclatura pós-RCVM 175
  (chave `CNPJ_Classe`).
- **[FIE](fie.md)** — 3 readers `BalanceteFieReader` (ZIP mensal, pós-RCVM 175), `BalancoFieReader`
  (ZIP anual, **descontinuado em 2020**, pré-175) e `MedidasMesFieReader` (CSV mensal solto): os três
  datasets dos Fundos de Investimento Especialmente constituídos, que **completam o portal root
  `fie/`**. Não há `FIE/CAD`. `FIE/MEDIDAS` é irmão de `FIE/DOC`, então o seu reader mora no *root*
  `fie/`.

- **[DFIN Securit (CRA/CRI) + Emissor CEPAC](securit_cepac_flat.md)** — 3 readers `DfinCraReader`,
  `DfinCriReader` (índices das demonstrações financeiras dos CRA/CRI, CSV solto anual, `Link_Download`
  não seguido) e `CadastroEmissorCepacReader` (retrato dos emissores de CEPAC — municípios — snapshot
  de URL fixa, sem `date_ref`). **Inauguram** os *portal roots* `securit/` e `emissor_cepac/`; primeira
  fatia da Wave 2 do #41.

- **[Informe Mensal OTS (Securitização)](inf_mensal_ots.md)** — 8 readers `InfMensalOts*Reader`
  (geral, ativo/passivo, classe, direitos creditórios, desembolso, fluxo de caixa, derivativos,
  cedente/devedor): as seções do informe mensal das operações de securitização não-CRA/CRI. ⚠️
  Particionado por **ano** apesar de mensal. `cedente_devedor.CNPJ` guarda CPF (dado pessoal, não
  validado como CNPJ); `Indice_Subordinacao_Data_Base` não é data. Segunda fatia da Wave 2 do #41.

- **[Informe Mensal CRA (Securitização)](inf_mensal_cra.md)** — 8 readers `InfMensalCra*Reader`
  (as mesmas 8 seções do OTS): o informe mensal das operações de **CRA** (recebíveis do
  agronegócio). ⚠️ Particionado por **ano** apesar de mensal. ⚠️ **Mesmos nomes de seção do OTS, mas
  nenhuma lista de colunas igual** (`CNPJ_Emissora` no lugar de `CNPJ_Securitizadora` nos 8;
  `direitos_creditorios` com 56 colunas contra 43) — por isso cada contract é **gerado do header
  publicado** e **pinado** a um fixture verbatim. `cedente_devedor.CNPJ` guarda CPF (dado pessoal,
  não validado como CNPJ); `Indice_Subordinacao_Data_Base` não é data. Terceira fatia da Wave 2 do
  #41.

- **[Informe Mensal CRI (Securitização)](inf_mensal_cri.md)** — 11 readers `InfMensalCri*Reader`: o
  informe mensal das operações de **CRI** (recebíveis imobiliários). ⚠️ Particionado por **ano**
  apesar de mensal. Compartilha 7 nomes de seção com CRA/OTS mas **não tem `direitos_creditorios`**
  (a seção de recebíveis é `creditos`, 51 colunas) e acrescenta 4 membros (`carteira`,
  `carteira_modificacao`, `creditos`, `responsavel`) — contracts **gerados do header** e **pinados**
  a fixtures verbatim. `cedente_devedor.CNPJ` pode guardar CPF; `Indice_Subordinacao_Data_Base` e
  `Data_LTV` (varchar no META) não são datas; `carteira_modificacao`/`responsavel` são header-only.
  **Quarta e última fatia da Wave 2 — fecha o portal root `securit/` (4/4).**

- **[Cadastro de Auditores (AUDITOR)](auditor.md)** — 2 readers `AuditorPfReader` /
  `AuditorPjReader` sobre o `cad_auditor.zip` (auditores pessoa física + firmas de auditoria).
  **Snapshot** de URL fixa, **sem `date_ref`** (molde do `CadastroFiReader`). O membro `pf` **não tem
  CPF** (identifica por `CD_CVM`+nome); `pj.CNPJ` chega mascarado. Contracts **gerados do header** e
  **pinados** a fixtures verbatim. **Inaugura o portal root `auditor/` e a primeira fatia da Wave 3
  do #41** (snapshots CAD de prestadores de serviço).

- **[Cadastro de Agentes Fiduciários (AGENTE_FIDUC)](agente_fiduc.md)** — 2 readers
  `AgenteFiducPfReader` / `AgenteFiducPjReader` sobre o `cad_agente_fiduc.zip` (agentes pessoa física
  + firmas). **Snapshot** de URL fixa, **sem `date_ref`**. O membro `pf` **não tem CPF nem `CD_CVM`**
  (identifica só pelo nome); `pj.CNPJ` chega mascarado. ⚠️ **Não é cópia do AUDITOR** — são **3
  colunas de data** em vez de 1, sem `CD_CVM`, e o `pj` acrescenta `PAIS`/`DDD_TEL`/`TEL`; contracts
  **gerados do header** e **pinados** a fixtures verbatim. **Segunda fatia da Wave 3 do #41**.

- **[Cadastro de Agentes Autônomos (AGENTE_AUTON)](agente_auton.md)** — 2 readers
  `AgenteAutonPfReader` / `AgenteAutonPjReader` sobre o `cad_agente_auton.zip` (agentes autônomos de
  investimento: pessoa física + firmas). **Snapshot** de URL fixa, **sem `date_ref`**. O `pf` **não
  tem CPF** (identifica pelo `NOME`, que pode vir em branco); `pj.CNPJ` chega mascarado. ⚠️ **Não é
  cópia dos irmãos** — acrescenta `MOTIVO_CANCEL`/`DENOM_COMERC`/`EMAIL`/`SITE_ADMIN` e usa `DDD`;
  contracts **gerados do header** e **pinados** a fixtures verbatim. **Terceira fatia da Wave 3 do
  #41**.

- **[Cadastro de Repres. de Inv. Não Residentes (INVNR)](invnr.md)** — 2 readers
  `InvnrRepresPfReader` / `InvnrRepresPjReader` sobre o `cad_invnr_repres.zip` (representantes de
  investidores não residentes: pessoa física + firmas). **Snapshot** de URL fixa, **sem `date_ref`**.
  O `pf` **não tem CPF** (identifica pelo `NOME`); `pj.CNPJ` chega mascarado. ⚠️ **Não é cópia dos
  irmãos** — acrescenta `CONTROLE_ACIONARIO`/`DDD_FAX`/`FAX`/`VL_PATRIM_LIQ`/`DT_PATRIM_LIQ` (4
  colunas de data no `pj`) e usa `DDD_TEL`; contracts **gerados do header** e **pinados** a fixtures
  verbatim. **Quarta fatia da Wave 3 do #41**.

- **[Cadastro de Intermediários (INTERMED)](intermed.md)** — 2 readers `IntermedReader` /
  `IntermedRespReader` sobre o `cad_intermed.zip` (intermediários de mercado + tabela de
  responsáveis). **Snapshot** de URL fixa, **sem `date_ref`**. ⚠️ **Os dois membros NÃO são
  `pf`/`pj`** — são o registro (28 cols) e os responsáveis (8 cols), ambos chaveados pelo `CNPJ` do
  intermediário; o membro de responsáveis tem dado pessoal (`RESP`/`EMAIL_RESP`) mas **sem CPF**.
  `CEP`/`TEL`/`FAX`/`CD_CVM` ficam `str` apesar de `numeric` no META; contracts **gerados do header**
  e **pinados** a fixtures verbatim. **Quinta fatia da Wave 3 do #41**.

- **[Cadastro de Administradores de Carteira (ADM_CART)](adm_cart.md)** — **5 readers**
  `AdmCartPfReader` / `AdmCartPjReader` / `AdmCartDiretorReader` / `AdmCartRespReader` /
  `AdmCartSociosReader` sobre o `cad_adm_cart.zip`. **Snapshot** de URL fixa, **sem `date_ref`**.
  ⚠️ **Primeiro root de 5 membros**, e **3 deles não têm nenhuma coluna de data**
  (`diretor`/`resp`/`socios` → `_DATE_COLS = ()`, tudo texto). O `pf` **não tem CNPJ nem CPF**
  (chave = `ADMIN`); os satélites têm dado pessoal mas **sem CPF** — o único `CNPJ` é o do
  administrador. Um CNPJ malformado da fonte (`00.010.354/1901-72`) é **devolvido como publicado**.
  Contracts **gerados do header** e **pinados** a fixtures verbatim. **Sexta fatia da Wave 3 do
  #41**.

- **[Cadastro de Consultores de Valores Mobiliários (CONSULTOR_VLMOB)](consultor_vlmob.md)** —
  **5 readers** `ConsultorVlmobPfReader` / `ConsultorVlmobPjReader` / `ConsultorVlmobDiretorReader` /
  `ConsultorVlmobRespReader` / `ConsultorVlmobSociosReader` sobre o `cad_consultor_vlmob.zip`.
  **Snapshot** de URL fixa, **sem `date_ref`**. Mesma forma do ADM_CART — **3 dos 5 membros sem
  nenhuma coluna de data**. ⚠️ **Não é cópia**: `pf` chaveado por `NOME` (não `ADMIN`), 7ª coluna
  `SITE_ADMIN`; `pj` com **20 cols** e **só 3 date cols** (sem `DT_PATRIM_LIQ`). Todos os CNPJ 100%
  válidos. Contracts **gerados do header** e **pinados** a fixtures verbatim. **Sétima fatia da
  Wave 3 do #41**.

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

## Automação

Dois jobs semanais vigiam a camada de leitura. Ambos **abrem/atualizam uma issue** e **nunca
reprovam o CI** — "a CVM caiu" e "o nosso contract está errado" não podem virar o mesmo check
vermelho:

- **[Deriva de contrato](contract_drift.md)** — a CVM mudou um dataset **depois** que embarcamos o
  seu `FileContract`? Compara META + header real contra os contracts. Nenhum check de PR consegue
  pegar isso, porque a mudança acontece depois do merge.
- **[Completude do portal](portal_completeness.md)** — a CVM publicou um dataset que ainda **não**
  lemos? Enumera o portal via CKAN e lista o que falta.
