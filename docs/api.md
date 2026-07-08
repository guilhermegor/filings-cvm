# **Referência da API**

Interface pública da biblioteca. Tudo abaixo é importável de `filings_cvm.submission`; os nomes
principais também são reexportados no topo de `filings_cvm`.

> **Veja também:** [Uso](usage.md) · Envio: [Perfil Mensal](submission/perfil_mensal.md), [Informe Diário](submission/informe_diario.md)

---

## Serializador

### `PerfilMensal`

`filings_cvm.submission.PerfilMensal`

Serializa um documento validado para XML compatível com a CVM (padrão Perfil Mensal V4).

#### `to_xml(doc, output_path=None, versao="4.0") -> str | None`

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `doc` | `PerfilMensalDocument` | Documento totalmente validado. |
| `output_path` | `str \| None` | Se informado, grava o arquivo em `windows-1252` e retorna `None`. Caso contrário, retorna a `str` XML (UTF-8 em memória). |
| `versao` | `str` | Versão do formato colocada na tag `VERSAO`. Padrão `"4.0"`. |

```python
from filings_cvm.submission import PerfilMensal

xml = PerfilMensal().to_xml(doc)                       # retorna str
PerfilMensal().to_xml(doc, output_path="perfil.xml")   # grava arquivo, retorna None
```

Não há acesso à rede — apenas lógica pura e I/O de arquivo na borda.

### `InformeDiario`

`filings_cvm.submission.InformeDiario`

Serializa um documento validado para XML compatível com a CVM (padrão Informe Diário V4).

#### `to_xml(doc, output_path=None, versao="4.0") -> str | None`

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `doc` | `InformeDiarioDocument` | Documento totalmente validado. |
| `output_path` | `str \| None` | Se informado, grava o arquivo em `windows-1252` e retorna `None`. Caso contrário, retorna a `str` XML (UTF-8 em memória). |
| `versao` | `str` | Versão do formato colocada na tag `VERSAO`. Padrão `"4.0"`. |

```python
from filings_cvm.submission import InformeDiario

xml = InformeDiario().to_xml(doc)                          # retorna str
InformeDiario().to_xml(doc, output_path="informe.xml")     # grava arquivo, retorna None
```

O XML usa o namespace `urn:infdiario` e `COD_DOC=1`. Mesma borda de I/O do `PerfilMensal`.

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
  `src/filings_cvm/_internal/schemas/<padrao>.py`.
- O escritor de envio vai em `src/filings_cvm/submission/<padrao>.py` (uma classe pública por
  arquivo, nomeada como o arquivo).
- Reexporte os símbolos públicos em `filings_cvm/submission/__init__.py` e, quando fizer sentido,
  no `filings_cvm/__init__.py`.

O catálogo completo de padrões (implementados e pendentes) está no `CLAUDE.md` do repositório.
