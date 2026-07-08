# **Informe Diário — V4**

Envio (→ CVM) do padrão **Informe Diário V4**
([`PadraoXMLInfoDiarioNetV4.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiarioNetV4.asp)).

> **Veja também:** [Referência da API](../api.md) para cada símbolo público · [Uso](../usage.md)
> para instalação e o conceito geral.

---

## Descrição

Monte um `InformeDiarioDocument` (um `InformeDiarioHeader` + uma lista de `InformeDiarioInform`,
uma por fundo, até 100) e serialize com `InformeDiario().to_xml(...)`. O XML usa o namespace
`urn:infdiario` e `COD_DOC=1`.

| Modelo | Tag XML | Papel |
|--------|---------|-------|
| `InformeDiarioDocument` | `DOC_ARQ` | Documento completo: `header` + `informs` (até 100 fundos). |
| `InformeDiarioHeader` | `CAB_INFORM` | Cabeçalho. `dt_compt` e `dt_gerac_arq` no formato `DD/MM/AAAA`. |
| `InformeDiarioInform` | `INFORM` | O informe diário de um fundo. |
| `SignificantShareholder` | `COTST_SIGNIF` | Um cotista com participação ≥ 20% do PL (bloco opcional). |

**Identificação do fundo:** cada `INFORM` informa **exatamente um** de `cnpj_fdo` (classe,
validado por dígito verificador) **ou** `cod_subclasse` (subclasse). Informar ambos — ou nenhum —
levanta `ValidationError`.

**Campos obrigatórios:** `data_prox_pl` (`DD/MM/AAAA`), `vl_total`, `vl_quota` (até 12 casas),
`patrim_liq`, `captc_dia`, `resg_dia`, `vl_total_sai`, `vl_total_atv` (monetários, 2 casas) e
`nr_cotst` (inteiro ≥ 0). `lista_cotst_signif` é opcional; `pr_cotst` tem até 4 casas.

- **Decimais** são **truncados em direção a zero** (`ROUND_DOWN`), nunca arredondados; passe
  `str`/`Decimal`, nunca `float`.
- Na serialização, decimais saem com **vírgula** (`1,50`); o arquivo é gravado em `windows-1252`.

---

## Exemplos

### Arquivo XML mínimo

Um cabeçalho e um `INFORM` com os campos obrigatórios.

```python
from filings_cvm.submission import (
    InformeDiario,
    InformeDiarioDocument,
    InformeDiarioHeader,
    InformeDiarioInform,
)

doc = InformeDiarioDocument(
    header=InformeDiarioHeader(dt_compt="15/01/2025", dt_gerac_arq="15/01/2025"),
    informs=[
        InformeDiarioInform(
            cnpj_fdo="11222333000181",
            data_prox_pl="16/01/2025",
            vl_total="1000000.00", vl_quota="1.23456789",
            patrim_liq="999999.50", captc_dia="0", resg_dia="0",
            vl_total_sai="0", vl_total_atv="0", nr_cotst=0,
        )
    ],
)

print(InformeDiario().to_xml(doc))
```

### Escrever direto em disco (codificação da CVM)

```python
InformeDiario().to_xml(doc, output_path="informe_20250115.xml")
```

### Cotistas com participação ≥ 20% do PL

O bloco `LISTA_COTST_SIGNIF` é opcional; `pr_cotst` sai com até 4 casas e vírgula decimal.

```python
from filings_cvm.submission import InformeDiarioInform, SignificantShareholder

inform = InformeDiarioInform(
    cnpj_fdo="11222333000181",
    data_prox_pl="16/01/2025",
    vl_total="0", vl_quota="1.0", patrim_liq="0",
    captc_dia="0", resg_dia="0", vl_total_sai="0", vl_total_atv="0",
    nr_cotst=1,
    lista_cotst_signif=[
        SignificantShareholder(
            tp_pessoa="PJ",
            cpf_cnpj_cotst="11222333000181",   # CPF para PF, CNPJ para PJ
            pr_cotst="25.5",                    # <PR_COTST>25,5000</PR_COTST>
        ),
    ],
)
```

### Identificar o fundo por classe OU subclasse (nunca ambos)

Informar os dois — ou nenhum — falha cedo na construção do modelo.

```python
from pydantic import ValidationError
from filings_cvm.submission import InformeDiarioInform

try:
    InformeDiarioInform(
        cnpj_fdo="11222333000181",
        cod_subclasse="SUB123",   # conflito: classe E subclasse
        data_prox_pl="16/01/2025",
        vl_total="0", vl_quota="1.0", patrim_liq="0",
        captc_dia="0", resg_dia="0", vl_total_sai="0", vl_total_atv="0",
        nr_cotst=0,
    )
except ValidationError as exc:
    print("Identificador ambíguo recusado:", exc)
```
