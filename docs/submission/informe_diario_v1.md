# **Informe Diário — V1**

Envio (→ CVM) do padrão **Informe Diário V1**
([`PadraoXMLInfoDiarioNet.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiarioNet.asp)), válido até 2012-07-01. A versão atual é o
[V4](informe_diario.md).

> **Veja também:** [Referência da API](../api.md).

## Diferenças medidas contra a página

- `CAB_INFORM`: só `COD_DOC` (1), `DT_COMPT`, `DT_GERAC_ARQ` — **sem `VERSAO`**.
- `INFORM` identificado só por `CNPJ_FDO`; **sem** `COD_SUBCLASSE`, `DATA_PROX_PL`, `VL_TOTAL_SAI`, `VL_TOTAL_ATV`.
- Ordem: `CNPJ_FDO, VL_TOTAL, VL_QUOTA, PATRIM_LIQ, CAPTC_DIA, RESG_DIA, NR_COTST, LISTA_COTST_SIGNIF`, dentro de `LISTA_INFORM`.
- Escalas: monetários 2 casas, `VL_QUOTA` até 12, `PR_COTST` até 4; vírgula decimal; truncado (`ROUND_DOWN`).
- Até 100 fundos por arquivo; namespace `urn:infdiario`; `windows-1252`.
- A página não fixa a cardinalidade de `LISTA_COTST_SIGNIF`; tratada como opcional (como no V4).

## Exemplo

```python
from filings_cvm.submission import (
    InformeDiarioV1, InformeDiarioV1Document, InformeDiarioV1Header, InformeDiarioV1Inform,
)

doc = InformeDiarioV1Document(
    header=InformeDiarioV1Header(dt_compt="15/01/2005", dt_gerac_arq="16/01/2005"),
    informs=[InformeDiarioV1Inform(
        cnpj_fdo="11222333000181", vl_total="1000.50", vl_quota="1.23",
        patrim_liq="1000.50", captc_dia="0", resg_dia="0", nr_cotst=3,
    )],
)
print(InformeDiarioV1().export(doc))
```
