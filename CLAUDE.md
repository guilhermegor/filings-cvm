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

**META (metadados publicados pela CVM)** — ✅ **ingestion**, **35 readers** (`Meta*Reader`), um por
dataset, em `ingestion/<root>/…/<dataset>/meta.py` sobre a base privada
`ingestion/_base_meta_reader.py`; parser puro `_internal/utils/meta_parser.py`; contracts
`_internal/config/contracts/meta.py` (35 instâncias de um factory sobre uma tupla compartilhada —
o formato do frame é **nosso** e idêntico; só o `source_key` difere, prefixado `meta_`). Doc:
`docs/ingestion/meta.md`. Cada META é texto em blocos (`Campo:`/`Descrição`/`Tipo Dados`),
**ISO-8859-1 + CRLF**, num `.txt` solto (11) ou `.zip` multi-membro (13); volta como **um frame
longo** com o membro em `section`. **Sem `date_ref`** (URL fixa, a CVM sobrescreve no lugar).
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
    __init__.py            # the public API surface (control it with __all__)
    submission/            # envio → CVM: SubmissionWriter adapters (validated model → XML)
    ingestion/             # leitura ← CVM: IngestionReader adapters (CVM file → typed DataFrame)
                           #   nested by CVM portal path (dados/<ROOT>/…); __init__ FLAT public API
        _base_meta_reader.py   # PRIVATE base for the 26 Meta*Reader (shared across every root)
                           #   EVERY dataset is a FOLDER holding its reader(s) + a meta.py:
                           #   dfin_cra/{dfin_cra.py,meta.py}. Mirrors the portal, which has a
                           #   directory per dataset. Public API stays flat via re-exports.
        fi/                #   FI/ — Fundos de Investimento (one portal root; FIDC/, FII/, … as siblings)
            doc/           #     FI/DOC/* — informe_diario, cda, lamina/ (lamina + lamina_carteira)
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
