# **CDA — V3**

Envio (→ CVM) do padrão **CDA V3** (Composição e Diversificação das Aplicações,
[`PadraoXMLCDANetV3.aspx`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLCDANetV3.aspx)).

> **Veja também:** [CDA V4](cda.md) (versão corrente; escalas, Tabelas A/B/D/F e regras
> compartilhadas) · [Referência da API](../api.md).

---

## Descrição

Monte um `CdaV3Document` (um `CdaV3Header` + até **50** `CdaV3Inform`, todos da mesma competência)
e serialize com `CdaV3().export(...)`. XML em `urn:cda`, `COD_DOC=3`, `VERSAO=3.0`, gravado em
`windows-1252`, vírgula como separador decimal.

O V3 compartilha com o V4 a ordem dos blocos, as escalas (`VL_PL` 21+2; `VL_*_NEGOC`/`MERC_POS_FIM`
15+2; `QTDE_*` 15+6; taxas 3+6) e as Tabelas A, B, D e F: esses modelos são **importados** do V4
(`CdaTitPub`, `CdaSwap`, `CdaDemaisCodif`, `CdaTitAgroCredPriv`, `CdaDemaisNCodif`, `CdaAplic`,
`CdaNegoc`, `CdaPosFim`, ...).

**Diferenças medidas na página do V3 (modelos próprios):**

| Ponto | V3 | V4 |
|-------|----|----|
| `VERSAO` | `3.0` | `4.0` |
| Fundos por arquivo | até 50 | até 1000 |
| `COTAS` | só `CNPJ_FDO` (`CdaV3Cotas`) | `CNPJ_FDO` ou `COD_SUBCLASSE` |
| `DEP_PRAZO_TIT_IF` | sem `DESC_ATIV_VINC` (`CdaV3DepPrazoTitIf`) | com |
| `INV_EXT` | sem `INV_COLETIVO`/`GEST_INV_COLETIVO` (`CdaV3InvExt`) | com |
| `APLIC` de `INV_EXT` | sem `ATIVO_EXT` | com |

Um campo exclusivo do V4 informado a um modelo V3 é recusado, e o `CdaV3` recusa um `CdaDocument`
(V4) com `TypeError`.

**Limites conhecidos:** os mesmos do [V4](cda.md) (Tabelas E, G e H não enumeradas; teto de 90 dias
em `QTDE_DIAS_CONFID`). A página do V3 descreve a tag do CNPJ do fundo como `CNPJ_FUNDO` na seção
de campos, mas o exemplo de XML usa `CNPJ_FDO`; o writer segue o XML de exemplo.

---

## Exemplo

```python
from filings_cvm.submission import CdaV3, CdaV3Document, CdaV3Header, CdaV3Inform

doc = CdaV3Document(
    header=CdaV3Header(dt_compt="03/2024", dt_gerac_arq="05/04/2024"),
    informs=[CdaV3Inform(cnpj_fdo="11.222.333/0001-81", vl_pl="1000000.00")],
)
xml = CdaV3().export(doc)
```
