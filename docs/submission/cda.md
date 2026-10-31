# **CDA — V4**

Envio (→ CVM) do padrão **CDA V4** (Composição e Diversificação das Aplicações,
[`PadraoXMLCDANetV4.aspx`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLCDANetV4.aspx)).

> **Veja também:** [Referência da API](../api.md) para cada símbolo público · [Uso](../usage.md)
> para instalação e o conceito geral.

---

## Descrição

Monte um `CdaDocument` (um `CdaHeader` + até 1000 `CdaInform`, um por fundo/classe, todos da mesma
competência) e serialize com `Cda().export(...)`. O XML usa o namespace `urn:cda`, `COD_DOC=3` e
`VERSAO=4.0`; o arquivo é gravado em `windows-1252`.

| Modelo | Tag XML | Papel |
|--------|---------|-------|
| `CdaDocument` | `DOC_ARQ` | `header` + `informs` (até 1000 fundos). |
| `CdaHeader` | `CAB_INFORM` | `dt_compt` em `MM/AAAA`, `dt_gerac_arq` em `DD/MM/AAAA`. |
| `CdaInform` | `INFORM` | Um fundo: `cnpj_fdo`, `vl_pl` e as listas de blocos de ativos. |
| `CdaTitPub` / `CdaCotas` / `CdaSwap` | `TIT_PUB` / `COTAS` / `SWAP` | Blocos 1 a 3. |
| `CdaDemaisCodif` | `DEMAIS_CODIF` | Demais ativos codificados. |
| `CdaDepPrazoTitIf` / `CdaTitAgroCredPriv` | `DEP_PRAZO_TIT_IF` / `TIT_AGRO_CRED_PRIV` | Blocos 5 e 6. |
| `CdaInvExt` / `CdaDemaisNCodif` | `INV_EXT` / `DEMAIS_N_CODIF` | Blocos 7 e 8. |
| `CdaAplic`, `CdaNegoc`, `CdaPosFim` | `APLIC`, `NEGOC`, `POS_FIM` | Aplicação, negócios do mês e posição final. |

**Ordem dos blocos:** o writer sempre emite os blocos na ordem exigida pela CVM (títulos públicos,
cotas, swap, demais codificados, depósitos a prazo, agro/crédito privado, exterior, não codificados).

**Escalas** (truncadas com `ROUND_DOWN`, vírgula decimal na saída): `VL_PL` 21 inteiras + 2;
`VL_*_NEGOC` e `MERC_POS_FIM` 15 + 2; `QTDE_*` 15 + 6; `TIT_POS_FIX_PR_INDEX`, `TIT_POS_FIX_CUPOM`
e `TIT_PRE_FIX_TAXA_CONTR` 3 + 6. Passe `str`/`Decimal`, nunca `float`.

**Validações vindas da página da CVM:**

- Quais `COD_TP_APLIC` cada bloco aceita (tabela *Blocos x Tipos de Aplicações*).
- Matriz da *Tabela A*: `EMPR_LIGADA`, vendas, aquisições e quantidade final são obrigatórios,
  opcionais ou proibidos conforme o tipo de aplicação; quantidade e valor andam juntos.
- *Tabela B*: o `COD_TP_ATIV` deve ser compatível com o `COD_TP_APLIC`.
- Pós-fixado exige `TIT_POS_FIX_INDEX` (indexador da Tabela D); pré-fixado exige a taxa contratada.
  `CLASSIF_RISCO` existe se, e somente se, `ST_CLASSIF_RISCO` é `S`.
- CNPJ/CPF validados por dígito verificador. Conforme a página, zeros à esquerda são omitidos
  na saída.

Os blocos `COTAS`, `DEP_PRAZO_TIT_IF` e `INV_EXT` não têm a tag `COD_TP_APLIC` no XML (o tipo é
implícito: 197, 74 e 189), portanto `cod_tp_aplic` deve ficar vazio neles.

---

## Exemplos

### Um fundo com uma posição em ações

```python
from filings_cvm.submission import (
    Cda, CdaAplic, CdaDemaisCodif, CdaDocument, CdaHeader, CdaInform, CdaNegoc, CdaPosFim,
)

aplic = CdaAplic(
    cod_tp_aplic=37,
    empr_ligada="N",
    qtde_dias_confid=0,
    negoc=CdaNegoc(
        tp_negoc=1,
        qtde_vendas_negoc="0", vl_vendas_negoc="0",
        qtde_aquis_negoc="100", vl_aquis_negoc="3500.00",
    ),
    pos_fim=CdaPosFim(qtde_pos_fim="100", merc_pos_fim="3550.00"),
)
doc = CdaDocument(
    header=CdaHeader(dt_compt="03/2024", dt_gerac_arq="05/04/2024"),
    informs=[
        CdaInform(
            cnpj_fdo="11.222.333/0001-81",
            vl_pl="1000000.00",
            demais_codif=[
                CdaDemaisCodif(
                    cod_ativ="PETR4", cod_tp_ativ=1, dt_ini_vigen="01/01/2020", aplic=aplic
                )
            ],
        )
    ],
)
xml = Cda().export(doc)              # devolve a string
Cda().export(doc, "cda_202403.xml")  # ou grava o arquivo (windows-1252)
```
