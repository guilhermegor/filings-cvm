# **Informe Mensal FIDC — ICVM 576**

Envio (→ CVM) do padrão **Informe Mensal FIDC**, vigente desde 2019-11-01
([`PadraoXMLMensalFIDC576.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLMensalFIDC576.asp)).
O layout anterior (`PadraoXMLMensalFIDC489.asp`) está em [Informe Mensal FIDC — ICVM 489](inf_mensal_fidc_489.md).

> **Veja também:** [Referência da API](../api.md) para cada símbolo público · [Uso](../usage.md)
> para instalação e o conceito geral.

---

## Descrição

Monte um `InfMensalFidcDocument` (`cab_inform` + `lista_inform`) e serialize com
`InfMensalFidc().export(...)`. O arquivo contém **um** informe: um fundo e uma competência.
O XML usa o namespace `urn:fidc` e é gravado em `windows-1252`.

| Modelo | Tag XML | Papel |
|--------|---------|-------|
| `InfMensalFidcDocument` | `DOC_ARQ` | Documento completo. |
| `InfMensalFidcHeader` | `CAB_INFORM` | Fundo: `dt_compt` (`MM/AAAA`), CNPJ do administrador e do fundo, condomínio, exclusivo, vinculado e, só para fundo aberto, os prazos de resgate. |
| `InfMensalFidcInform` | `LISTA_INFORM` | Os blocos Ativo, Carteira por segmento, Passivo, PL, Comportamento, Negócios, Sacados, Taxas e Outras Informações. |

Cada tag XML é o nome do atributo em maiúsculas, na ordem do modelo (que é a ordem da CVM).

**Regras da CVM aplicadas na construção do modelo**

- **Escalas:** valores monetários, quantidades e percentuais com **2 casas**; `QT_COTAS`/`VL_COTAS`
  da descrição da série/classe, quantidades de cotas e `VL_COTA` de amortização com até **8**.
  O excedente é **truncado** (`ROUND_DOWN`), nunca arredondado. Passe `str`/`Decimal`, nunca `float`.
- **Tags obrigatórias:** todo valor deve ser informado ("preencher com zero"); são opcionais apenas
  `lista_cedent_cred_existe`, `lista_cedent`, `num_cotistas_desc` (a tag sai vazia), `desemp`
  (idem) e `liquidez` (obrigatória para fundo **aberto**, com ao menos um campo).
- **Fundo fechado** não pode informar `pr_entre_resgate`, `tp_dias_resgate`, `pr_entre_conver`
  nem `tp_dias_conver`.
- **Somatórios (itens 1 a 30 da página):** cada total deve ser igual à soma prescrita; a provisão
  deve ser positiva e menor ou igual aos créditos que cobre; `VL_SOM_PRAZO_VENC` e
  `VL_SOM_INAD_VENC` devem fechar com a carteira; `QT_TOTAL_COTISTAS_*` com as séries.
- **Sacados:** de 1 a 25, com CPF/CNPJ válido ou o marcador `99.999.999/9999-99` /
  `999.999.999-99` (sem CNPJ / isento de CPF).
- Pelo menos uma série da classe sênior em cada bloco de série.
- Tags desconhecidas levantam `ValidationError`.

---

## Exemplos

### Gerar o XML

O documento completo tem centenas de tags obrigatórias; monte-o a partir de um dicionário e
valide com `model_validate`.

```python
from filings_cvm.submission import InfMensalFidc, InfMensalFidcDocument

doc = InfMensalFidcDocument.model_validate(payload)  # payload: dict com todos os blocos
InfMensalFidc().export(doc, output_path="inf_mensal_fidc_202010.xml")
```

### Totais inconsistentes são recusados

```python
from pydantic import ValidationError

payload["lista_inform"]["patrliq"]["vl_patrim_liq"] = "10.00"  # VL_SOM_PATRLIQ continua 0,00
try:
    InfMensalFidcDocument.model_validate(payload)
except ValidationError as exc:
    print(exc)  # VL_SOM_PATRLIQ (item 16): SOMATÓRIO must be 10.00, got 0.00
```
