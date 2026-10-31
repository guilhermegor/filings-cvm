# **Informe Art. 12 Res. CVM 33 — Escriturador**

Envio (→ CVM) do informe dos escrituradores de valores mobiliários
([`PadraoXMLPrest.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPrest.asp)).

> **Veja também:** [Referência da API](../api.md) para cada símbolo público · [Uso](../usage.md)
> para instalação e o conceito geral.

---

## Descrição

Monte um `PrestDocument` (um `PrestHeader` + uma ou mais `PrestInform`) e serialize com
`InformeArt12Res33().export(...)`. O XML usa o namespace `urn:prestserv` e `COD_ARQ=29`. O informe
é mensal; um arquivo cobre uma única competência, com vários prestadores se necessário.

| Modelo | Tag XML | Papel |
|--------|---------|-------|
| `PrestDocument` | `DOC_ARQ` | Arquivo: `ds_inform` + `prestadores` (1 ou mais). |
| `PrestHeader` | `DS_INFORM` | `dt_compt` (`MM/AAAA`) e `dt_gerac_arq` (`DD/MM/AAAA`). |
| `PrestInform` | `INFORM_PREST` | Um prestador: `ds_prest` + `emissores` (1 ou mais). |
| `PrestDados` | `DS_PREST` | `cnpj_escriturador` e `cd_tp_prest` (Tabela A). |
| `PrestEmissor` | `EMISSOR` | `cnpj_emissor` + `ativos` (1 ou mais). |
| `PrestAtivo` | `ATIVO` | `ativo_escriturado` (Tabela B), `dt_inicio_contrato`, `dt_fim_contrato` opcional. |

---

## Tipagem

Não há campo decimal neste padrão. CNPJ é aceito com ou sem máscara, validado por dígito
verificador (formato checado antes) e gravado **sem** pontuação, como a página exige. Datas são
datas reais (`31/02` falha; ano mínimo 1900).

### Regras entre campos

- `dt_gerac_arq` não pode ser anterior ao mês da competência.
- `dt_fim_contrato`, quando presente, não pode ser anterior a `dt_inicio_contrato`.
- `cd_tp_prest`: `41` sempre; `42`, `52` e `65` só para competência anterior a `07/2014`
  (a página os declara migrados para 41 a partir de 01/07/2014).
- Sem `cnpj_emissor` repetido dentro de um prestador, nem `cnpj_escriturador` repetido no arquivo.

---

## Limites e pontos em aberto

- **A página se contradiz:** o exemplo fecha `LISTA_PREST` como `</LISTA_APREST>`. Usada
  `LISTA_PREST` (a tag de abertura e a da lista de campos).
- A página não limita o número de prestadores, emissores ou ativos; cada lista exige ao menos um
  item e nenhum teto foi inventado.
- `DT_FIM_CONTRATO` só deve aparecer se o contrato encerrou no mês anterior; isso depende de dados
  fora do arquivo e **não é verificado**.
- Nenhum validador da CVM (a página linka um testador de sintaxe) foi executado.

---

## Exemplos

### Arquivo XML mínimo

```python
from filings_cvm.submission import (
    InformeArt12Res33, PrestAtivo, PrestDados, PrestDocument,
    PrestEmissor, PrestHeader, PrestInform,
)

doc = PrestDocument(
    ds_inform=PrestHeader(dt_compt="09/2025", dt_gerac_arq="03/10/2025"),
    prestadores=(
        PrestInform(
            ds_prest=PrestDados(cnpj_escriturador="11222333000181", cd_tp_prest=41),
            emissores=(
                PrestEmissor(
                    cnpj_emissor="11444777000161",
                    ativos=(PrestAtivo(ativo_escriturado="A1", dt_inicio_contrato="01/02/2020"),),
                ),
            ),
        ),
    ),
)
xml = InformeArt12Res33().export(doc)                     # retorna str
InformeArt12Res33().export(doc, output_path="prest.xml")  # grava windows-1252, retorna None
```

### Contrato encerrado

Informe do mês seguinte ao encerramento: acrescente `dt_fim_contrato="30/09/2025"` ao `PrestAtivo`.
