# **CDA — V2**

Envio (→ CVM) do padrão **CDA V2** (Nova CDA,
[`PadraoXMLCDANet.aspx`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLCDANet.aspx)).
A versão atual é o [CDA V4](cda.md).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

Monte um `CdaV2Document` (um `CdaV2Header` + até **50** `CdaV2Inform`, um por fundo/classe, todos da
mesma competência) e serialize com `CdaV2().export(...)`. XML em `windows-1252`, namespace
`urn:cda`, `COD_DOC=3`, `VERSAO=2.0`. Vírgula como separador decimal.

| Modelo | Tag XML | Papel |
|--------|---------|-------|
| `CdaV2Inform` | `INFORM` | `cnpj_fdo`, `vl_pl` (2 casas) e as listas de blocos. |
| `CdaV2TitPub` | `TIT_PUB` | `cod_selic`, `dt_venc`, `aplic` (tipo 75). |
| `CdaV2Cotas` | `COTAS` | `cnpj_fdo`, `aplic` (tipos 92, 93, 190). |
| `CdaV2Swap` | `SWAP` | `cod_swap` (`SWP`+3), `aplic` (183/184). |
| `CdaV2DemaisCodif` | `DEMAIS_CODIF` | `cod_ativ`, `cod_tp_ativ`, `dt_ini_vigen`, `aplic`. |
| `CdaV2DemaisNCodif` | `DEMAIS_N_CODIF` | `cod_tp_ativ`, `desc`, `emis`, `aplic`. |

Ordem dos blocos: `TIT_PUB`, `COTAS`, `SWAP`, `DEMAIS_CODIF`, `DEMAIS_N_CODIF`. Em `APLIC`:
`COD_TP_APLIC`, `QTDE_DIAS_CONFID` (obrigatório, 0 a 90), `NEGOC`, `POS_FIM`
(`QTDE_POS_FIM`, `CUSTO_CORREC_POS_FIM`, `MERC_POS_FIM`).

## Escalas

`VL_PL` 21+2; `VL_*_NEGOC`, `CUSTO_CORREC_POS_FIM`, `MERC_POS_FIM` 15+2; `QTDE_*` 15+6. Excesso é
truncado (`ROUND_DOWN`); `float` é recusado.

## Diferenças para o V4

Cinco blocos (sem `DEP_PRAZO_TIT_IF`, `TIT_AGRO_CRED_PRIV`, `INV_EXT`), `POS_FIM` com
`CUSTO_CORREC_POS_FIM`, sem `EMPR_LIGADA`, sem `COD_SUBCLASSE`, Tabela A própria (Vendas,
Aquisições, Posição Final com Quant./Custo/Mercado) e máximo de 50 fundos por arquivo. A tag do
CNPJ é `CNPJ_FDO` (o exemplo XML da página; a tabela de campos da mesma página grafa
`CNPJ_FUNDO`, divergência que a página não resolve).

```python
from filings_cvm.submission import CdaV2
xml = CdaV2().export(doc)
```
