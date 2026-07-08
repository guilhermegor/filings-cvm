# **Uso**

Como instalar a biblioteca e gerar o seu primeiro arquivo XML compatível com a CVM.

> **Veja também:** [Referência da API](api.md) · Envio: [Perfil Mensal](submission/perfil_mensal.md), [Informe Diário](submission/informe_diario.md)

---

## Instalação

```bash
pip install filings-cvm
```

Ou com Poetry:

```bash
poetry add filings-cvm
```

Requer **Python >= 3.10**.

---

## Conceito: modelo validado → XML

O fluxo de envio (`submission`) tem sempre a mesma forma:

1. Monte um `PerfilMensalDocument` — um cabeçalho (`DocumentHeader`) mais uma ou mais linhas
   (`PerfilMensalRow`), cada uma referente a uma classe de fundo.
2. Na construção, os modelos **validam** tudo: formato de datas (`MM/AAAA`, `DD/MM/AAAA`),
   dígitos verificadores de CNPJ/CPF, e a **escala decimal** de cada campo.
3. Serialize com `PerfilMensal().export(...)` — em memória (retorna a `str`) ou direto para um
   arquivo (codificação `windows-1252`, como a CVM exige).

Valores com mais casas decimais do que o padrão permite são **truncados em direção a zero**
(`ROUND_DOWN`), nunca arredondados — assim um valor reportado nunca é inflado.

---

## Uso básico

```python
from filings_cvm.submission import (
    ClientCount,
    DocumentHeader,
    PerfilMensal,
    PerfilMensalDocument,
    PerfilMensalRow,
)

# Cabeçalho do documento (bloco CAB_INFORM).
header = DocumentHeader(dt_compt="01/2025", dt_gerac_arq="15/01/2025")

# Contagem obrigatória de clientes por tipo de investidor (bloco NR_CLIENT).
clientes = ClientCount(
    nr_pf_priv_bank=0, nr_pf_varj=0,
    nr_pj_n_financ_priv_bank=0, nr_pj_n_financ_varj=0,
    nr_bnc_comerc=0, nr_pj_corr_dist=0, nr_pj_outr_financ=0,
    nr_inv_n_res=0, nr_ent_ab_prev_compl=0, nr_ent_fc_prev_compl=0,
    nr_reg_prev_serv_pub=0, nr_soc_seg_reseg=0,
    nr_soc_captlz_arrendm_merc=0, nr_fdos_club_inv=0,
    nr_cotst_distr_fdo=0, nr_outros_n_relac=0,
)

# Uma linha por classe de fundo (bloco ROW_PERFIL) — apenas os campos obrigatórios.
linha = PerfilMensalRow(
    cnpj_fdo="11222333000181",   # validado por dígito verificador, armazenado sem máscara
    nr_client=clientes,
    total_recurs_exter="0",
    total_recurs_br="0",
    tot_ativos_p_relac="0",
    tot_ativos_cred_priv="0",
)

doc = PerfilMensalDocument(header=header, rows=[linha])

# 1) Obter o XML como string (sem escrever em disco):
xml = PerfilMensal().export(doc)

# 2) Ou gravar direto no arquivo (retorna None):
PerfilMensal().export(doc, output_path="perfil_202501.xml")
```

Passe os valores decimais como **strings** (`"10.5"`) para preservar a precisão — nunca como
`float`.

---

## Informe Diário

O fluxo é idêntico — troque os modelos pelos do padrão Informe Diário. Cada `INFORM` identifica o
fundo por **exatamente um** de `cnpj_fdo` (classe) **ou** `cod_subclasse` (subclasse):

```python
from filings_cvm.submission import (
    InformeDiario,
    InformeDiarioDocument,
    InformeDiarioHeader,
    InformeDiarioInform,
)

doc = InformeDiarioDocument(
    header=InformeDiarioHeader(dt_compt="15/01/2025", dt_gerac_arq="15/01/2025"),
    informs=[
        InformeDiarioInform(
            cnpj_fdo="11222333000181",   # ou cod_subclasse=..., nunca os dois
            data_prox_pl="16/01/2025",
            vl_total="1000000.00",
            vl_quota="1.23456789",       # até 12 casas decimais
            patrim_liq="999999.50",
            captc_dia="0", resg_dia="0",
            vl_total_sai="0", vl_total_atv="0",
            nr_cotst=2,
        )
    ],
)

InformeDiario().export(doc, output_path="informe_20250115.xml")
```

---

## Leitura (← CVM)

O fluxo de leitura (`ingestion`) faz o caminho inverso: baixa um arquivo publicado pela CVM e o
devolve como um `DataFrame` **tipado e validado por contrato**. O primeiro leitor cobre o dump
mensal de *open-data* do Informe Diário de fundos (`inf_diario_fi_AAAAMM`):

```python
from datetime import date

from filings_cvm.ingestion import InformeDiarioReader

# Qualquer dia do mês de referência seleciona o dump mensal; o padrão é hoje.
df = InformeDiarioReader(date_ref=date(2025, 1, 15)).read()
```

O leitor baixa, descompacta e faz o parse em um diretório temporário, valida o
[contrato](api.md) (colunas obrigatórias + coluna de CNPJ coercível) e aplica os tipos
declarados. As colunas monetárias são mantidas como **texto exato** (o que a CVM publicou),
nunca `float` — converta para `Decimal` no ponto em que for calcular.

---

## Rodando os testes

```bash
make unit_tests         # apenas testes unitários
make integration_tests  # apenas testes de integração
make test_cov           # testes unitários + relatório de cobertura + badge
```

---

## Lint e formatação

```bash
make lint          # ruff check + ruff format + codespell + pydocstyle
```

---

## Publicando no PyPI

Dois workflows do GitHub Actions cuidam dos lançamentos (presentes quando o repositório tem um
remoto no GitHub):

- **`release-test-pypi.yaml`** — publica primeiro no [Test PyPI](https://test.pypi.org).
- **`release-pypi.yaml`** — publica no [PyPI](https://pypi.org) e cria um release no GitHub.

Ambos são disparados pela aba **Actions** (`workflow_dispatch`) com a versão a lançar, verificam
que a nova versão é maior que a última publicada e constroem com Poetry. Detalhes de configuração
em [Contribuindo](contributing.md).
