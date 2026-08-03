# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this template is

A **PyPI-ready Python library starter**. A clean, importable package with CI, pre-commit,
tests, docs, and PyPI + Test-PyPI release workflows ready to go. It is scaffolded by
BlueprintX into a new project directory; the scaffold replaces the `<project_name>` package
directory and the `pyproject.toml` placeholders via `envsubst`.

## CVM Sources of Truth — one per direction

The library implements the CVM regulatory file standards in two directions, and **each
direction has its own authoritative CVM source.** Do not cross them.

**Submission (`submission/`, envio → CVM) — the XML-standards catalog page:**

> https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadroesXML.asp

Each catalog entry below links to a `PadraoXML*.asp` page (relative to that base URL) describing
one XML standard. When implementing or updating a **writer**, treat the linked CVM page as
authoritative — field names, decimal scales, and cardinalities come from there, not from this
file.

**Ingestion (`ingestion/`, leitura ← CVM) — the open-data portal:**

> https://dados.cvm.gov.br/dados/

The **readers** consume the flat open-data dumps published under this portal, **not** the
submission XML specs. Nearly every ingestion artifact comes from here, each with its own dataset
page — e.g. Perfil Mensal ingestion is <https://dados.cvm.gov.br/dataset/fi-doc-perfil_mensal>,
and the implemented readers pull from `FI/DOC/INF_DIARIO`, `FI/DOC/CDA`, `FI/DOC/LAMINA`,
`FI/CAD`, … When implementing or updating a **reader**, ground its `FileContract` in the real
downloaded artifact from the relevant dataset page (per "Standing decisions" in the sweep ledger).

The portal holds far more than is implemented; a standing task (issue **#41**) is to survey it
once the current ingestion backlog is cleared and decide what else is worth scraping.

### Two macro-sections — every solution lives in one of them

- **`submission/` (envio → CVM)** — build, validate, and serialise a document to a
  CVM-compliant file *to send* to CVM. Takes schema models (or a filled spreadsheet) → XML.
- **`ingestion/` (leitura ← CVM)** — parse and interpret a file *received/downloaded* from
  CVM back into typed models / DataFrames.

The **shared, direction-neutral schema** (Pydantic models mirroring each XML standard) lives
under `_internal/config/schemas/<standard>.py`; both sections import it. `submission/` and
`ingestion/` re-export the public names consumers need.

Each section's classes implement a private **port** (hexagonal ports-and-adapters) in
`_internal/config/ports/`: submission writers are `SubmissionWriter[TDoc]` adapters exposing
`export(doc, output_path)`; ingestion readers are `IngestionReader` adapters exposing
`read() -> pd.DataFrame`. The ports are ABCs (`ABCTypeCheckerMeta`) and stay private — consumers
import the concrete writers/readers, never the port. An `ingestion` reader of a CVM open-data
CSV consumes a **different artifact** from the same standard's submission XML, so it declares its
own `FileContract` rather than reusing the submission Pydantic schema.

**Every ingestion reader takes an optional `path_raw: Path | None = None`** at construction.
`None` → the artifact is fetched into a `TemporaryDirectory` and destroyed on exit, so nothing
persists (note: the read still transiently touches disk and needs a writable temp dir — it is not
a zero-disk read); a path → the untouched raw artifact (`.zip`, `.csv`, `.html`, `.xlsx`, …) is
written there and **kept**, before any parsing. This is the reading-side mirror of the writers' `output_path`. It is
implemented once by the shared `_internal/utils/raw_workspace.py` context manager — never
re-branch on the tempdir inside a reader. Keeping the raw bytes is what makes a downstream
datalake's bronze layer authoritative: when CVM changes a data contract and a transform breaks,
the exact bytes that broke it stay on disk, replayable, instead of being lost to a re-fetch of an
already-changed source.

### Catalog (status: ✅ implemented · ⬜ pending)

Status marks the `submission` direction unless noted; `ingestion` is tracked as it grows.

**Fundos**
- Informe Diário — ✅ **V4** (`PadraoXMLInfoDiarioNetV4.asp`) — `submission/informe_diario.py` (`InformeDiario`); schema `_internal/config/schemas/informe_diario.py` · ✅ **ingestion** FIF open-data CSV — `ingestion/fi/doc/informe_diario.py` (`InformeDiarioReader`); contract `_internal/config/contracts/informe_diario_fif.py` · ⬜ V3 (`PadraoXMLInfoDiarioNetV3.asp`) · V2 (`PadraoXMLInfoDiarioNet739.asp`) · V1 (`PadraoXMLInfoDiarioNet.asp`)
- ⬜ Informe de Fundo 157 (`PadraoXMLInf157.asp`)
- ⬜ Informe Sintético — FCCE (`PadraoXMLSintFCCE.asp`) · FITVM/FMP-FGTS CL/FIIM (`PadraoXMLSintFITVM.asp`) · FIC-FITVM (`PadraoXMLSintFIC.asp`) · FMP-FGTS/FMAI (`PadraoXMLSintOutros.asp`)
- Demonstrativo de Composição e Diversificação das Aplicações (CDA) — ✅ **ingestion** FIF open-data CSV — `ingestion/fi/doc/cda.py` (`CdaReader`); contract `_internal/config/contracts/cda_fif.py` · ⬜ **submission** V2 (`PadraoXMLCDANet.aspx`) · V3 (`PadraoXMLCDANetV3.aspx`) · V4 (`PadraoXMLCDANetV4.aspx`)
- ⬜ Demonstrativo de Fontes e Aplicações de Recursos — FAR (`PadraoXMLFAR.asp`)
- ⬜ Balanço (`PadraoXMLBalanco.asp`)
- ⬜ Balancete (`PadraoXMLBalancete.asp`)
- ⬜ Informe Quadrimestral V2 (`PadraoXMLInfoTrimV2.asp`, antigo Informe Trimestral) · Informe Trimestral V1 (`PadraoXMLInfoTrim.asp`)
- Informe Mensal FIDC — ✅ **ingestion** FIDC open-data dump (`inf_mensal_fidc_AAAAMM.zip`, **17
  membros**: Tabelas I–X + sub-tabelas X.1/X.1.1/X.2…X.7) — `ingestion/fidc/doc/inf_mensal/*`
  (`InfMensalFidcTab*Reader`, base privada `_base_inf_mensal_fidc_reader.py`); contracts
  `_internal/config/contracts/inf_mensal_fidc.py`. Inaugura o portal root `fidc/` (irmão de `fi/`)
  · ⬜ **submission** até 2019-11-01 (`PadraoXMLMensalFIDC489.asp`) · a partir de 2019-11-01 (`PadraoXMLMensalFIDC576.asp`)
- Cadastro de Fundos (CAD/FI) — **open-data only, sem padrão XML de envio** — ✅ **ingestion**
  snapshot `cad_fi.csv` — `ingestion/fi/cad/cadastro_fi.py` (`CadastroFiReader`); contract
  `_internal/config/contracts/cad_fi.py`. Sem `date_ref` (retrato do estado atual) e **sem chave
  única** (o CNPJ se repete entre regimes) · ✅ **ingestion** `cad_fi_hist.zip` (log de alterações,
  19 membros/atributos) — `ingestion/fi/cad/cad_fi_hist/cad_fi_hist_*.py` (`CadastroFiHist*Reader`, base privada
  `_base_cad_fi_hist_reader.py`); contracts em `_internal/config/contracts/cad_fi_hist.py`
  · ✅ **ingestion** `registro_fundo_classe.zip` (cadastro pós-RCVM 175, onde estão os fundos vivos) —
  `ingestion/fi/cad/registro/registro_fundo.py`, `registro_classe.py`, `registro_subclasse.py`
  (`RegistroFundoReader`, `RegistroClasseReader`, `RegistroSubclasseReader`); contracts
  `_internal/config/contracts/registro_{fundo,classe,subclasse}.py`

**Fundos Imobiliários (FII)** — portal root `fii/` ✅ **COMPLETO (4/4 datasets)**; **open-data only**
(a CVM não publica padrão XML de envio para estes informes). Não há `FII/CAD`. Os 4 datasets sob
`FII/DOC/`:
- Informe Mensal FII — ✅ **ingestion** `inf_mensal_fii_AAAA.zip` (**3 membros**: `geral`,
  `ativo_passivo`, `complemento`) — `ingestion/fii/doc/inf_mensal/*` (`InfMensalFii*Reader`, base
  privada `_base_inf_mensal_fii_reader.py`); contracts `_internal/config/contracts/inf_mensal_fii.py`.
  Inaugura o portal root `fii/`. ⚠️ **Particionado por ANO** (`_AAAA`), apesar de mensal — o
  `date_ref` seleciona o ano
- DFIN — ✅ **ingestion** `dfin_fii_AAAA.csv` (índice das demonstrações financeiras; CSV solto,
  particionado por ano) — `ingestion/fii/doc/dfin.py` (`DfinFiiReader`); contract
  `_internal/config/contracts/dfin_fii.py`. Uma linha por documento entregue; `Link_Download`
  devolvido como texto, **não seguido**
- Informe Trimestral FII — ✅ **ingestion** `inf_trimestral_fii_AAAA.zip` (**16 membros**: geral,
  complemento, ativo(+garantia), direito, imóvel(+desempenho/contrato/inquilino), terreno,
  aquisição/alienação de imóvel/terreno, rentabilidade, resultado contábil/financeiro) —
  `ingestion/fii/doc/inf_trimestral/*` (`InfTrimestralFii*Reader`, base privada
  `_base_inf_trimestral_fii_reader.py`); contracts `_internal/config/contracts/inf_trimestral_fii.py`.
  Particionado por ano
- Informe Anual FII — ✅ **ingestion** `inf_anual_fii_AAAA.zip` (**12 membros**: geral, complemento,
  ativo adquirido/transação/valor contábil, distribuição de cotistas, diretor responsável,
  experiência profissional, prestador de serviço, processo(+semelhante), representante de cotistas)
  — `ingestion/fii/doc/inf_anual/*` (`InfAnualFii*Reader`, base privada
  `_base_inf_anual_fii_reader.py`); contracts `_internal/config/contracts/inf_anual_fii.py`.
  ⚠️ Contém **CPF** (dado pessoal, texto exato, nunca validado como CNPJ) e um `Link_Download_Anexo`
  **não seguido**. **Com este, o portal root `fii/` está completo (4/4 datasets)**

**Fundos de Investimento em Participações (FIP)** — portal root `fip/` ✅ **COMPLETO (2/2 datasets)**;
**open-data only** (a CVM não publica padrão XML de envio). Não há `FIP/CAD`. Os 2 datasets sob
`FIP/DOC/`, ambos CSVs soltos particionados por ano (um reader cada):
- Informe Trimestral FIP — ✅ **ingestion** `inf_trimestral_fip_AAAA.csv` (54 colunas, regime
  **pré-RCVM 175**, série 2010–2023) — `ingestion/fip/doc/inf_trimestral.py` (`InfTrimestralFipReader`);
  contract `_internal/config/contracts/inf_trimestral_fip.py`. Chaveado por `CNPJ_FUNDO`. Inaugura o
  portal root `fip/`
- Informe Quadrimestral FIP — ✅ **ingestion** `inf_quadrimestral_fip_AAAA.csv` (55 colunas, regime
  **pós-RCVM 175**, a partir de 2024) — `ingestion/fip/doc/inf_quadrimestral.py`
  (`InfQuadrimestralFipReader`); contract `_internal/config/contracts/inf_quadrimestral_fip.py`.
  Idêntico ao trimestral **exceto** as 2 primeiras colunas: `TP_FUNDO_CLASSE` + `CNPJ_FUNDO_CLASSE`
  (split fundo/classe da RCVM 175) no lugar de `CNPJ_FUNDO`. **Com este, o portal root `fip/` está
  completo (2/2 datasets)**

**Fundos de Investimento nas Cadeias Produtivas Agroindustriais (FIAGRO)** — portal root `fiagro/`;
**open-data only** (a CVM não publica padrão XML de envio). Sob `FIAGRO/DOC/`:
- Informe Mensal FIAGRO — ✅ **ingestion** `inf_mensal_fiagro_AAAAMM.zip` (**2 membros**: informe +
  subclasse) — `ingestion/fiagro/doc/inf_mensal/*` (`InfMensalFiagroReader`,
  `InfMensalFiagroSubclasseReader`, base privada `_base_inf_mensal_fiagro_reader.py`); contracts
  `_internal/config/contracts/inf_mensal_fiagro.py`. Inaugura o portal root `fiagro/`.
  **Particionado por mês** (`_AAAAMM`, série a partir de 2025-05); nomenclatura pós-RCVM 175 (chave
  `CNPJ_Classe`). O informe (133 colunas) traz uma linha por classe/mês; a subclasse (6 colunas) é
  longa. Grafias da CVM preservadas verbatim (`Provisoes_Contigencias`, `A_Vencer_Acima1080_Dias`)

**Fundos de Investimento Especialmente constituídos (FIE)** — portal root `fie/` ✅ **COMPLETO
(3/3 datasets)**; **open-data only** (a CVM não publica padrão XML de envio). **Não há `FIE/CAD`**
(tanto `DADOS/` quanto `META/` estão vazios). Os 3 datasets, um reader cada (6 colunas, grão único):
- Balancete FIE — ✅ **ingestion** `balancete_fie_AAAAMM.zip` (ZIP de 1 membro, **mensal** a partir de
  202401) — `ingestion/fie/doc/balancete.py` (`BalanceteFieReader`); contract
  `_internal/config/contracts/balancete_fie.py`. Balancete contábil (uma linha por fundo/classe × mês
  × conta); nomenclatura **pós-RCVM 175** (`TP_FUNDO_CLASSE`/`CNPJ_FUNDO_CLASSE`). Inaugura `fie/`
- Balanço FIE — ✅ **ingestion** `balanco_fie_AAAA.zip` (ZIP de 1 membro, **anual**) —
  `ingestion/fie/doc/balanco.py` (`BalancoFieReader`); contract `_internal/config/contracts/balanco_fie.py`.
  Balanço patrimonial; **descontinuado em 2020** (série 2005–2020), nomenclatura **pré-175**
  (`TP_FUNDO`/`CNPJ_FUNDO`)
- Medidas Mensais FIE — ✅ **ingestion** `medidas_mes_fie_AAAAMM.csv` (**CSV solto, não ZIP**, mensal)
  — `ingestion/fie/medidas.py` (`MedidasMesFieReader`); contract `_internal/config/contracts/medidas_mes_fie.py`.
  Patrimônio líquido + nº de cotistas; `FIE/MEDIDAS` é irmão de `FIE/DOC`, então o reader mora no root
  `fie/`. **Com este, o portal root `fie/` está completo (3/3)** e a Wave 1 do #41 encerra
  (FIDC→FII→FIP→FIAGRO→FIE)

**Securitização (SECURIT)** — portal root `securit/` ✅ **COMPLETO (4/4 datasets)**; **open-data
only** (a CVM não publica padrão XML de envio). Não há `SECURIT/CAD`. Encerra a Wave 2 do #41. Sob
`SECURIT/DOC/`:
- DFIN CRA — ✅ **ingestion** `dfin_cra_AAAA.csv` (CSV solto, anual) — `ingestion/securit/doc/dfin_cra.py`
  (`DfinCraReader`); contract `_internal/config/contracts/dfin_cra.py`. Índice das demonstrações
  financeiras dos CRA (uma linha por documento); `Link_Download` devolvido como texto, **não seguido**.
  Inaugura o portal root `securit/`
- DFIN CRI — ✅ **ingestion** `dfin_cri_AAAA.csv` (CSV solto, anual) — `ingestion/securit/doc/dfin_cri.py`
  (`DfinCriReader`); contract `_internal/config/contracts/dfin_cri.py`. Idêntico ao CRA (9 colunas),
  para os CRI
- INF_MENSAL_OTS — ✅ **ingestion** `inf_mensal_ots_AAAA.zip` (**8 membros**: geral, ativo_passivo,
  classe, direitos_creditorios, desembolso, fluxo_caixa, derivativos, cedente_devedor) —
  `ingestion/securit/doc/inf_mensal_ots/*` (`InfMensalOts*Reader`, base privada
  `_base_inf_mensal_ots_reader.py`); contracts `_internal/config/contracts/inf_mensal_ots.py`.
  Operações de securitização não-CRA/CRI. **Particionado por ANO apesar de mensal** (`date_ref` = o
  ano). Armadilhas honradas: `cedente_devedor.CNPJ` guarda CPF (não é coluna de CNPJ; é dado
  pessoal), `Indice_Subordinacao_Data_Base` NÃO é data, e a grafia `Outras_Contigencias_Relevantes`
  é preservada verbatim
- INF_MENSAL_CRA — ✅ **ingestion** `inf_mensal_cra_AAAA.zip` (**8 membros**, os mesmos nomes de seção
  do OTS: geral, ativo_passivo, classe, direitos_creditorios, desembolso, fluxo_caixa, derivativos,
  cedente_devedor) — `ingestion/securit/doc/inf_mensal_cra/*` (`InfMensalCra*Reader`, base privada
  `_base_inf_mensal_cra_reader.py`); contracts `_internal/config/contracts/inf_mensal_cra.py`.
  Operações de **CRA** (recebíveis do agronegócio). **Particionado por ANO apesar de mensal**.
  ⚠️ **Mesmos nomes de seção do OTS e NENHUMA lista de colunas igual** — o CRA é agro:
  `CNPJ_Securitizadora`→`CNPJ_Emissora` nos 8; `direitos_creditorios` com **56** colunas contra 43
  (13 baldes agro); `derivativos` com `*_Commodities_Agricolas`; `geral` derruba o bloco de
  contingências do OTS (logo a typo `Outras_Contigencias_Relevantes` **não existe aqui**). Copiar os
  contracts do irmão embarcaria 8 errados **com todos os testes verdes** → cada contract é **gerado
  do header publicado** e **pinado** a `tests/fixtures/inf_mensal_cra/*_header.csv` (bytes verbatim
  da CVM — o único oráculo não-tautológico). Armadilhas honradas: `cedente_devedor.CNPJ` **não é
  coluna de CNPJ** (guarda CPF, `'0'`, `','`, valores malformados e dois ids na mesma célula),
  `Indice_Subordinacao_Data_Base` NÃO é data, e as 3 colunas `CNPJ_*` 100% vazias de `geral` ficam
  fora de `tuple_cnpj_cols`
- INF_MENSAL_CRI — ✅ **ingestion** `inf_mensal_cri_AAAA.zip` (**11 membros**: geral, ativo_passivo,
  classe, creditos, carteira, carteira_modificacao, desembolso, fluxo_caixa, derivativos,
  cedente_devedor, responsavel) — `ingestion/securit/doc/inf_mensal_cri/*` (`InfMensalCri*Reader`,
  base privada `_base_inf_mensal_cri_reader.py`); contracts `_internal/config/contracts/inf_mensal_cri.py`.
  Operações de **CRI** (recebíveis imobiliários). **Particionado por ANO apesar de mensal**.
  ⚠️ **Compartilha 7 nomes de seção com CRA/OTS mas NÃO é cópia** — não tem `direitos_creditorios`
  (a seção de recebíveis é `creditos`, 51 cols) e acrescenta 4 membros (`carteira`,
  `carteira_modificacao`, `creditos`, `responsavel`); 5 das 7 seções compartilhadas diferem do CRA e
  2 (`desembolso`, `cedente_devedor`) são de fato **idênticas** (estruturas genéricas — a coincidência
  é da fonte, provada pelo header pinado). Contracts **gerados do header** e **pinados** a
  `tests/fixtures/inf_mensal_cri/*_header.csv`. Armadilhas honradas: `cedente_devedor.CNPJ` pode ser
  CPF (fora de `tuple_cnpj_cols`), `Indice_Subordinacao_Data_Base` e `Data_LTV` (varchar no META) NÃO
  são datas, `carteira_modificacao`/`responsavel` são **header-only** em 2025 → `tuple_cnpj_cols`
  vazio (senão um arquivo legitimamente vazio falharia). **Com este, o root `securit/` está completo
  (4/4) e a Wave 2 do #41 encerra**

**Emissor de CEPAC (EMISSOR_CEPAC)** — portal root `emissor_cepac/`; **open-data only**. Publica só
um cadastro:
- Cadastro de Emissor CEPAC — ✅ **ingestion** `cad_emissor_cepac.csv` (CSV solto, **snapshot de URL
  fixa, sem `date_ref`**) — `ingestion/emissor_cepac/cad/cadastro.py` (`CadastroEmissorCepacReader`);
  contract `_internal/config/contracts/cad_emissor_cepac.py`. Retrato dos emissores de CEPAC
  (municípios). Como o `cad_fi.csv`, a CVM sobrescreve no lugar → só um `path_raw` persistido guarda o
  estado. Inaugura o portal root `emissor_cepac/`

**META (metadados publicados pela CVM)** — ✅ **ingestion**, **45 readers** (`Meta*Reader`), um por
dataset, em `ingestion/<root>/…/<dataset>/meta.py` sobre a base privada
`ingestion/_base_meta_reader.py`; parser puro `_internal/utils/meta_parser.py`; contracts
`_internal/config/contracts/meta.py` (45 instâncias de um factory sobre uma tupla compartilhada —
o formato do frame é **nosso** e idêntico; só o `source_key` difere, prefixado `meta_`). Doc:
`docs/ingestion/meta.md`. Cada META é texto em blocos (`Campo:`/`Descrição`/`Tipo Dados`),
**ISO-8859-1 + CRLF**, num `.txt` solto (17) ou `.zip` multi-membro (28); volta como **um frame
longo** com o membro em `section`. **Sem `date_ref`** (URL fixa, a CVM sobrescreve no lugar).
⚠️ **Estes números são MEDIDOS do código** (`45 = 17 .txt + 28 .zip`, e 45 contracts — o 46º nome
`META_*` em `meta.py` é o `META_COLUMNS`, a tupla compartilhada, não um contract). O gate
`test_meta_readers.py` deriva a verdade de `__all__` mas cobre **`docs/ingestion/meta.md` e
`docs/api.md`, NÃO este arquivo** — então **atualize esta contagem no mesmo commit do reader novo**,
senão ela estagna sem nada ficar vermelho (já aconteceu duas vezes: ficou em 37 com 38 exportados,
e o parêntese dos números medidos ficou em `38 = 16 + 22` enquanto o texto acima já dizia 42).
**Ao corrigir, RE-MEDIR do código, nunca incrementar** — foi re-medindo que se viu que os dois
números do mesmo parágrafo discordavam.
⚠️ **Três fatos da fonte, honrados verbatim e nunca "consertados":**
  1. **A CVM trunca o nome do campo em exatamente 50 caracteres** (provado 8/8 no CRA; o header real
     vai até 60). Logo o META **não pode ser gate duro de nomes** — reconciliar é do consumidor
     (#98) e tem de ser *truncation-aware* (`header[:50] == meta`).
  2. **A ordem do META nunca é a do arquivo real** (0/8 seções; `meta_cad_fi.txt` é alfabético) → o
     **header real segue sendo a fonte da ordem** e dos nomes longos. Oráculos complementares.
  3. **A URL é constante por dataset, jamais derivada:** os nomes são irregulares
     (`meta_cda_fi_txt.zip`, infixo `_txt`) e **`meta_cad_fi.txt` (41 campos = `cad_fi`) vs
     `meta_cad_fi.zip` (19 membros = `cad_fi_hist`) são datasets DIFERENTES** com o mesmo radical —
     uma regra "derive o nome"/"prefira o zip" entregaria o metadado errado com os testes verdes.
  Inclui `MetaInfMensalCriReader` (`meta_inf_mensal_cri.zip`, 11 membros), que fecha o root
  `securit/` junto com os readers do CRI. `Data_LTV` do CRI é declarado **`varchar`** no META
  (confirmou o `str`), e `Indice_Subordinacao_Data_Base` é **`numeric`** — o META como oráculo de tipo

**Lâmina de Fundos**
- Lâmina — ✅ **ingestion** carteira FIF open-data CSV (`lamina_fi_carteira_*`, o membro de alocação
  por tipo de ativo do dump `lamina_fi_AAAAMM.zip`) — `ingestion/fi/doc/lamina/lamina_carteira.py`
  (`LaminaCarteiraReader`); contract `_internal/config/contracts/lamina_carteira_fif.py` ·
  ✅ **ingestion** lâmina proper (`lamina_fi_*`, 78 colunas) — `ingestion/fi/doc/lamina/lamina.py`
  (`LaminaReader`); contract `_internal/config/contracts/lamina_fif.py` ·
  ⬜ **ingestion** `rentab_ano_*` / `rentab_mes_*` (membros irmãos do mesmo ZIP) ·
  ⬜ **submission** V3 (`PadraoXMLLaminaV3.asp`) · V2 (`PadraoXMLLaminaV2.asp`) · V1 (`PadraoXMLLamina.asp`)

**Documentos Eventuais (FI/DOC/EVENTUAL)** — **open-data only** (a CVM não publica padrão XML de
envio; é o registro do que foi entregue, não um informe):
- Documentos Eventuais — ✅ **ingestion** `eventual_fi_AAAA.csv` (**CSV solto**, não ZIP, 11 cols,
  **186.453 linhas / 50,91 MB em 2025**, série ao menos 2020–2026) —
  `ingestion/fi/doc/eventual/eventual.py` (`EventualFiReader`); contract
  `_internal/config/contracts/eventual_fi.py`, **gerado do header e pinado** a
  `tests/fixtures/eventual_fi/eventual_fi_header.csv`. **Particionado por ANO**. ⚠️ **É um ÍNDICE,
  não o documento** — `LINK_ARQ` (portal *fundosweb*, host distinto do RAD usado pelo IPE/CGVN)
  volta como **texto, não seguido**. Nomenclatura **pós-RCVM 175** (`TP_FUNDO_CLASSE`/
  `CNPJ_FUNDO_CLASSE` + `ID_SUBCLASSE`). ⚠️⚠️ **NÃO é cópia do `DfinFiiReader`** — os dois são
  índices anuais de documentos em CSV solto e **7 colunas significam a mesma coisa com nomes TODOS
  diferentes** (`TP_FUNDO_CLASSE`×`Tipo_Fundo_Classe`, `DT_COMPTC`×`Data_Referencia`,
  `LINK_ARQ`×`Link_Download`, …): **paralelismo semântico não é regra de nomenclatura**, anti-cópia
  pinada nas 2 direções. ⚠️ `ID_DOC` é `int` na META e fica **`str`** (identificador; um numérico
  apaga zero à esquerda em silêncio). ⚠️ **4 colunas parcialmente vazias** (`ID_SUBCLASSE` 96,8%,
  `RESULTADO_AUDITORIA` 83,5%, `ID_DOC` 75,6%, `NM_ARQ` 24,4%) — dependem do tipo de documento;
  vazio volta vazio. ⚠️ META é **`.txt` solto** (as outras 3 grafias dão 404)

**Perfil Mensal e Extrato das Informações sobre o Fundo**
- ✅ **Perfil Mensal — V4** (`PadraoXMLPerfilV4.asp`) — `submission/perfil_mensal.py` (`PerfilMensal`); schema `_internal/config/schemas/perfil_mensal.py`
- ⬜ Perfil Mensal — V3 (`PadraoXMLPerfilV3.asp`) · 739 (`PadraoXMLPerfil739.asp`) · original (`PadraoXMLPerfil.asp`)
- ⬜ Extrato das Informações sobre o Fundo — V3 (`PadraoXMLInfExtratoV3.asp`) · V2 (`PadraoXMLInfExtratoV2.asp`) · V1/450 (`PadraoXMLInfExtrato450.asp`)

**Auditores** — portal root `auditor/`; **open-data only** para o cadastro (a CVM não publica padrão
XML de envio para o registro). Sob `AUDITOR/CAD/`:
- Cadastro de Auditores — ✅ **ingestion** `cad_auditor.zip` (**2 membros**: `pf`, `pj`) —
  `ingestion/auditor/cad/{auditor_pf,auditor_pj}.py` (`AuditorPfReader`, `AuditorPjReader`, base
  privada `_base_auditor_reader.py`); contracts `_internal/config/contracts/cad_auditor.py`, pinados
  aos headers em `tests/fixtures/cad_auditor/*_header.csv`. **Snapshot** de URL fixa, **sem
  `date_ref`** (molde do `CadastroFiReader`). O membro `pf` **não tem CPF** (identifica por
  `CD_CVM`+nome); `pj.CNPJ` chega mascarado. **Inaugura o portal root `auditor/` e a primeira fatia
  da Wave 3 do #41** (snapshots CAD de prestadores de serviço)
- ⬜ **submission** Informe Anual de Auditor (`PadraoXMLAuditorAnual.asp`)

**Agentes Fiduciários** — portal root `agente_fiduc/`; **open-data only** (a CVM não publica padrão
XML de envio). Não há submission. Sob `AGENTE_FIDUC/CAD/`:
- Cadastro de Agentes Fiduciários — ✅ **ingestion** `cad_agente_fiduc.zip` (**2 membros**: `pf`, `pj`)
  — `ingestion/agente_fiduc/cad/{agente_fiduc_pf,agente_fiduc_pj}.py` (`AgenteFiducPfReader`,
  `AgenteFiducPjReader`, base privada `_base_agente_fiduc_reader.py`); contracts
  `_internal/config/contracts/cad_agente_fiduc.py`, pinados aos headers em
  `tests/fixtures/cad_agente_fiduc/*_header.csv`. **Snapshot** de URL fixa, **sem `date_ref`**. O
  membro `pf` **não tem CPF nem `CD_CVM`** (identifica só pelo nome); `pj.CNPJ` chega mascarado.
  ⚠️ **Não é cópia do AUDITOR** — **3 colunas de data** (`DT_REG`/`DT_CANCEL`/`DT_INI_SIT`) em vez de
  1, sem `CD_CVM`, `pj` acrescenta `PAIS`/`DDD_TEL`/`TEL`. **Segunda fatia da Wave 3 do #41**

**Agentes Autônomos de Investimento** — portal root `agente_auton/`; **open-data only** (a CVM não
publica padrão XML de envio). Sob `AGENTE_AUTON/CAD/`:
- Cadastro de Agentes Autônomos — ✅ **ingestion** `cad_agente_auton.zip` (**2 membros**: `pf`, `pj`)
  — `ingestion/agente_auton/cad/{agente_auton_pf,agente_auton_pj}.py` (`AgenteAutonPfReader`,
  `AgenteAutonPjReader`, base privada `_base_agente_auton_reader.py`); contracts
  `_internal/config/contracts/cad_agente_auton.py`, pinados aos headers em
  `tests/fixtures/cad_agente_auton/*_header.csv`. **Snapshot** de URL fixa, **sem `date_ref`**. O
  `pf` (6 cols, ~49k linhas) **não tem CPF** (chave = `NOME`, que pode vir em branco); `pj` (19 cols)
  tem `CNPJ` mascarado. ⚠️ **Não é cópia dos irmãos** — acrescenta
  `MOTIVO_CANCEL`/`DENOM_COMERC`/`EMAIL`/`SITE_ADMIN`, usa `DDD` (não `DDD_TEL`). **Terceira fatia da
  Wave 3 do #41**

**Representantes de Investidores Não Residentes** — portal root `invnr/`; **open-data only** (a CVM
não publica padrão XML de envio). Sob `INVNR/CAD/`:
- Cadastro de Representantes de INVNR — ✅ **ingestion** `cad_invnr_repres.zip` (**2 membros**: `pf`,
  `pj`) — `ingestion/invnr/cad/{invnr_repres_pf,invnr_repres_pj}.py` (`InvnrRepresPfReader`,
  `InvnrRepresPjReader`, base privada `_base_invnr_repres_reader.py`); contracts
  `_internal/config/contracts/cad_invnr_repres.py`, pinados aos headers em
  `tests/fixtures/cad_invnr_repres/*_header.csv`. **Snapshot** de URL fixa, **sem `date_ref`**. O
  `pf` (6 cols) **não tem CPF** (chave = `NOME`); `pj` (23 cols) tem `CNPJ` mascarado. ⚠️ **Não é
  cópia dos irmãos** — acrescenta `CONTROLE_ACIONARIO`/`DDD_FAX`/`FAX`/`VL_PATRIM_LIQ`/`DT_PATRIM_LIQ`
  (4 date cols no `pj` contra 3 no `pf`), usa `DDD_TEL` (não `DDD`). ⚠️ `CEP`/`TEL`/`FAX` são
  `numeric` no META mas ficam `str` (identificadores, não quantidades — o `CEP` já chega sem o zero à
  esquerda). **Quarta fatia da Wave 3 do #41**

**Intermediários** — portal root `intermed/`; **open-data only** (a CVM não publica padrão XML de
envio). Sob `INTERMED/CAD/`:
- Cadastro de Intermediários — ✅ **ingestion** `cad_intermed.zip` (**2 membros**) —
  `ingestion/intermed/cad/{intermed,intermed_resp}.py` (`IntermedReader`, `IntermedRespReader`, base
  privada `_base_intermed_reader.py`); contracts `_internal/config/contracts/cad_intermed.py`,
  pinados aos headers em `tests/fixtures/cad_intermed/*_header.csv`. **Snapshot** de URL fixa, **sem
  `date_ref`**. ⚠️ **Os 2 membros NÃO são split `pf`/`pj`** — são o registro do intermediário
  (`cad_intermed.csv`, 28 cols, 4 date cols) e a tabela de responsáveis (`cad_intermed_resp.csv`, 8
  cols, 2 date cols), **ambos chaveados pelo `CNPJ` do intermediário** (mascarado). O `resp` tem dado
  pessoal (`RESP`/`EMAIL_RESP`) mas **sem coluna de CPF** → `tuple_cnpj_cols=("CNPJ",)` nos dois.
  ⚠️ `CEP`/`TEL`/`FAX`/`CD_CVM` são `numeric`/`char` no META mas ficam `str`. **Quinta fatia da Wave
  3 do #41**

**Administradores de Carteira** — portal root `adm_cart/`; **open-data only** (a CVM não publica
padrão XML de envio). Sob `ADM_CART/CAD/`:
- Cadastro de Administradores de Carteira — ✅ **ingestion** `cad_adm_cart.zip` (**5 membros**) —
  `ingestion/adm_cart/cad/{adm_cart_pf,adm_cart_pj,adm_cart_diretor,adm_cart_resp,adm_cart_socios}.py`
  (`AdmCartPfReader`, `AdmCartPjReader`, `AdmCartDiretorReader`, `AdmCartRespReader`,
  `AdmCartSociosReader`, base privada `_base_adm_cart_reader.py`); contracts
  `_internal/config/contracts/cad_adm_cart.py`, pinados aos headers em
  `tests/fixtures/cad_adm_cart/*_header.csv`. **Snapshot** de URL fixa, **sem `date_ref`**.
  **Primeiro root de 5 membros.** ⚠️ **3 dos 5 membros não têm NENHUMA coluna de data**
  (`diretor`/`resp`/`socios` → `_DATE_COLS=()`, tudo texto) — a primeira ocorrência dessa forma. O
  `pf` (7 cols) **não tem CNPJ nem CPF** (chave = `ADMIN`); os satélites têm dado pessoal
  (`DIRETOR`/`RESP`/`SOCIOS`) mas **sem CPF** → `tuple_cnpj_cols=("CNPJ",)` (o do administrador). O
  `pj` (24 cols) usa `DDD` (não `DDD_TEL`). ⚠️ Um CNPJ malformado da fonte (`00.010.354/1901-72` em
  `pj`+`resp`) é **honrado como publicado** (o check exige ao menos um válido). `CEP`/`TEL` `numeric`
  no META mas `str`. **Sexta fatia da Wave 3 do #41**

**Consultores de Valores Mobiliários** — portal root `consultor_vlmob/`; **open-data only** (a CVM
não publica padrão XML de envio). Sob `CONSULTOR_VLMOB/CAD/`:
- Cadastro de Consultores de Valores Mobiliários — ✅ **ingestion** `cad_consultor_vlmob.zip`
  (**5 membros**) — `ingestion/consultor_vlmob/cad/consultor_vlmob_{pf,pj,diretor,resp,socios}.py`
  (`ConsultorVlmobPfReader`, `ConsultorVlmobPjReader`, `ConsultorVlmobDiretorReader`,
  `ConsultorVlmobRespReader`, `ConsultorVlmobSociosReader`, base privada
  `_base_consultor_vlmob_reader.py`); contracts `_internal/config/contracts/cad_consultor_vlmob.py`,
  pinados aos headers em `tests/fixtures/cad_consultor_vlmob/*_header.csv`. **Snapshot** de URL fixa,
  **sem `date_ref`**. Mesma forma do ADM_CART: **3 dos 5 membros sem NENHUMA coluna de data**
  (`diretor`/`resp`/`socios` → `_DATE_COLS=()`). ⚠️ **Não é cópia do ADM_CART** — `pf` chaveado por
  `NOME` (não `ADMIN`) com 7ª coluna `SITE_ADMIN` (não `CATEG_REG`); `pj` com **20 cols** (não 24),
  sem `CATEG_REG`/`SUBCATEG_REG`/`VL_PATRIM_LIQ`/`DT_PATRIM_LIQ` → **só 3 date cols**. `pf` **sem
  CNPJ nem CPF**; satélites com dado pessoal mas **sem CPF** → `tuple_cnpj_cols=("CNPJ",)` (o do
  consultor). Todos os CNPJ 100% válidos. `CEP`/`TEL` `numeric` no META mas `str`. **Sétima fatia da
  Wave 3 do #41**

**Administradores de FII** — portal root `adm_fii/`; **open-data only** (a CVM não publica padrão XML
de envio). Sob `ADM_FII/CAD/`:
- Cadastro de Administradores de FII — ✅ **ingestion** `cad_adm_fii.csv` (**CSV solto**, não ZIP,
  18 cols) — `ingestion/adm_fii/cad/cadastro/cadastro.py` (`CadastroAdmFiiReader`); contract
  `_internal/config/contracts/cad_adm_fii.py` (verificado contra os bytes reais). **Snapshot** de URL
  fixa, **sem `date_ref`** (molde do `CadastroFiReader` / `CadastroEmissorCepacReader`). ⚠️ **Único
  membro da Wave 3 num CSV solto** — 1 reader, sem o multi-membro dos irmãos. 3 colunas de data
  (`DT_REG`/`DT_CANCEL`/`DT_INI_SIT`; `MOTIVO_CANCEL` é TEXTO, não data); chaveado por `CNPJ`
  (mascarado), **sem coluna de CPF**. `CEP`/`DDD`/`TEL` `numeric` no META mas `str`; usa `DDD` (não
  `DDD_TEL`). **Oitava e última fatia da Wave 3 do #41 — ENCERRA A WAVE 3 (8/8)**

**Companhias Estrangeiras** — portal root `cia_estrang/`; **open-data only** (a CVM não publica
padrão XML de envio). Sob `CIA_ESTRANG/CAD/`:
- Cadastro de Companhias Estrangeiras — ✅ **ingestion** `cad_cia_estrang.csv` (**CSV solto**, não
  ZIP, **49 cols**) — `ingestion/cia_estrang/cad/cadastro/cadastro.py` (`CadastroCiaEstrangReader`);
  contract `_internal/config/contracts/cad_cia_estrang.py`, **gerado do header e pinado** a
  `tests/fixtures/cad_cia_estrang/cad_cia_estrang_header.csv` (49 cols = risco de transcrição).
  **Snapshot** de URL fixa, **sem `date_ref`** (molde do `CadastroAdmFiiReader`). ⚠️ **7 colunas de
  data** (`DT_REG`/`DT_CONST`/`DT_CANCEL`/`DT_INI_SIT`/`DT_INI_CATEG`/`DT_INI_SIT_EMISSOR`/
  `DT_INI_RESP`; `MOTIVO_CANCEL` é TEXTO). ⚠️ **Duas colunas de CNPJ** (`CNPJ` da companhia +
  `CNPJ_AUDITOR`) → `tuple_cnpj_cols=("CNPJ","CNPJ_AUDITOR")`. `RESP` tem nome de pessoa mas **sem
  coluna de CPF**. `CD_CVM`/`CEP`/`TEL`/`FAX`/`DDD_*`/`CD_PAIS_*` `numeric`/`char` no META mas `str`.
  **ABRE A WAVE 4 do #41** (companhias/ofertas)

**Companhias Incentivadas** — portal root `cia_incent/`; **open-data only** (a CVM não publica padrão
XML de envio). Sob `CIA_INCENT/CAD/`:
- Cadastro de Companhias Incentivadas — ✅ **ingestion** `cad_cia_incent.csv` (**CSV solto**, não ZIP,
  **47 cols**, ~3.570 linhas) — `ingestion/cia_incent/cad/cadastro/cadastro.py`
  (`CadastroCiaIncentReader`); contract `_internal/config/contracts/cad_cia_incent.py`, **gerado do
  header e pinado** a `tests/fixtures/cad_cia_incent/cad_cia_incent_header.csv`. **Snapshot** de URL
  fixa, **sem `date_ref`**. ⚠️ **Não é cópia do CIA_ESTRANG** — acrescenta `ST_CIA_INCENT_REG`, **não
  tem** `PAIS_ORIGEM`/`CD_PAIS_*`, usa `MUN`/`UF` (não `CIDADE`/`ESTADO`). **7 colunas de data**
  (`MOTIVO_CANCEL` é TEXTO; ⚠️ `DT_INI_CATEG` chega 100% vazia mas é data por contrato → tudo `NaT`).
  **Duas colunas de CNPJ** (`CNPJ` + `CNPJ_AUDITOR`); `RESP` sem CPF. **Segunda fatia da Wave 4 do
  #41**

**Coordenadores de Oferta** — portal root `coord_oferta/`; **open-data only** (a CVM não publica
padrão XML de envio). Sob `COORD_OFERTA/CAD/`:
- Cadastro de Coordenadores de Oferta — ✅ **ingestion** `cad_coord_oferta.zip` (**2 membros**) —
  `ingestion/coord_oferta/cad/{coord_oferta,coord_oferta_resp}.py` (`CoordOfertaReader`,
  `CoordOfertaRespReader`, base privada `_base_coord_oferta_reader.py`); contracts
  `_internal/config/contracts/cad_coord_oferta.py`, pinados aos headers em
  `tests/fixtures/cad_coord_oferta/*_header.csv`. **Snapshot** de URL fixa, **sem `date_ref`**.
  ⚠️ **Os 2 membros NÃO são split `pf`/`pj`** (molde do INTERMED) — são o registro
  (`cad_coord_oferta.csv`, 25 cols, 4 date cols) e a tabela de responsáveis
  (`cad_coord_oferta_resp.csv`, 6 cols, 2 date cols), **ambos chaveados pelo `CNPJ` do coordenador**
  (100% válidos). O `resp` tem dado pessoal (`RESP`) mas **sem coluna de CPF** →
  `tuple_cnpj_cols=("CNPJ",)` nos dois. ⚠️ **A META é um `.zip` de 2 membros** (`.txt` dá **404**) —
  a URL é constante por dataset, jamais derivada — e as `section` voltam **assimétricas**
  (`cad_coord_oferta` + `resp`), como no INTERMED. `CD_CVM`/`CEP`/`TEL`/`FAX`/`DDD_*`
  `numeric`/`char` no META mas `str`. **Terceira fatia da Wave 4 do #41; primeiro ZIP multi-membro
  da onda**

**Plataformas de Crowdfunding** — portal root `crowdfunding/`; **open-data only** (a CVM não publica
padrão XML de envio). Sob `CROWDFUNDING/CAD/`:
- Cadastro de Plataformas de Crowdfunding — ✅ **ingestion** `cad_crowdfunding.zip` (**3 membros**) —
  `ingestion/crowdfunding/cad/{crowdfunding,crowdfunding_adm_resp,crowdfunding_socios}.py`
  (`CrowdfundingReader`, `CrowdfundingAdmRespReader`, `CrowdfundingSociosReader`, base privada
  `_base_crowdfunding_reader.py`); contracts `_internal/config/contracts/cad_crowdfunding.py`,
  pinados aos headers em `tests/fixtures/cad_crowdfunding/*_header.csv`. **Snapshot** de URL fixa,
  **sem `date_ref`**. ⚠️ **Não é split `pf`/`pj`** — registro (17 cols, 2 date cols) + 2 satélites
  (`adm_resp` e `socios`, 2 cols cada), **todos chaveados pelo `CNPJ` da plataforma** (100%
  válidos). ⚠️ **Os 2 satélites não têm NENHUMA coluna de data** (`_DATE_COLS=()`, forma do
  ADM_CART); têm dado pessoal (`ADM_RESP`; `SOCIO` mistura PF e PJ) mas **sem coluna de CPF**.
  ⚠️ **O registro é mais ENXUTO que os irmãos** — **sem** `DT_CANCEL`/`MOTIVO_CANCEL`/`CD_CVM`, e
  grafa `WEBSITE` (não `SITE_WEB`) e `DDD` (não `DDD_TEL`); copiar o COORD_OFERTA embarcaria colunas
  erradas com os testes verdes → anti-cópia pinada por teste. ⚠️ **A META é um `.zip` de 3 membros**
  (o `.txt` dá **404**) com `section` **assimétricas** (`cad_crowdfunding` + `adm_resp` + `socios`).
  `CEP`/`TEL`/`DDD` `numeric` no META mas `str`. **Quarta fatia da Wave 4 do #41**

**Ofertas de Distribuição de Valores Mobiliários** — portal root `oferta/`; **open-data only** (a CVM
não publica padrão XML de envio). Sob `OFERTA/DISTRIB/`:
- Ofertas de Distribuição — ✅ **ingestion** `oferta_distribuicao.zip` (**2 membros por regime**) —
  `ingestion/oferta/distrib/{oferta_distribuicao,oferta_resolucao_160}.py` (`OfertaDistribuicaoReader`,
  `OfertaResolucao160Reader`, base privada `_base_oferta_reader.py`); contracts
  `_internal/config/contracts/oferta_distribuicao.py`, **gerados dos headers e pinados** a
  `tests/fixtures/oferta_distribuicao/*_header.csv` (76/71 cols = risco de transcrição). **Snapshot**
  de URL fixa, **sem `date_ref`**. ⚠️ **Os 2 membros NÃO são registro+satélite** — são o registro
  histórico pré-RCVM 160 (`oferta_distribuicao.csv`, 76 cols, 9 date cols, ~48,9k linhas) e os
  requerimentos RCVM 160 (`oferta_resolucao_160.csv`, 71 cols, 3 date cols, ~13,9k linhas), de
  **regimes diferentes** com colunas disjuntas → anti-cópia pinada. Colunas monetárias/contagem
  (`Valor_*`/`Preco_*`/`Nr_*`/`Num_*`/`Qtd_*`/`Qtde_*`) ficam `str` (texto decimal exato → `Decimal`
  a jusante). 3 CNPJ cols no histórico (`CNPJ_Emissor`/`CNPJ_Lider`/`CNPJ_Ofertante`), 2 no RCVM 160.
  ⚠️ **`Data_deliberacao_aprovou_oferta` (RCVM 160) chega em `DD/MM/YYYY`** — a coerção é ISO-only,
  então fica **`str`** (fora de `_DATE_COLS`; consumidor parseia com `dayfirst=True`), não
  misparseado dia/mês. ⚠️ **A META é um `.zip` de 2 membros** (o `.txt` dá **404**), mas as `section`
  voltam **simétricas** (`distribuicao`/`resolucao_160`, `_MEMBER_STEM='oferta'`), diferente do
  INTERMED/COORD_OFERTA. **Quinta fatia da Wave 4 do #41; fecha a issue #14**

**Companhias Abertas** — portal root `cia_aberta/`; **open-data only** (a CVM não publica padrão XML
de envio). ⚠️ **É o maior root do portal** — três sub-roots: `CAD` (o cadastro, implementado),
`DOC/{CGVN,DFP,FCA,FRE,IPE,ITR,VLMO}` (7 datasets de demonstrações, **pendentes**) e `EVENTOS`
(**pendente**). Cada sub-dataset precisa de grounding próprio; não presumir a forma do vizinho.
Sob `CIA_ABERTA/CAD/`:
- Cadastro de Companhias Abertas — ✅ **ingestion** `cad_cia_aberta.csv` (**CSV solto**, não ZIP,
  **47 cols**, ~2.677 linhas) — `ingestion/cia_aberta/cad/cadastro/cadastro.py`
  (`CadastroCiaAbertaReader`); contract `_internal/config/contracts/cad_cia_aberta.py`, **gerado do
  header e pinado** a `tests/fixtures/cad_cia_aberta/cad_cia_aberta_header.csv`. **Snapshot** de URL
  fixa, **sem `date_ref`** (molde do `CadastroCiaEstrangReader`/`CadastroCiaIncentReader`).
  ⚠️ **Não é cópia dos irmãos CIA_\*** — a chave é `CNPJ_CIA` (não `CNPJ`) e acrescenta `TP_MERC`
  (BOLSA / BALCÃO ORGANIZADO / BALCÃO NÃO ORGANIZADO). **7 colunas de data** (`MOTIVO_CANCEL` é
  TEXTO). **Duas colunas de CNPJ** (`CNPJ_CIA` 2.677 + `CNPJ_AUDITOR` 2.577 preenchidos); `RESP` tem
  nome de pessoa mas **sem coluna de CPF**. ⚠️ **A META é um `.txt` solto** de seção única
  (`meta_cad_cia_aberta.txt`, 47 campos) — ao contrário dos `.zip` do COORD_OFERTA/CROWDFUNDING/
  OFERTA. `CD_CVM`/`CEP`/`TEL`/`FAX`/`DDD_*` `numeric`/`char` no META mas `str`. **Sexta fatia da
  Wave 4 do #41; abre o root `cia_aberta/` (1/9 datasets)**
- IPE (Informações Periódicas e Eventuais) — ✅ **ingestion** `ipe_cia_aberta_AAAA.zip` (**ZIP de 1
  membro**, 13 cols, ~49,3k linhas em 2025) — `ingestion/cia_aberta/doc/ipe/ipe.py`
  (`IpeCiaAbertaReader`); contract `_internal/config/contracts/ipe_cia_aberta.py`, **gerado do header
  e pinado** a `tests/fixtures/ipe_cia_aberta/ipe_cia_aberta_header.csv`. **Particionado por ANO** (o
  `date_ref` seleciona o ano). ⚠️ **É um ÍNDICE, não o documento** — uma linha por documento
  entregue, com `Link_Download` (RAD da CVM) devolvido como **texto, não seguido** (molde do
  `DfinFiiReader`; a extração ZIP vem do `BalanceteFieReader`). 2 date cols (`Data_Referencia`,
  `Data_Entrega`, ambas ISO e declaradas `date` no META). ⚠️ **`CNPJ_Companhia` carrega o placeholder
  `00.000.000/0000-00`** para emissores estrangeiros sem CNPJ brasileiro (44 de 49.277 em 2025; zero
  malformados) — devolvido **como publicado**, e a coluna segue em `tuple_cnpj_cols` porque o check
  exige **ao menos um** válido (a aresta — uma partição só de placeholders levantaria — é pinada por
  teste). `Codigo_CVM` (`Numérico`) e `Versao` (`smallint`) no META ficam **`str`** (identificadores).
  `Tipo`/`Especie`/`Assunto`/`Protocolo_Entrega` chegam **parcialmente preenchidos**. ⚠️ **A META é um
  `.txt` SOLTO** — entre os 7 datasets do `DOC` a CVM usa **4 grafias distintas** de META
  (`meta_<ds>_cia_aberta.zip`, `meta_<ds>_cia_aberta_txt.zip`, **`fca_cia_aberta.zip` sem o prefixo
  `meta_`**, e este `.txt`): a URL é constante por dataset, **jamais derivada**. **Sétima fatia da
  Wave 4; abre o sub-root `DOC` (2/9 datasets do `cia_aberta/`)**
- VLMO (Valores Mobiliários negociados e detidos) — ✅ **ingestion** `vlmo_cia_aberta_AAAA.zip`
  (**ZIP de 2 membros**) — `ingestion/cia_aberta/doc/vlmo/*` (`VlmoCiaAbertaReader` índice 12 cols
  ~5,8k linhas; `VlmoCiaAbertaConReader` conteúdo 17 cols ~63k linhas; base privada
  `_base_vlmo_reader.py`); contracts `_internal/config/contracts/vlmo_cia_aberta.py`, **gerados dos
  headers e pinados** a `tests/fixtures/vlmo_cia_aberta/*_header.csv`. **Particionado por ANO**.
  ⚠️ **Os 2 membros NÃO são registro+satélite** — são **índice + conteúdo** (colunas disjuntas,
  anti-cópia pinada). ⚠️ **PRIMEIRAS COLUNAS MONETÁRIAS DO ROOT** — `Preco_Unitario`/`Volume` com
  **10 casas decimais** e `Quantidade` inteiro (META: `decimal`/`decimal`/`bigint`) ficam **texto
  exato**, nunca float: um `float64` transforma `61961072.9999543100` em `61961072.99995431`
  (provado por mutação; o gate `check_dtypes` também barra). ⚠️ **`Data_Movimentacao` chega ~58%
  VAZIA** — data por contrato, branco vira `NaT`. ⚠️ **SEM dado pessoal** apesar de ser informe de
  insider: `Empresa` é a *companhia* e `Tipo_Cargo` é *categoria de cargo*; o indivíduo nunca é
  nomeado. CNPJ 100% válido nos dois (sem o placeholder do IPE). ⚠️ **A META é `.zip` e o `.txt` dá
  404 — o INVERSO do IPE**; `section` assimétricas (`meta_vlmo_cia_aberta` + `con`, molde INTERMED).
  **Sétima fatia da Wave 4; `DOC` em 2/7**
- FCA (Formulário Cadastral) — ✅ **ingestion** `fca_cia_aberta_AAAA.zip` (**ZIP de 10 membros**:
  índice 9 cols + auditor 15 + canal_divulgacao 7 + departamento_acionistas 23 + dri 26 + endereco 21
  + escriturador 24 + geral 26 + pais_estrangeiro_negociacao 7 + valor_mobiliario 18) —
  `ingestion/cia_aberta/doc/fca/*` (10 `FcaCiaAberta*Reader`, base privada `_base_fca_reader.py`);
  contracts `_internal/config/contracts/fca_cia_aberta.py`, **gerados dos headers e pinados** a
  `tests/fixtures/fca_cia_aberta/*_header.csv`. **Particionado por ANO**.
  ⚠️ **O ÍNDICE NÃO SEGUE A CONVENÇÃO DE NOMES DOS PRÓPRIOS SATÉLITES** — usa `CNPJ_CIA`/`DT_REFER`/
  `DT_RECEB`/`DENOM_CIA`/`ID_DOC` (estilo `cad_cia_aberta.csv`) contra `CNPJ_Companhia`/
  `Data_Referencia`/`ID_Documento` nos 9; gerar de um molde só quebra o índice **em silêncio**
  (anti-cópia pinada nas 2 direções). ⚠️ **`departamento_acionistas` é HEADER-ONLY (0 linhas)** →
  `tuple_cnpj_cols=()`, senão um artefato legitimamente vazio levanta `ContractError` (provado por
  mutação; classe de falha do CRI). ⚠️ **PRIMEIROS CPF DO ROOT (LGPD):** `dri.CPF_Responsavel`
  (1.003 CPF + 4 CNPJ), `auditor.CPF_Responsavel_Tecnico`, e `auditor.CPF_CNPJ_Auditor` (misto por
  definição — todo CNPJ em 2025, mas um ano com CPF quebraria um check) → **fora de
  `tuple_cnpj_cols`**, fixtures **header-only**. `escriturador` é o único com **2** CNPJ cols de
  fato. De 1 a **9** date cols por membro (`geral`), todas ISO-ou-branco → branco vira `NaT`.
  ⚠️ **A META é `fca_cia_aberta.zip` — SEM o prefixo `meta_`** (as 2 derivações óbvias dão 404,
  enquanto o vizinho `CAD` serve `meta_cad_cia_aberta.txt`): o caso mais forte de "URL jamais
  derivada". **8ª fatia da Wave 4; `DOC` em 3/7**
- CGVN (Informe sobre o Código Brasileiro de Governança Corporativa) — ✅ **ingestion**
  `cgvn_cia_aberta_AAAA.zip` (**ZIP de 2 membros**: índice 12 cols/382 linhas + `praticas` 11
  cols/**19.980** linhas) — `ingestion/cia_aberta/doc/cgvn/*` (`CgvnCiaAbertaReader`,
  `CgvnCiaAbertaPraticasReader`, base privada `_base_cgvn_reader.py`); contracts
  `_internal/config/contracts/cgvn_cia_aberta.py`, **gerados dos headers e pinados** a
  `tests/fixtures/cgvn_cia_aberta/*_header.csv`. **Particionado por ANO**. Molde do VLMO
  (índice + conteúdo). ⚠️ **O índice do CGVN usa CamelCase** (`CNPJ_Companhia`/`Data_Referencia`) —
  **o FCA era a EXCEÇÃO do sub-root, não a regra**; generalizar do vizinho escreveria este errado
  (anti-generalização pinada, comparando os 2 contracts). ⚠️ **`Codigo_CVM` chega `001023`, COM zero
  à esquerda** — primeiro caso do root em que o texto é **load-bearing** (provado por mutação:
  `int64` devolve `1023`); `ID_Item` é hierárquico (`1.1.1`). 4 date cols no índice (inclui
  `Data_Inicio/Fim_Exercicio_Social`), 1 no `praticas`. `Explicacao` até ~6.000 chars, sem `;`
  embutido (larguras uniformes sob `QUOTE_NONE`, medido). `Link_Download` é **`http://…/ENETCONSULTA/…`**
  (≠ o `https://…/ENET/…` do IPE/VLMO) e vai **como publicado**, não seguido. ⚠️ **META é
  `meta_cgvn_cia_aberta.zip`** (a forma padrão); as outras 3 dão 404, **incluindo a sem-prefixo que é
  a correta do FCA**. **9ª fatia da Wave 4; `DOC` em 4/7**
- FRE (Formulário de Referência) — ✅ **ingestion COMPLETA (36/36 membros)**
  `fre_cia_aberta_AAAA.zip` — ⚠️ **o MAIOR dataset do portal: 36 membros, ~131 mil linhas**, entregue
  em **4 PRs temáticos** (1: índice+capital ✅ · 2: administração/pessoas, **todos os com CPF** ✅ ·
  3: diversidade (agregados) ✅ · 4: remuneração/val. mobiliários/transações ✅).
  ⚠️ **A fatia 4 acrescentou 4 pares de mesma largura, 3 deles com PREFIXO IDÊNTICO:**
  `acao_entregue`, `remuneracao_acao` e `remuneracao_maxima_minima_media` têm **14 colunas cada** e
  os dois primeiros **compartilham as 10 primeiras** — a colisão mais apertada do dataset (9 pares
  no total com as fatias 3+4). ⚠️ **`participacao_sociedade` tem DUAS colunas de CNPJ** e 792 dos
  6.511 valores de `CNPJ` são o placeholder `00000000000000` (subsidiária no exterior sem CNPJ
  brasileiro) — devolvidos **como publicados**; a coluna segue declarada porque o check exige **ao
  menos um** válido. ⚠️ **`transacao_parte_relacionada.Documento_Parte_Relacionada` fica FORA de
  `tuple_cnpj_cols` apesar de 100% VAZIA em 2025** — a irmã `Tipo_Pessoa` é `PF/PJ` na META, então é
  CPF-ou-CNPJ por definição (mesma classe do `Documento_Pessoa_Relacionada`); declarar passaria em
  todo ano vazio. ⚠️ **Coluna vazia é propriedade do ANO, não do schema:** 12 colunas de
  `participacao_sociedade` chegam vazias, e `Data_Valor_Mercado`/`Data_Valor_Contabil` **seguem
  data** (META `date`, tudo `NaT`). ⚠️ `Duracao_Transacao` traz 879 valores `DD/MM/YYYY` e **não é
  data** (`varchar` na META, texto livre).
  ⚠️ **Os 11 membros de diversidade têm 5 PARES de mesma largura e listas diferentes**
  (9/10/11/12/13 cols) — diferem por **uma** coluna de agrupamento (`Local` × `Posicao` ×
  `Orgao_Administracao`) e pelos baldes; copiar o irmão bate na largura e só falha no header pinado.
  `administrador_PCD` e `empregado_PCD` têm 10 cols cada e compartilham **8** (divergem em 2 cada). Em
  `administrador_PCD` as `Quantidade_*` chegam ~1/5 **vazias** — vazio **não** é zero.
  `ingestion/cia_aberta/doc/fre/*` (base privada `_base_fre_reader.py`); contracts
  `_internal/config/contracts/fre_cia_aberta.py`, **gerados dos headers e pinados**. **Particionado
  por ANO**. ⚠️ **O índice usa `CNPJ_CIA`/`DT_REFER`/`DT_RECEB`** (como o FCA), os satélites usam
  `CNPJ_Companhia`/`Data_Referencia` — **o CGVN NÃO faz isso**: não há regra entre datasets, só
  medição (pinado nas 2 direções, com o CGVN como contra-exemplo). ⚠️ **SEIS nomes de coluna de CNPJ**
  ao longo dos 36 membros (`CNPJ`, `CNPJ_Auditor`, `CNPJ_CIA`, `CNPJ_Companhia`, `CNPJ_Emissor`,
  `CNPJ_Emissor_Pessoa_Relacionada`) → cada contrato declara o seu; `auditor` declara **2** e
  `relacao_familiar` **3**. ⚠️⚠️ **COLUNA DE CNPJ É A QUE SÓ GUARDA CNPJ — O NOME NÃO É O TESTE:**
  ficam **fora** de `tuple_cnpj_cols` toda coluna `CPF*`, as 3 `CPF_CNPJ_*` de `posicao_acionaria`
  (mistas por definição) e **`relacao_subordinacao.Documento_Pessoa_Relacionada`**, que **não diz nem
  CPF nem CNPJ e guarda os dois** (8.462 CNPJ × 34 CPF em 2025, tipados pela irmã
  `Tipo_Pessoa_Relacionada`) — uma coluna mista declarada passa no ano todo-CNPJ e quebra no primeiro
  CPF. ⚠️ **Máscara não é uniforme nem dentro de um membro:** em `auditor`, `CNPJ_Companhia` vem
  pontuado e `CNPJ_Auditor`, na mesma linha, vem em dígitos crus. ⚠️ `membro_comite` e
  `administrador_membro_conselho_fiscal` têm **21 colunas cada e colunas diferentes** → copiar o irmão
  passaria em tudo menos no header pinado (anti-cópia pinada nas 2 direções). ⚠️ **2 colunas de data
  chegam 100% VAZIAS** em 2025 (`auditor.Data_Fim_Contratacao`,
  `posicao_acionaria.Data_Composicao_Capital_Social`) e **seguem data por contrato** — e um teste de
  vazio **NÃO** prova isso: branco vira NA sob `dtype="str"` também, então a asserção é sobre o
  **dtype** (`datetime64` × `string`). ⚠️ `CPF_CNPJ_Representante_legal` com `legal` **minúsculo**,
  preservado verbatim. ⚠️ **Os membros `*_declaracao_raca`/`*_declaracao_genero`/`*_PCD`/
  `*_faixa_etaria` NÃO são dado pessoal sensível — são CONTAGENS AGREGADAS** (`Quantidade_Preto`,
  `Quantidade_Feminino`); o PII real são os **6 membros com CPF** da fatia 2, com fixtures
  **header-only**. `Valor_*`/`Quantidade_*`/`Numero_*`/`Percentual_*` ficam texto exato. ⚠️ **META =
  `meta_fre_cia_aberta.zip`** (padrão), **50 membros para 36 de dados** e prefixo interno **misto**.
  **10ª–12ª fatias da Wave 4; `DOC` em 5/7 (FRE COMPLETO)**
- DFP (Demonstrações Financeiras Padronizadas) — ✅ **ingestion COMPLETA (19/19 membros)**
  `dfp_cia_aberta_AAAA.zip` (12,73 MB, **~1,17 MILHÃO de linhas**: índice + 8 demonstrações em
  `_con`/`_ind` + composição do capital + parecer) — `ingestion/cia_aberta/doc/dfp/*`
  (`DfpCiaAberta*Reader`, base privada `_base_dfp_reader.py`); contracts
  `_internal/config/contracts/dfp_cia_aberta.py`, **gerados dos headers e pinados**.
  **Particionado por ANO**.
  ⚠️⚠️ **INVERTE A ARMADILHA DE TODOS OS ANTERIORES:** em CRA/CRI/FCA/FRE membros de mesma largura
  tinham colunas DIFERENTES; aqui os 16 membros de demonstração colapsam em **3 listas** e são
  **genuinamente idênticos** (14 = balanço, só `DT_FIM_EXERC`; 15 = fluxo, soma `DT_INI_EXERC`;
  16 = DMPL, soma `COLUNA_DF`). 19 membros → **6** listas distintas. **Medido contra as fixtures** —
  presumir "iguais" e presumir "diferentes" é o mesmo erro.
  ⚠️⚠️ **O BURACO QUE ISSO ABRE:** com 10 membros de lista idêntica, um reader apontado ao membro
  ERRADO (swap `con`↔`ind`) devolve frame **válido**, tipos certos, contrato passa — **nada fica
  vermelho**. Provado por mutação (`DRE_con` lendo `DRE_ind` passava na suíte INTEIRA) e fechado por
  um teste de **identidade do membro** (cada membro sintético se identifica numa coluna).
  ⚠️⚠️ **`VL_CONTA` tem 10 casas decimais E SUA ESCALA ESTÁ EM OUTRA COLUNA** (`ESCALA_MOEDA` =
  `MIL`/`UNIDADE`): somar sem ler a escala erra por **1000×**. Texto exato; os readers **não**
  reescalam. ⚠️ `CD_CVM` vem `001023` (zero à esquerda) · `ORDEM_EXERC` (`ÚLTIMO`/`PENÚLTIMO`)
  duplica cada conta, **sem chave única** · **todos os 19 usam `CNPJ_CIA`/`DT_REFER`**, diferente do
  FCA/FRE cujos satélites trocam de convenção · META = `meta_dfp_cia_aberta_txt.zip` (**infixo
  `_txt`**; as outras 3 dão 404, inclusive a sem-prefixo que é a correta do FCA)
- ITR (Informações Trimestrais) — ✅ **ingestion COMPLETA (19/19 membros)** — **FECHA o `DOC` (7/7)**
  `itr_cia_aberta_AAAA.zip` (31,63 MB, **3.640.994 linhas — 3× o DFP e o maior artefato da
  biblioteca**) — `ingestion/cia_aberta/doc/itr/*` (`ItrCiaAberta*Reader`, base privada
  `_base_itr_reader.py`); contracts `_internal/config/contracts/itr_cia_aberta.py`, **gerados dos
  headers e pinados**. Mesma forma do DFP (19 membros → 6 listas; 16 demonstrações em 3).
  ⚠️⚠️ **18 DOS 19 MEMBROS SÃO BYTE-IDÊNTICOS AO DFP E EXATAMENTE 1 NÃO É:** o `parecer` grafa
  **`TP_RELAT_ESP`** (revisão especial, trimestral) onde o DFP grafa **`TP_RELAT_AUD`** (auditoria,
  anual) — **mesma largura (8), mesma posição (5ª), 7 de 8 nomes**. Copiar o contract do DFP erraria
  **uma** coluna e passaria em tudo menos no header pinado. **É o contraponto exato da lição do
  DFP:** lá o achado foi "aqui membros irmãos SÃO idênticos"; levar isso ao dataset vizinho é o mesmo
  erro — **18/19 idênticos é o que faz alguém copiar o 19º**. Pinado nas 2 direções, membro a membro,
  contra as fixtures dos DOIS datasets.
  ⚠️ Herdadas do DFP e **re-medidas** aqui: `VL_CONTA` 10 casas + **escala em `ESCALA_MOEDA`** ·
  10 membros de lista idêntica ⇒ swap `con`↔`ind` só visível pelo **teste de identidade do membro**
  (provado: `DRE_con` lendo `DRE_ind` fica vermelho) · `CD_CVM` com zero à esquerda · `ORDEM_EXERC`
  duplica cada conta, **sem chave única** · todos os 19 usam `CNPJ_CIA`/`DT_REFER` (100% válidos,
  medido sobre **valores distintos**) · todo `DT_*` 100% ISO · `COLUNA_DF` e `TP_RELAT_ESP`
  parcialmente vazias · META = `meta_itr_cia_aberta_txt.zip` (infixo `_txt`; as outras 3 dão 404)
- ⬜ **ingestion** `EVENTOS/RECOMPRA_ACOES` — **o único pendente do root `cia_aberta/`**

**Investidores Não Residentes**
- ⬜ Informe Mensal de Investidor não Residente (`PadraoXMLInfoMensalINR.asp`)
- ⬜ Informe Semestral de Investidor não Residente (`PadraoXMLInfoSemestralINR.asp`)

**Mercados de Negociação**
- ⬜ Atualização do Cadastro de Ativos (`PadraoXMLAtivos.asp`)

**Escriturador de Valores Mobiliários**
- ⬜ Informe Art. 12 Resolução CVM 33 (`PadraoXMLPrest.asp`)
- ⬜ Informe de Portabilidade (`PadraoXMLInfoPortabilidade.asp`)

## Layout

```
src/filings_cvm/
    __init__.py            # ONLY the cross-cutting names: RetryPolicy + __version__ (#91).
                           #   NOT readers, NOT writers — each section owns its own names.
    submission/            # envio → CVM: SubmissionWriter adapters (validated model → XML)
                           #   `from filings_cvm.submission import InformeDiario`
    ingestion/             # leitura ← CVM: IngestionReader adapters (CVM file → typed DataFrame)
                           #   nested by CVM portal path (dados/<ROOT>/…); its __init__ exports the
                           #   22 ROOT PACKAGES, never the readers
        _base_meta_reader.py   # PRIVATE base for the 42 Meta*Reader (shared across every root)
                           #   EVERY dataset is a FOLDER holding its reader(s) + a meta.py:
                           #   dfin_cra/{dfin_cra.py,meta.py}. Mirrors the portal, which has a
                           #   directory per dataset. THE PORTAL ROOT IS THE PUBLIC SURFACE:
                           #   `from filings_cvm.ingestion.cia_aberta import FreCiaAbertaAuditorReader`
                           #   A new reader touches ONLY its own root's __init__ — not four of them.
        fi/                #   FI/ — Fundos de Investimento (one portal root; FIDC/, FII/, … as siblings)
            doc/           #     FI/DOC/* — informe_diario, cda, lamina/ (lamina + lamina_carteira),
                           #       eventual/ (índice de documentos eventuais, CSV solto anual)
            cad/           #     FI/CAD — cadastro_fi, registro/ (fundo/classe/subclasse),
                           #       cad_fi_hist/ (19 change-log readers + private base)
        fidc/              #   FIDC/ — inf_mensal/ (17 table readers + private base)
        fii/               #   FII/ — COMPLETO: inf_mensal/ (3), dfin (1), inf_trimestral/ (16), inf_anual/ (12)
        fip/               #   FIP/ — COMPLETO: doc/ (inf_trimestral + inf_quadrimestral, 2 flat-CSV readers)
        fiagro/            #   FIAGRO/ — doc/inf_mensal/ (informe + subclasse, 2 members + private base)
        fie/               #   FIE/ — COMPLETO: doc/{balancete,balanco} (ZIP) + medidas (flat CSV); no CAD
        securit/           #   SECURIT/ — COMPLETO: doc/{dfin_cra,dfin_cri} (flat) + inf_mensal_ots/ (8)
                           #     + inf_mensal_cra/ (8) + inf_mensal_cri/ (11); contracts pinned to real headers
        emissor_cepac/     #   EMISSOR_CEPAC/ — cad/cadastro (snapshot, no date_ref)
        auditor/           #   AUDITOR/ — cad/{auditor_pf,auditor_pj} (snapshot ZIP, 2 membros, no date_ref)
        agente_fiduc/      #   AGENTE_FIDUC/ — cad/{agente_fiduc_pf,agente_fiduc_pj} (snapshot ZIP, 2 membros, no date_ref)
        agente_auton/      #   AGENTE_AUTON/ — cad/{agente_auton_pf,agente_auton_pj} (snapshot ZIP, 2 membros, no date_ref)
        invnr/             #   INVNR/ — cad/{invnr_repres_pf,invnr_repres_pj} (snapshot ZIP, 2 membros, no date_ref)
        intermed/          #   INTERMED/ — cad/{intermed,intermed_resp} (snapshot ZIP, 2 membros NÃO-pf/pj, no date_ref)
        adm_cart/          #   ADM_CART/ — cad/{adm_cart_pf,adm_cart_pj,adm_cart_diretor,adm_cart_resp,adm_cart_socios} (snapshot ZIP, 5 membros, no date_ref; 3 sem coluna de data)
        consultor_vlmob/   #   CONSULTOR_VLMOB/ — cad/consultor_vlmob_{pf,pj,diretor,resp,socios} (snapshot ZIP, 5 membros, no date_ref; 3 sem coluna de data)
        adm_fii/           #   ADM_FII/ — cad/cadastro (cad_adm_fii.csv, CSV solto, 18 cols, snapshot, no date_ref) — encerra a Wave 3 do #41
        cia_estrang/       #   CIA_ESTRANG/ — cad/cadastro (cad_cia_estrang.csv, CSV solto, 49 cols, snapshot, no date_ref; 2 CNPJ cols) — abre a Wave 4 do #41
        cia_incent/        #   CIA_INCENT/ — cad/cadastro (cad_cia_incent.csv, CSV solto, 47 cols, snapshot, no date_ref; 2 CNPJ cols; NÃO é cópia do cia_estrang)
        coord_oferta/      #   COORD_OFERTA/ — cad/{coord_oferta,coord_oferta_resp} (snapshot ZIP, 2 membros NÃO-pf/pj, no date_ref; META é .zip)
        crowdfunding/      #   CROWDFUNDING/ — cad/{crowdfunding,crowdfunding_adm_resp,crowdfunding_socios} (snapshot ZIP, 3 membros, no date_ref; 2 satélites sem data; META é .zip)
        oferta/            #   OFERTA/ — distrib/{oferta_distribuicao,oferta_resolucao_160} (snapshot ZIP, 2 membros por regime, no date_ref; NÃO registro+satélite; META é .zip simétrica) — fecha #14
        cia_aberta/        #   CIA_ABERTA/ — cad/cadastro (cad_cia_aberta.csv, CSV solto, 47 cols, snapshot, no date_ref; chave CNPJ_CIA + TP_MERC; 2 CNPJ cols; META é .txt solto)
                           #     doc/ipe/ — IPE (ipe_cia_aberta_AAAA.zip, ZIP de 1 membro, 13 cols, anual; ÍNDICE de documentos, Link_Download não seguido; CNPJ placeholder 00.000.000/0000-00 honrado; META .txt solto)
                           #     doc/vlmo/ — VLMO (vlmo_cia_aberta_AAAA.zip, ZIP de 2 membros: índice 12 cols + conteúdo 17 cols, anual; monetárias 10dp como TEXTO; Data_Movimentacao ~58% vazia; META .zip — inverso do IPE)
                           #     doc/fca/ — FCA (fca_cia_aberta_AAAA.zip, ZIP de 10 membros, anual; o ÍNDICE usa outra convenção de nomes que os 9 satélites; departamento_acionistas é header-only → tuple_cnpj_cols=(); CPF em dri/auditor; META sem prefixo meta_)
                           #     doc/cgvn/ — CGVN (cgvn_cia_aberta_AAAA.zip, ZIP de 2 membros: índice 12 cols + praticas 11 cols/19.980 linhas, anual; índice em CamelCase — FCA era a exceção; Codigo_CVM com zero à esquerda; META .zip padrão)
                           #     doc/fre/ — FRE (fre_cia_aberta_AAAA.zip, MAIOR do portal: 36 membros/~131k linhas, anual; COMPLETO em 4 fatias temáticas — 1 (índice+capital, 8), 2 (administração/pessoas, 7, TODOS os com CPF), 3 (diversidade, 11, AGREGADOS), 4 (remuneração/val. mob./transações, 10) = 36/36; índice em maiúsculas como o FCA mas NÃO como o CGVN; 6 nomes de CNPJ col, mas coluna de CNPJ é a que SÓ guarda CNPJ — Documento_Pessoa_Relacionada e Documento_Parte_Relacionada guardam CNPJ+CPF e ficam de fora; membros de diversidade são AGREGADOS, não PII; participacao_sociedade tem 2 CNPJ cols com 792 placeholders 00000000000000)
                           #     doc/dfp/ — DFP (dfp_cia_aberta_AAAA.zip, 19 membros/~1,17M linhas, anual; INVERTE a armadilha: 16 membros colapsam em 3 listas IDÊNTICAS, e por isso um swap con/ind era invisível — fechado por teste de identidade do membro; VL_CONTA com 10 casas E escala em ESCALA_MOEDA; todos usam CNPJ_CIA; META com infixo _txt)
                           #     doc/itr/ — ITR (itr_cia_aberta_AAAA.zip, 19 membros/3,64M linhas, anual; 18 dos 19 headers BYTE-IDÊNTICOS ao DFP e exatamente 1 não: parecer usa TP_RELAT_ESP onde o DFP usa TP_RELAT_AUD, mesma largura e posição — 18/19 idênticos é o que faz copiar o 19º; fecha o DOC 7/7)
                           #     EVENTOS pendente (grounding próprio)
    _internal/             # PRIVATE — ships in the wheel, but not a public API
        utils/             # vendored helpers (dtypes, tabular_reader, retry, http_downloader,
                           #   text, zip_extractor, br_identifiers, typing/)
        config/            # private structural declarations (shapes + interfaces, not machinery)
            contracts/     # FileContract declarations (one per input source)
            schemas/       # shared, direction-neutral Pydantic models (one per XML standard)
            ports/         # private behavioural ABCs (SubmissionWriter, IngestionReader)
tests/
    unit/  integration/  performance/
```

**Public vs private.** Consumers import `<project_name>` (your core). Everything under
`<project_name>._internal` is vendored support code: it ships inside the wheel (so imports
resolve after `pip install`), but the leading underscore marks it off-limits — keep it out
of your public `__all__`. The internal imports are package-qualified
(`from <project_name>._internal.utils.dtypes import …`).

**⚠️ The import surface is grouped, not flat (#91).** Each section owns its own names, and the
top-level `filings_cvm.__all__` holds **only** `RetryPolicy` and `__version__` — what belongs to
neither section:

| what | import from |
|---|---|
| an ingestion reader | `filings_cvm.ingestion.<portal_root>` (22 roots) |
| a submission writer | `filings_cvm.submission` |
| `RetryPolicy` | `filings_cvm` |

**So a new reader is registered along its own package chain up to its portal root — and stops
there.** For a flat root that is two `__init__` files (dataset + root); for a nested one it is
every level in between — `cia_aberta` has an extra `doc/` layer, so its readers need **three**
(`doc/fre/` → `doc/` → `cia_aberta/`). Count the packages on the path rather than assuming two.
It must **not** be added to `filings_cvm/__init__.py` or `ingestion/__init__.py`;
`tests/unit/test_public_surface.py` fails in both directions if it is.

⚠️ **And register the contract in `_internal/config/contracts/__init__.py` too** — a reader
importing its contract from the module directly works fine while the contract is missing from that
`__all__`, so nothing fails. Check the **exported count**, not the suite.
The flat namespace was removed because at 216 readers it was an undivided wall of names that every
new reader widened, while the CVM portal already supplies the grouping.

⚠️ **"Every public reader" is now `_internal/utils/introspection.py`**, which walks the roots —
not a flat `__all__`. Any new gate that sweeps all readers must use it: a walk over the top-level
`__all__` finds **zero** readers and stays **green**, which is how a parametrised gate becomes a
placebo.

## Architecture

- **One public class per module/file.** The public class is named after the file
  (`user_service.py` → `UserService`). When helpers share no state and need no lifecycle,
  prefer **module-level functions** over a utility class. A private/shared base class gets
  its **own** `_`-prefixed file (`_base_reader.py`) — never share a module with a public
  class.
- **Separate I/O from logic**: pure functions in the core, side effects at the edges.
- Reach for a class only when there is **state + lifecycle**, **interface conformance**, or
  **dependency injection** — otherwise a module of functions is the right shape.
- **No redundant package-name subfolder.** When the package's whole purpose is one domain
  (e.g. `calendars`), do **not** nest a subfolder that repeats the package name
  (`src/<project_name>/<project_name>-ish/`) — the package name already conveys the scope. Keep
  public modules **flat** at `src/<project_name>/` (`src/<project_name>/calendar_br.py`), and put
  non-exported abstract bases / internals under `_internal/`.
- **On migration, reuse the target's own implementation.** When lifting code in from another
  repo, if this project already has an equivalent module (its own `_internal` typing engine, a
  helper), rewrite the imports to **this** project's version and discard the source's duplicate —
  never vendor a second copy (DRY). The scaffold's own `rewrite_internal_imports` embodies this.

## Conventions (inherited from `templates/python-common/`)

- **Ruff**: linter + formatter. Line-length 99, tab indent, double quotes, NumPy docstrings.
- **Pre-commit**: ruff, pydocstyle, codespell, commitizen, gitlint, unit + integration
  tests, coverage badge.
- **Gate parity — every lint/static/test gate lives in BOTH `.pre-commit-config.yaml` and
  `.github/workflows/tests.yaml`.** CI runs its gates as explicit steps (not `pre-commit run`),
  so adding a hook does not cover CI — add the matching step in the same commit, or a
  hook-skipping contributor (or branch-protection CI) bypasses it. Full rationale + canonical
  set + current open drift: `.github/CLAUDE.md` ("Gate parity").
- **Tests**: `pytest` — `make unit_tests` (`poetry run pytest tests/unit/`). Write
  pytest-style functions with fixtures, not `unittest.TestCase`.
- **Explicit column typing & Brazilian identifiers** — if the library touches pandas, type
  every DataFrame on load via `apply_dtypes` (`_internal.utils.dtypes`, never pandas'
  inference), route reads through `_internal.utils.tabular_reader`, and use
  `_internal.utils.br_identifiers` for CNPJ/CPF (alphanumeric-aware for the 2026 CNPJ).
- **A number whose fractional part carries meaning is NEVER a binary float.** `float64` cannot
  represent most decimal fractions (`1984223115.42` is stored as `1984223115.4200000762939453125`),
  and the loss happens at ingestion, is irreversible, and is **silent** — no contract fails, no
  single-value test fails, the frame prints correctly, and it surfaces much later as a
  reconciliation against CVM's own totals that misses by a hair. Declare such a column as exact
  text (this repo's prevailing convention — `Decimal` downstream) or via `list_decimal_cols`
  (`apply_dtypes` / `read_table` / `read_query`, exact `Decimal` with the **source's own scale**
  preserved). `_to_decimal` **refuses** a `float` rather than converting it, because converting
  launders an already-lossy value into a type that advertises exactness. A genuinely dimensionless
  statistic opts out per line with `# dtype-ok: <reason>`. Enforced by `bin/check_dtypes.py`
  (pre-commit + CI).
- **Every ingested DataFrame is provenance-stamped.** A reader's returned frame carries, beside
  its source columns, the six `FileContract.PROVENANCE_COLUMNS` — `url`, `updated_at` (tz-aware
  UTC collection time), `source_key`, `package_version`, `ingestion_run_id`, `content_hash` —
  appended by the shared `_internal.utils.provenance.stamp_provenance` seam **after** contract
  validation (they are not in `tuple_required`; the source lacks them). `updated_at` stays
  tz-aware — a SQL sink that needs naive normalises at the warehouse load, never here. This is
  enforced structurally: `bin/check_provenance.py` (pre-commit + CI) fails any `src/` module that
  calls `read_table` without also calling `stamp_provenance`, so the contract read and the stamp
  ship together.
- **No `.env`** — a distributable library has no runtime env to seed (unlike the service
  tiers), so none is shipped.
- **Logging via dependency injection** — never hard-import a logging backend in a helper;
  inject a logger (stdlib default), as `_internal/utils/retry.py`'s `LogEmitter` shows. The
  in-repo `logs.py` helper is **opt-in** at scaffold time; see `_internal/utils/CLAUDE.md`.
- **Every imported package is a direct dependency.** If a module `import`s a package, declare
  it in `pyproject.toml` — even when it is already installed transitively via another dep. A
  transitive presence is an accident of another package's tree and breaks silently the day that
  package drops or version-caps it. Run `poetry add <pkg>` for anything you import.
- **Runtime type checking is mandatory everywhere in `src/`.** It complements — does not replace
  — ruff `ANN` + mypy: static checks miss what crosses runtime boundaries (deserialised data, DB
  rows), so honest signatures become enforced contracts that fail loudly. The rule is uniform, no
  by-layer and no public/private exemption: **every class** under `src/` declares a checker
  metaclass from `_internal.utils.typing` (`metaclass=TypeChecker`; `ABCTypeCheckerMeta` for ABCs,
  `ProtocolTypeCheckerMeta` for Protocols), and **every standalone function** uses `@type_checker`
  — private (`_`-prefixed) helpers included. The only exclusions:
  - **Pydantic `BaseModel` subclasses** — Pydantic owns the metaclass (conflict at import) and
    already validates at construction, so never add `metaclass=TypeChecker` to a model.
  - **The typing engine itself** (`_internal/utils/typing/`) — it is the machinery.
  - **Dunders** (`__x__`) — the `TypeChecker` metaclass leaves them untouched, so the hook
    skips them too; single-underscore private names are **not** exempt.
  - Metaclasses are **inherited**, so only a hierarchy root declares it — a subclass of a
    checker-metaclass class (e.g. `LogsEmitter(LogEmitter)`) is already checked.

  The `check-typing` pre-commit hook (`bin/check_typing.py`) enforces this across all of `src/`.

## Releasing to PyPI

Two workflows ship under `.github/workflows/` (present only when a GitHub remote is set up):

- `release-test-pypi.yaml` — publish to **Test PyPI** first (`workflow_dispatch`).
- `release-pypi.yaml` — publish to **PyPI** and cut a GitHub release.

Both gate on the version being greater than what is already published, build with Poetry,
and fall back to `twine` if `poetry publish` is unavailable. Configure these repository
secrets and a GitHub Environment named **`release`**:

- `PYPI_TOKEN` — a PyPI API token.
- `TEST_PYPI_TOKEN` — a Test PyPI API token.

## Extending this template

- Keep `src/<project_name>/` as the importable package root; grow the public API there.
- Add sub-packages as the project grows — do not dump everything into `main.py`.
- Mirror the test folder hierarchy to match the package structure.
- Drop `_internal/config/contracts` (and the pandas deps) if the library never reads
  tabular inputs.
