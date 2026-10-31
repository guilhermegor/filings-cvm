# **Informe de Fundo 157**

Envio (→ CVM) do padrão **Informe de Fundo 157**
([`PadraoXMLInf157.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInf157.asp)).

> **Veja também:** [Referência da API](../api.md) para cada símbolo público · [Uso](../usage.md)
> para instalação e o conceito geral.

---

## Descrição

Monte um `InfFundo157Document` (um `InfFundo157Header` + de 1 a N `InfFundo157Cotista`) e
serialize com `InfFundo157().export(...)`.

| Modelo | Tag XML | Papel |
|--------|---------|-------|
| `InfFundo157Document` | `DOC_ARQ` / `LISTA_COTSTS` | Documento: `header` + `cotistas`. |
| `InfFundo157Header` | `DESC_FDO_157` | `COD_DOC` = 55 (fixo), `CNPJ_FDO_157`, `DT_GERAC_ARQ` `DD/MM/AAAA`, `DT_COMPTC` `MM/AAAA`. |
| `InfFundo157Cotista` | `COTST` | `CPF` (11 dígitos, sem máscara), `NOME` (até 200), `DT_FIM`, `CONF` (`S`/`N`). |

Os campos de cada modelo são o nome da tag em minúsculas e seguem a ordem do arquivo de exemplo
da CVM. Os modelos são imutáveis e recusam campos desconhecidos. O namespace é `urn:inffdo157`.

## Tipagem

A página **não tem nenhum campo decimal**. Datas são parseadas (`31/02` é recusada, ano ≥ 1900);
o formato é checado antes do dígito verificador, sem espaços ou quebra de linha: o CPF são
exatamente 11 dígitos `[0-9]`; o CNPJ aceita `[0-9A-Z]` nas 12 primeiras posições (CNPJ
alfanumérico de 2026) e dígitos verificadores numéricos, com ou sem máscara, e é gravado sem
máscara. `NOME` é não vazio, até 200 caracteres, sem caracteres de
controle e codificável em `windows-1252`.

### O que a página não diz (decisões deste repositório)

- **Formato de `DT_FIM`**: não declarado; adotado `DD/MM/AAAA`, como `DT_GERAC_ARQ`.
- **Cardinalidade de `COTST`**: "bloco de repetição" sem mínimo nem máximo; exigido **ao menos um**, sem teto.
- **Tamanho do CPF**: "sem traços e pontos"; exigidos 11 dígitos com dígito verificador válido.
- **Inconsistência textual**: a página chama a descrição de "padrão XML do informe diário"; é
  erro de copiar-e-colar, o padrão é o do Informe 157 (`COD_DOC=55`, `urn:inffdo157`).
- CPF repetido no mesmo arquivo e `DT_FIM` posterior à geração não são verificados (a página
  não os proíbe).

## Política de retry

Não se aplica: o writer não faz I/O de rede.

## Exemplos

```python
from filings_cvm.submission import InfFundo157, InfFundo157Document

doc = InfFundo157Document.model_validate(
    {
        "header": {
            "cnpj_fdo_157": "11222333000181",
            "dt_gerac_arq": "31/10/2026",
            "dt_comptc": "10/2026",
        },
        "cotistas": [
            {"cpf": "52998224725", "nome": "Maria da Conceição",
             "dt_fim": "15/09/2026", "conf": "S"},
        ],
    }
)
xml = InfFundo157().export(doc)                        # retorna str
InfFundo157().export(doc, output_path="inf157.xml")    # grava windows-1252, retorna None
```

O texto é codificado e checado como XML bem formado **antes** de abrir o destino: uma falha não
trunca um arquivo existente. Nenhum validador da CVM foi executado contra a saída.
