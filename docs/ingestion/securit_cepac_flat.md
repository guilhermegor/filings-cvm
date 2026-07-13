# **DFIN da Securitização (CRA/CRI) + Cadastro de Emissor CEPAC — leitura**

Leitura (← CVM) dos três datasets **de CSV solto** da Securitização e dos emissores de CEPAC,
publicados no [portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/). Estes três readers
**inauguram** os *portal roots* `securit/` e `emissor_cepac/` (irmãos de `fi/`, `fidc/`, `fii/`, …).

> Primeira fatia da **Wave 2** do #41 (Securitização). Os três dumps mensais multi-membro
> (`INF_MENSAL_CRA/CRI/OTS`) chegam em PRs seguintes.

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

| Reader | Dataset | Artefato | Precedente |
|--------|---------|----------|------------|
| `DfinCraReader` | `SECURIT/DOC/DFIN_CRA` | `dfin_cra_AAAA.csv` (solto, anual) | `DfinFiiReader` |
| `DfinCriReader` | `SECURIT/DOC/DFIN_CRI` | `dfin_cri_AAAA.csv` (solto, anual) | `DfinFiiReader` |
| `CadastroEmissorCepacReader` | `EMISSOR_CEPAC/CAD` | `cad_emissor_cepac.csv` (**snapshot, URL fixa**) | `CadastroFiReader` |

**DFIN CRA / DFIN CRI** são o **índice das demonstrações financeiras** — uma linha por documento
entregue (não a demonstração em si) — dos CRA (Certificados de Recebíveis do Agronegócio) e CRI
(Certificados de Recebíveis Imobiliários). Estruturalmente idênticos (9 colunas), diferindo só no
tipo de certificado. Particionados por **ano** (o `date_ref` seleciona o ano). O `Link_Download`
aponta para o documento no portal fnet da B3 e é **devolvido como texto, não seguido** (o princípio
do `DfinFiiReader`). Chave frouxa `CNPJ_Emissora`; sem chave única.

**Cadastro de Emissor CEPAC** é o **retrato do estado atual** dos emissores de CEPAC (Certificados de
Potencial Adicional de Construção) — **municípios** conduzindo uma operação urbana, então o cadastro
é minúsculo (poucas linhas). Como o `cad_fi.csv`, é um CSV solto numa **URL fixa** que a CVM
sobrescreve no lugar — por isso **não tem `date_ref`**, e um `path_raw` persistido é o único registro
do que o cadastro dizia no dia da coleta.

### Tipagem

Apenas colunas de data viram `date` puro (`Data_Referencia`/`Data_Entrega` no DFIN;
`DT_REG`/`DT_CANCEL`/`DT_INI_SIT` no CEPAC; brancos viram `NaT`). Todo o restante — inclusive
`Link_Download` e `Versao` — mantém o **texto exato da CVM**. O mapa de tipos é derivado do contrato.

---

## Política de retry

Todo reader aceita `retry_policy: RetryPolicy | None = None` e declara o seu padrão em
`_RETRY_POLICY` (padrão paciente: 5 tentativas, *backoff* ~2, 4, 8, 10 s). Veja a
[visão geral da leitura](index.md#politica-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Índice de demonstrações financeiras de CRA de um ano

```python
from datetime import date
from filings_cvm import DfinCraReader

df_ = DfinCraReader(date_ref=date(2025, 6, 1)).read()   # o ANO de 2025
# uma linha por documento; Link_Download devolvido como texto (não seguido).
```

### Cadastro de emissor CEPAC (snapshot) + persistir a camada *bronze*

```python
from pathlib import Path
from filings_cvm import CadastroEmissorCepacReader

df_ = CadastroEmissorCepacReader(
    path_raw=Path("/data/bronze/cvm/cad_emissor_cepac"),
).read()
# df_[["CNPJ", "DENOM_SOCIAL", "MUN", "UF", "SIT"]]
```

Cada `read` levanta `OSError` (falha de download) ou `ContractError` (CSV viola o contrato) — falha
cedo, sem devolver dados corrompidos.
