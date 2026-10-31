# **Atos Declaratórios (ATO_DECLR) — leitura**

Leitura (← CVM) da lista de **atos declaratórios** que suspendem a intermediação irregular de
valores mobiliários, publicada no [portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/).
Este reader **inaugura** o *portal root* `ato_declr/` (distinto de `intermed/`).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

| Reader | Artefato | Colunas | Colunas de data | Chaves CNPJ |
|--------|----------|---------|-----------------|-------------|
| `AtoDeclrReader` | `ato_declr.csv` (CSV solto, ISO-8859-1, `;`) | 7 | 2 | nenhuma |

`ATO_DECLR/INTERMED` é o único dataset do root (medido na listagem: `DADOS/ato_declr.csv` e
`META/meta_ato_declr.txt`, sem irmãos). Uma linha por ato e parte listada (914 linhas, ~141 KB, no
dia da medição); o mesmo ato aparece em várias linhas e o mesmo documento (`Link_Download`) em
várias partes. É um **retrato** numa **URL fixa** que a CVM sobrescreve no lugar — **sem
`date_ref`**, e um `path_raw` persistido é o único registro do que a lista dizia no dia da coleta.

⚠️ **`CNPJ_CPF` mistura CNPJ, CPF e vazio** (129 CNPJ, 531 CPF, 252 em branco, e 1 CNPJ sem máscara
e sem o zero à esquerda) — por isso **não** é coluna de CNPJ e `tuple_cnpj_cols` é vazio. Volta como
publicada. `Denominacao` traz nomes de pessoas físicas (LGPD), então a fixture é só o header.
`Link_Download` é devolvido como texto, **não seguido**.

---

## Tipagem

`Data_Ato_Declaratorio` e `Data_Publicacao_DOU` (ISO `AAAA-MM-DD`) viram `date`. O restante mantém
o texto exato — inclusive `Numero_Ato_Declaratorio`, `numeric` no META mas identificador. O
contract é **gerado do header publicado** e **pinado** a
`tests/fixtures/ato_declr/ato_declr_header.csv`.

---

## Política de retry

O reader aceita `retry_policy: RetryPolicy | None = None` e declara o seu padrão em `_RETRY_POLICY`
(5 tentativas, *backoff* ~2, 4, 8, 10 s). Veja a
[visão geral da leitura](index.md#politica-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

```python
from pathlib import Path
from filings_cvm.ingestion.ato_declr import AtoDeclrReader

df_ = AtoDeclrReader().read()
# ou, preservando o CSV bruto para o bronze:
df_ = AtoDeclrReader(path_raw=Path("/data/bronze/cvm/ato_declr")).read()
```

Cada `read` levanta `OSError` (falha de download) ou `ContractError` (CSV viola o contrato).
