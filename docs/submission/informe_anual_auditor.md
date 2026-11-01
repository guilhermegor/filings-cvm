# **Informe Anual de Auditor**

Envio (→ CVM) do padrão **Informe Anual de Auditor**
([`PadraoXMLAuditorAnual.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLAuditorAnual.asp)).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md)

---

## Descrição

Monte um `InformeAnualAuditorDocument` (um arquivo = um auditor e um ano base) e serialize com
`InformeAnualAuditor().export(...)`. O XML usa o namespace `urn:audtanual`, `COD_DOC=23` e
codificação `windows-1252`.

| Modelo | Tag XML |
|--------|---------|
| `InformeAnualAuditorDocument` | `DOC_ARQ` / `INFORM_AUDIT` |
| `AuditorHeader` | `DS_INFORM` |
| `AuditorIdentity` | `DS_AUDIT` |
| `AuditorAddress` | `ENDER` (em `LISTA_ENDER`) |
| `AuditorRepresentative` | `RESP` (em `LISTA_RESP`) |
| `AuditedEntity` | `ENTID_AUDITA` (em `LISTA_ENTID_AUDITA`) |
| `AuditorAnnualBilling` | `FATURA_ANUAL` |
| `AuditorStaff` | `RH` |
| `AffiliatedEntity` | `ENTID_COLIG` (em `LISTA_ENTID_COLIG`) |
| `AuditorTraining` | `TREINA` (em `LISTA_TREINA`) |
| `TrainingParticipant` | `TREINA_PESSOA` (em `LISTA_TREINA_PESSOA`) |

**Regras aplicadas:**

- Auditor `PF`: um único endereço (sede, sem `NM_FILIAL`), sem `LISTA_RESP`, sem `QT_SOCIOS`,
  cargos de treinamento só `4` (AIPF). Auditor `PJ`: `QT_SOCIOS` obrigatório, cargos `1` a `3`.
- `NR_PF_PJ` e `NR_PF` são validados (formato e dígitos verificadores) e saem só com dígitos.
- `TP_ENTID` na Tabela B (48 códigos), `TP_TREINA` na Tabela D, `TP_CARGO` na Tabela C.
- `PR_FATURA` só acima de 10% (até 100); `VL_AUDIT`/`PR_AUDIT` com 2 casas, truncadas, nunca
  `float`. `PR_AUDIT` fica entre 0 e 100.
- Datas `DD/MM/AAAA` precisam existir; `ANO_BASE` não pode ser posterior ao ano de `DT_GERAC_ARQ`.
- `NR_PJ` da coligada é obrigatório se `ST_ESTR=N` e proibido se `S`.
- `LISTA_RESP` e `LISTA_TREINA` vazias são omitidas; as demais listas permanecem.
- Limites da Tabela A (upload): 1.000 endereços, 8.000 entidades auditadas, 1.000 coligadas.

## Decisões sobre o que a página não diz

- `DS_NOME` da entidade auditada e `CD_MUN`/`CD_CVM`: sem tamanho nem formato declarado — assumido até 100
  caracteres e inteiro positivo.
- `CEP` com exatamente 8 dígitos (único campo que mantém zero à esquerda).
- E-mail: um único endereço, até 50 caracteres.
- Namespace `urn:audtanual` vem do exemplo da página.
- A página lista `LISTA_ENTID_COLIG` antes de `LISTA_TREINA` no texto; o exemplo termina em
  `LISTA_ENTID_COLIG`. A ordem de saída segue o texto das tags.
- Nenhum validador da CVM foi executado.

## Tipagem

Modelos Pydantic fechados e imutáveis; decimais como `Decimal` truncado (`ROUND_DOWN`) e saída com
vírgula.

## Política de retry

Não se aplica: o envio não faz chamadas de rede. A gravação codifica o texto **antes** de abrir o
destino, então uma falha de codificação não trunca um arquivo existente.

---

## Exemplos

```python
from filings_cvm.submission import (
    AuditorAnnualBilling, AuditorAddress, AuditorHeader, AuditorIdentity, AuditorStaff,
    InformeAnualAuditor, InformeAnualAuditorDocument,
)

doc = InformeAnualAuditorDocument(
    ds_inform=AuditorHeader(ano_base=2024, dt_gerac_arq="15/04/2025", motivo_entreg=1),
    ds_audit=AuditorIdentity(
        tp_pf_pj="PJ", nr_pf_pj="11222333000181", cd_cvm=123,
        ds_nome="Auditor Exemplo", ds_email="contato@exemplo.com.br",
    ),
    lista_ender=[AuditorAddress(
        tp_ender=1, nm_lograd="Rua Exemplo", ds_bairro="Centro", cd_mun=3550308,
        nr_cep="01001000",
    )],
    qt_outra_entid_audita=0,
    fatura_anual=AuditorAnnualBilling(vl_audit="1000.50", pr_audit="80", hh_audit=900),
    ds_criter_honor="Horas trabalhadas.",
    rh=AuditorStaff(qt_socios=2, qt_func_tecno=10),
)
InformeAnualAuditor().export(doc, output_path="auditor.xml")
```
