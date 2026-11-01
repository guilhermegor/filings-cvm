# **Informe Diário — V2**

Envio (→ CVM) do padrão **Informe Diário V2**, vigente de 01/07/2012 a 30/09/2015
([`PadraoXMLInfoDiarioNet739.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiarioNet739.asp)).
Para a versão atual veja [Informe Diário V4](informe_diario.md).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md)

---

## Descrição

Monte um `InformeDiarioV2Document` (um `InformeDiarioV2Header` + até 100 `InformeDiarioV2Inform`)
e serialize com `InformeDiarioV2().export(...)`. Namespace `urn:infdiario`, `COD_DOC=1`,
`VERSAO=2.0`, arquivo em `windows-1252`.

Diferenças medidas na página contra o V4: o fundo é identificado só por `CNPJ_FDO` (sem
`COD_SUBCLASSE`) e não existe `DATA_PROX_PL`. Escalas e o bloco `SignificantShareholder`
são os do V4 (reutilizados, não copiados). `NOME_FUNDO`, `RESG_NAO_PROCES` e `LIQ_DIA_DISPON`
aparecem na página apenas em comentários HTML e não são emitidos.

Ordem das tags de `INFORM`: `CNPJ_FDO`, `VL_TOTAL`, `VL_QUOTA`, `PATRIM_LIQ`, `CAPTC_DIA`,
`RESG_DIA`, `VL_TOTAL_SAI`, `VL_TOTAL_ATV`, `NR_COTST`, `LISTA_COTST_SIGNIF` (opcional).
Monetários com 2 casas, `VL_QUOTA` até 12, `PR_COTST` até 4; decimais são truncados e saem com vírgula.

## Exemplo

```python
from filings_cvm.submission import (
    InformeDiarioV2,
    InformeDiarioV2Document,
    InformeDiarioV2Header,
    InformeDiarioV2Inform,
)

header = InformeDiarioV2Header(dt_compt="15/01/2014", dt_gerac_arq="16/01/2014")
inform = InformeDiarioV2Inform(
    cnpj_fdo="11222333000181", vl_total="100.00", vl_quota="1.5", patrim_liq="100.00",
    captc_dia="0", resg_dia="0", vl_total_sai="0", vl_total_atv="0", nr_cotst=1,
)
xml = InformeDiarioV2().export(InformeDiarioV2Document(header=header, informs=[inform]))
```
