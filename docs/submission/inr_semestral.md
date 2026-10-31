# **Informe Semestral de Investidor não Residente**

Envio (→ CVM) do padrão **Informe Semestral de INR**
([`PadraoXMLInfoSemestralINR.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoSemestralINR.asp)).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

O informe é composto por **dois arquivos enviados conjuntamente**, com a mesma competência e os
mesmos investidores. Há um writer para cada um, sobre um schema compartilhado
(`inr_semestral.py`).

| Arquivo | Página da CVM | `COD_DOC` | Namespace | Writer | Documento |
|---------|---------------|-----------|-----------|--------|-----------|
| Parte I (fluxos de recursos) | `PadraoXMLInfoSemestralINRParte1.asp` | 69 | `urn:infmensal` | `InrSemestralParte1` | `InrParte1Document` |
| Parte II (aplicações) | `PadraoXMLInfoSemestralINRParte2.aspx` | 70 | `urn:cda` | `InrSemestralParte2` | `InrParte2Document` |

Os namespaces são copiados literalmente da CVM (o da Parte I diz `infmensal`, mesmo sendo o
informe semestral). Ambos os arquivos aceitam até **1000 participantes** (`PARTICIPANTE` / `INFORM`).

### Parte I

- Cabeçalho: `cd_cvm` (código CVM do representante, até 5 dígitos), `dt_compt` (`MM/AAAA`),
  `dt_gerac_arq` (`DD/MM/AAAA`).
- Cada participante: `cod_partic` (`AAAAA.BBBBBB.CCCCCC.T-DV`, sem zeros à esquerda; o primeiro
  segmento deve ser o `cd_cvm` do cabeçalho), `entrada_saida`, `transf_recursos`, os blocos
  opcionais `recursos_mesmo_invest` e `recursos_outro_invest` (recebidos e enviados, repetíveis) e
  `patrim_liq`.
- Todos os valores são **inteiros não negativos**, em reais ("numérico e inteiro").

### Parte II

Os blocos de ativos saem **na ordem do padrão**: `TIT_PUB`, `COTAS`, `SWAP` (+ `NOCION_SWAP`),
`DEMAIS_CODIF`, `DEP_PRAZO_TIT_IF`, `TIT_AGRO_CRED_PRIV`, `INV_EXT`, `DEMAIS_N_CODIF`. Cada um pode
repetir; pelo menos um é obrigatório por participante.

Regras de tabela aplicadas na validação:

- **Bloco × tipo de aplicação** (tabela "Blocos de repetição").
- **Tabela A**: `QTDE_POS_FIM` e `NOCION_POS_FIM` obrigatórios ou proibidos por tipo de aplicação;
  `MERC_POS_FIM` sempre obrigatório.
- **Tabela B**: o tipo de ativo precisa estar relacionado ao tipo de aplicação.
- **Tabelas C, D, E, G, H**: tipo de ativo, indexador, swap (`SWP` + código), país e bolsa.
- Pós-fixado (`ST_TIT_POS_FIX=S`) exige `TIT_POS_FIX_INDEX` e proíbe `TIT_PRE_FIX_TAXA_CONTR`; o
  pré-fixado, o inverso. `CLASSIF_RISCO` existe se e somente se `ST_CLASSIF_RISCO=S`.
- CNPJ/CPF validados por forma e dígito verificador, e gravados sem máscara e sem zeros à esquerda.

### Escalas decimais

| Campo | Escala |
|-------|--------|
| `QTDE_POS_FIM` | 6 casas, não negativo |
| `MERC_POS_FIM`, `NOCION_POS_FIM`, `NOCION_SWAP` | 2 casas |
| `TIT_POS_FIX_PR_INDEX`, `TIT_POS_FIX_CUPOM`, `TIT_PRE_FIX_TAXA_CONTR` | 6 casas |
| `VALOR_AT_EXT` | 2 casas (**premissa**: a página não informa escala) |

Excesso de casas é **truncado** (`ROUND_DOWN`); `float` é recusado. Na saída a vírgula é o
separador decimal e o arquivo é gravado em `windows-1252` (a codificação ocorre antes de abrir o
arquivo, então um caractere inválido nunca apaga um arquivo existente).

### Premissas e conflitos da especificação

- Campos de código sem tamanho declarado (`COD_ATIV`, `COD_SELIC`, `COD_ATIVO_BV_MERC`): até 50
  caracteres de `[0-9A-Za-z._/-]`.
- O bloco `DEMAIS_N_CODIF` também aceita os tipos de `DEMAIS_CODIF` (exceto 193) cujo ativo não
  está no cadastro, como diz a tabela de blocos.
- As colunas opcionais (`OP`) de vendas e aquisições da Tabela A não existem neste XML, que só
  carrega a posição final; a coluna "Empresa Ligada" não é modelada.
- A Tabela E traz a linha `Outros`; o código aceito é `SWPOutros`.
- `NOCION_SWAP` é obrigatório se houver bloco `SWAP` e proibido caso contrário.
- Nenhum validador da CVM foi executado contra a saída.

---

## Exemplos

```python
from filings_cvm.submission import (
    InrParte1Document,
    InrParte2Document,
    InrSemestralParte1,
    InrSemestralParte2,
)

parte1 = InrParte1Document(
    header={"cd_cvm": "123", "dt_compt": "06/2026", "dt_gerac_arq": "31/07/2026"},
    participantes=[
        {
            "cod_partic": "123.456.789.0-1",
            "entrada_saida": {"vl_entr": 10, "vl_saida": 20},
            "transf_recursos": {
                "vl_invest_carteira_haver_nres": 0,
                "vl_haver_nres_invest_carteira": 0,
                "vl_invest_carteira_adr": 0,
                "vl_adr_invest_carteira": 0,
                "vl_invest_carteira_estrang_direta": 0,
                "vl_estrang_direta_invest_carteira": 0,
            },
            "patrim_liq": 99,
        }
    ],
)
InrSemestralParte1().export(parte1, output_path="inr_semestral_parte1.xml")

parte2 = InrParte2Document(
    header={"dt_compt": "06/2026", "dt_gerac_arq": "31/07/2026"},
    informs=[
        {
            "cod_partic": "123.456.789.0-1",
            "cotas": [
                {
                    "cnpj_fdo": "11.222.333/0001-81",
                    "pos_fim": {"qtde_pos_fim": "1.5", "merc_pos_fim": "10.99"},
                }
            ],
        }
    ],
)
xml = InrSemestralParte2().export(parte2)  # retorna str
```
