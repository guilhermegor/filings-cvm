# **Cadastro de Auditores (AUDITOR) — leitura**

Leitura (← CVM) do cadastro dos **auditores independentes** supervisionados pela CVM, publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/). Estes readers **inauguram** o
*portal root* `auditor/` (irmão de `fi/`, `fidc/`, `fii/`, `securit/`, …).

> Primeira fatia da **Wave 3** do #41 (snapshots CAD de prestadores de serviço). Estabelece o molde
> multi-membro — base privada + `pf`/`pj` + Meta reader, contratos pinados aos headers publicados —
> que os demais roots de prestadores (ADM_CART, AGENTE_AUTON, INTERMED, INVNR, …) reaproveitam.

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

| Reader | Membro do `cad_auditor.zip` | Colunas | Chave CNPJ |
|--------|-----------------------------|---------|------------|
| `AuditorPfReader` | `cad_auditor_pf.csv` (pessoa física) | 4 | — (não há coluna de CNPJ) |
| `AuditorPjReader` | `cad_auditor_pj.csv` (pessoa jurídica) | 12 | `CNPJ` (mascarado) |

`AUDITOR/CAD` publica um **ZIP de dois membros**: os auditores **pessoa física** (código CVM, nome,
situação) e as **firmas de auditoria** (o mesmo código e situação, mais o `CNPJ` mascarado, a
denominação social e o endereço). Como o `cad_fi.csv`, é um **retrato do estado atual** numa **URL
fixa** que a CVM sobrescreve no lugar — por isso **não há `date_ref`**, e um `path_raw` persistido é
o único registro do que o cadastro dizia no dia da coleta. Nenhum grão é assumido.

⚠️ O membro **pessoa física não tem coluna de CPF** — o cadastro identifica o auditor pessoa física
por `CD_CVM` e nome, então não há identificador pessoal a validar (`tuple_cnpj_cols` vazio, explícito).
O `CNPJ` do membro pessoa jurídica chega **mascarado** (`36.348.092/0001-42`) e é a única coluna de
CNPJ; a rotina `br_identifiers` aceita a forma mascarada.

### Tipagem

Apenas `DT_INI_SIT` vira `date` puro (brancos viram `NaT`). Todo o restante — inclusive `CD_CVM` e o
`CEP` numérico, que preservam zeros à esquerda — mantém o **texto exato da CVM**. O mapa de tipos é
derivado do contrato, então os dois não podem divergir.

Os contratos são **gerados do header publicado** e **pinados** aos bytes verbatim da CVM em
`tests/fixtures/cad_auditor/*_header.csv` — o único oráculo não-tautológico (o teste
`test_contract_matches_the_published_header`).

---

## Política de retry

Todo reader aceita `retry_policy: RetryPolicy | None = None` e declara o seu padrão em
`_RETRY_POLICY` (padrão paciente: 5 tentativas, *backoff* ~2, 4, 8, 10 s). Veja a
[visão geral da leitura](index.md#politica-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Firmas de auditoria (pessoa jurídica)

```python
from filings_cvm import AuditorPjReader

df_ = AuditorPjReader().read()
# df_[["CD_CVM", "CNPJ", "DENOM_SOCIAL", "SIT", "UF"]]
```

### Auditores pessoa física + persistir a camada *bronze*

```python
from pathlib import Path
from filings_cvm import AuditorPfReader

df_ = AuditorPfReader(
    path_raw=Path("/data/bronze/cvm/cad_auditor"),
).read()
# o ZIP inteiro e ambos os membros ficam em disco: um path_raw de qualquer
# reader serve o outro (os dois baixam o mesmo arquivo).
```

Cada `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou
`ValueError` (membro ausente no arquivo) — falha cedo, sem devolver dados corrompidos.
