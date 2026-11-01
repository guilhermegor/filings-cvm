# **Informe Mensal de Investidor Não Residente**

Envio (→ CVM) do padrão **Informe Mensal INR**
([`PadraoXMLInfoMensalINR.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoMensalINR.asp)).

> **Veja também:** [Referência da API](../api.md) para cada símbolo público · [Uso](../usage.md)
> para instalação e o conceito geral.

---

## Descrição

Monte um `InrMensalDocument` (um `InrMensalHeader` + de 1 a 1000 `Participante`, todos da mesma
competência) e serialize com `InrMensal().export(...)`. O XML usa o namespace `urn:infmensal`,
`COD_DOC=477` e `VERSAO=1.0`, gravado em `windows-1252`.

| Modelo | Tag XML | Papel |
|--------|---------|-------|
| `InrMensalDocument` | `DOC_ARQ` | `header` + `participantes` (1 a 1000, códigos únicos). |
| `InrMensalHeader` | `CAB_INFORM` | `cd_cvm` (até 5 dígitos), `dt_compt` `MM/AAAA`, `dt_gerac_arq` `DD/MM/AAAA`. |
| `Participante` | `PARTICIPANTE` | Um participante; `cod_partic` no formato `AAAAA.BBBBBB.CCCCCC.T-DV`. |
| `EntradaSaida` | `ENTRADA_SAIDA` | `vl_entr`, `vl_saida`. |
| `MovRecursos` | `MOV_RECURSOS` | `transf_recursos` + 2 contêineres opcionais. |
| `TransfRecursos` | `TRANSF_RECURSOS` | Seis valores de transferência entre modalidades. |
| `RecursosMesmoInvest` | `RECURSOS_MESMO_INVEST` | Opcional: listas `RecursosRecebMesmoInvest` / `RecursosEnvMesmoInvest`. |
| `RecursosOutroInvest` | `RECURSOS_OUTRO_INVEST` | Opcional: listas `RecursosRecebOutroInvest` / `RecursosEnvOutroInvest`. |
| `Aplicacoes` | `APLICACOES` | Código da Tabela A (1 a 30), valor de mercado e, só para 15 a 24, o nocional. |

**Regras:** os códigos de participante não aceitam zeros à esquerda e `T` é `0` ou `1`; o dígito
verificador é checado apenas como um dígito (a página não publica o algoritmo). Contêineres
opcionais vazios são recusados (a página manda omitir). `vl_nocion_aplic` é obrigatório para os
códigos 15 a 24 e proibido nos demais.

**Valores:** todo valor é inteiro (`int`, `Decimal` sem fração ou `str` de dígitos); `float`,
`bool` e valores fracionários são recusados, nunca truncados. Fluxos, transferências e nocionais
não podem ser negativos; valor de mercado e patrimônio líquido podem.

### Pontos em que a página é ambígua (decisões)

- A página pede "vírgula para casas decimais" e, ao mesmo tempo, "valor numérico e inteiro" em
  todo campo: adotou-se **inteiro**, sem parte decimal.
- O exemplo traz `COD_DOC` 477, a lista de tags diz "deve ser 'XX'": usou-se **477**.
- Premissas não declaradas pela página: código de participante único por arquivo. A página define
  `CD_CVM` e o `AAAAA` de `COD_PARTIC` como o código CVM do representante, então o `AAAAA` de cada
  participante tem de igualar `CD_CVM`.
- Nenhum validador da CVM foi executado.

---

## Exemplos

### Arquivo XML mínimo

```python
from filings_cvm.submission import (
    EntradaSaida,
    InrMensal,
    InrMensalDocument,
    InrMensalHeader,
    MovRecursos,
    Participante,
    TransfRecursos,
)

doc = InrMensalDocument(
    header=InrMensalHeader(cd_cvm="12345", dt_compt="01/2025", dt_gerac_arq="15/02/2025"),
    participantes=[
        Participante(
            cod_partic="12345.123456.654321.1-9",
            entrada_saida=EntradaSaida(vl_entr=10, vl_saida=20),
            mov_recursos=MovRecursos(
                transf_recursos=TransfRecursos(
                    vl_invest_carteira_haver_nres=0,
                    vl_haver_nres_invest_carteira=0,
                    vl_invest_carteira_adr=0,
                    vl_adr_invest_carteira=0,
                    vl_invest_carteira_estrang_direta=0,
                    vl_estrang_direta_invest_carteira=0,
                )
            ),
            patrim_liq=500,
        )
    ],
)

print(InrMensal().export(doc))
```

### Escrever direto em disco

```python
InrMensal().export(doc, output_path="inr_mensal_202501.xml")
```

### Aplicação com derivativo

```python
from filings_cvm.submission import Aplicacoes

Aplicacoes(cd_aplic=15, vl_mercado_aplic=-5, vl_nocion_aplic=900)  # nocional obrigatório
```
