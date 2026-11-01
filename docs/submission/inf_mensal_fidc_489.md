# **Informe Mensal FIDC — ICVM 489**

Envio (→ CVM) do padrão **Informe Mensal FIDC** vigente **até a data-base 2019-11-01**
([`PadraoXMLMensalFIDC489.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLMensalFIDC489.asp)).
Para períodos posteriores use o layout da ICVM 576 ([Informe Mensal FIDC](inf_mensal_fidc.md)).

> **Veja também:** [Referência da API](../api.md) para cada símbolo público · [Uso](../usage.md)
> para instalação e o conceito geral.

---

## Descrição

Monte um `InfMensalFidc489Document` (`cab_inform` + `lista_inform`) e serialize com
`InfMensalFidc489().export(...)`. O arquivo contém **um** informe: um fundo e uma competência.
O XML usa o namespace `urn:fidc` e é gravado em `windows-1252`, de forma atômica (arquivo
temporário no mesmo diretório e `os.replace`).

Os blocos idênticos nas duas páginas da CVM são **importados** do schema da ICVM 576, não copiados.
Diferenças medidas na página:

| Bloco | ICVM 489 |
|-------|----------|
| `CAB_INFORM` | Seis tags; sem `PR_ENTRE_*` / `TP_DIAS_*`. |
| `APLIC_ATIVO` | Sem `LISTA_CEDENT_CRED_EXISTE` e sem `VL_PVS_*`; `DICRED` só tem `VL_DICRED` e `VL_DICRED_CEDENT`. |
| `OUTRAS_INFORM` | Plano: `DESC_SERIE_CLASSE_SENIOR_SERIE`/`_SUBORD`, `RENT_MES` (`PR_APURADA_SENIOR`/`_SUBORD`), `CAPT_MES_*`, `RESG_MES_*`, `RESG_SOLIC_*`, `AMORT_*`, `LIQUIDEZ`, `DESEMP_SENIOR`/`_SUBORD`. Sem `NUM_COTISTAS_DESC` e sem `GARANTIA`. |
| `NUM_COTISTAS` | Quatro inteiros: `QT_TOTAL_COTISTAS`, `_SENIOR`, `_SUBORD` e `QT_COTISTAS_SUBORD`. |

**Regras da CVM aplicadas na construção do modelo**

- **Escalas:** monetários, quantidades e percentuais com **2 casas**; `QT_COTAS`/`VL_COTAS` da
  descrição da série e `VL_COTA` de amortização com até **8**. O excedente é **truncado**. Passe
  `str`/`Decimal`, nunca `float`.
- **Somatórios (itens 1 a 31):** cada total deve igualar a soma prescrita; a provisão deve ser
  positiva e menor ou igual aos créditos que cobre; `VL_SOM_PRAZO_VENC` e `VL_SOM_INAD_VENC` devem
  fechar com `CRED_EXISTE`.
- **Fundo aberto** deve preencher ao menos um campo de `LIQUIDEZ`; para o fechado é facultativo.
- Pelo menos uma série da classe sênior em cada bloco; a classe subordinada pode ficar vazia.
- Tags desconhecidas levantam `ValidationError`.

⚠️ A página não declara cardinalidade por atributo. A repetição por série/classe é inferida de
"separar por classe e série", de "classe subordinada N" e do item 31 ("Subordinada 1 + ... + n").

---

## Exemplos

```python
from filings_cvm.submission import InfMensalFidc489, InfMensalFidc489Document

doc = InfMensalFidc489Document.model_validate(payload)  # payload: dict com todos os blocos
InfMensalFidc489().export(doc, output_path="inf_mensal_fidc_201910.xml")
```
