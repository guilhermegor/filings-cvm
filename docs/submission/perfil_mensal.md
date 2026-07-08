# **Perfil Mensal — V4**

Envio (→ CVM) do padrão **Perfil Mensal V4**
([`PadraoXMLPerfilV4.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfilV4.asp)).

> **Veja também:** [Referência da API](../api.md) para cada símbolo público · [Uso](../usage.md)
> para instalação e o conceito geral.

---

## Descrição

Monte um `PerfilMensalDocument` (um `DocumentHeader` + uma ou mais `PerfilMensalRow`, cada uma
por classe de fundo) e serialize com `PerfilMensal().to_xml(...)`. A validação acontece na
construção dos modelos [Pydantic](https://docs.pydantic.dev/): formato de datas, dígitos
verificadores de CNPJ/CPF e a escala decimal de cada campo.

| Modelo | Tag XML | Papel |
|--------|---------|-------|
| `PerfilMensalDocument` | `DOC_ARQ` | Documento completo: `header` + `rows`. |
| `DocumentHeader` | `CAB_INFORM` | Cabeçalho. `dt_compt` no formato `MM/AAAA`; `dt_gerac_arq` em `DD/MM/AAAA`. |
| `PerfilMensalRow` | `ROW_PERFIL` | Uma entrada de perfil mensal por classe de fundo. |

**Campos obrigatórios de `PerfilMensalRow`:** `cnpj_fdo` (validado por dígito verificador,
armazenado sem máscara), `nr_client`, `total_recurs_exter`, `total_recurs_br`,
`tot_ativos_p_relac`, `tot_ativos_cred_priv`. Os blocos opcionais (`DISTR_PATRIM`,
`VARIACAO_PERC_VAL_COTA`, derivativos de balcão, emissores de crédito privado, taxa de
performance, etc.) e a lista completa de modelos estão na [Referência da API](../api.md).

- **Decimais** têm escala fixada por campo; a precisão excedente é **truncada em direção a zero**
  (`ROUND_DOWN`), nunca arredondada. Passe valores como `str`/`Decimal`, nunca `float`.
- Na serialização, decimais saem com **vírgula** (`10,99`); o arquivo é gravado em
  `windows-1252`.

---

## Exemplos

### Arquivo XML mínimo

O menor documento válido: um cabeçalho e uma linha com apenas os campos obrigatórios.

```python
from filings_cvm.submission import (
    ClientCount,
    DocumentHeader,
    PerfilMensal,
    PerfilMensalDocument,
    PerfilMensalRow,
)

clientes = ClientCount(
    nr_pf_priv_bank=0, nr_pf_varj=0,
    nr_pj_n_financ_priv_bank=0, nr_pj_n_financ_varj=0,
    nr_bnc_comerc=0, nr_pj_corr_dist=0, nr_pj_outr_financ=0,
    nr_inv_n_res=0, nr_ent_ab_prev_compl=0, nr_ent_fc_prev_compl=0,
    nr_reg_prev_serv_pub=0, nr_soc_seg_reseg=0,
    nr_soc_captlz_arrendm_merc=0, nr_fdos_club_inv=0,
    nr_cotst_distr_fdo=0, nr_outros_n_relac=0,
)

doc = PerfilMensalDocument(
    header=DocumentHeader(dt_compt="01/2025", dt_gerac_arq="15/01/2025"),
    rows=[
        PerfilMensalRow(
            cnpj_fdo="11222333000181",
            nr_client=clientes,
            total_recurs_exter="0", total_recurs_br="0",
            tot_ativos_p_relac="0", tot_ativos_cred_priv="0",
        )
    ],
)

print(PerfilMensal().to_xml(doc))
```

### Escrever direto em disco (codificação da CVM)

Com `output_path`, o arquivo é gravado em **`windows-1252`** e o método retorna `None`.

```python
PerfilMensal().to_xml(doc, output_path="perfil_202501.xml")
```

### Truncamento de casas decimais (nunca arredonda para cima)

`TOTAL_RECURS_BR` usa duas casas; a precisão excedente é cortada em direção a zero:

```python
# ... total_recurs_br="10.999" na linha ...
xml = PerfilMensal().to_xml(doc)
assert "<TOTAL_RECURS_BR>10,99</TOTAL_RECURS_BR>" in xml   # 10,99 — não 11,00
```

### Várias classes de fundo em um só documento

`rows` aceita uma lista — cada item vira um bloco `<ROW_PERFIL>`.

```python
doc = PerfilMensalDocument(
    header=DocumentHeader(dt_compt="01/2025", dt_gerac_arq="15/01/2025"),
    rows=[
        PerfilMensalRow(cnpj_fdo="11222333000181", nr_client=clientes,
                        total_recurs_exter="0", total_recurs_br="0",
                        tot_ativos_p_relac="0", tot_ativos_cred_priv="0"),
        PerfilMensalRow(cnpj_fdo="11444777000161", nr_client=clientes,
                        total_recurs_exter="0", total_recurs_br="0",
                        tot_ativos_p_relac="0", tot_ativos_cred_priv="0"),
    ],
)
```

### Rejeição de CNPJ inválido

Um CNPJ com dígitos verificadores incorretos levanta `ValidationError` já na construção — falhe
cedo, antes de gerar qualquer XML.

```python
from pydantic import ValidationError
from filings_cvm.submission import PerfilMensalRow

try:
    PerfilMensalRow(
        cnpj_fdo="12345678000100",   # dígitos verificadores inválidos
        nr_client=clientes,
        total_recurs_exter="0", total_recurs_br="0",
        tot_ativos_p_relac="0", tot_ativos_cred_priv="0",
    )
except ValidationError as exc:
    print("CNPJ recusado:", exc)
```
