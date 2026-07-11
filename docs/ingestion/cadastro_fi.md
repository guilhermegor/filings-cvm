# **Cadastro de Fundos (CAD/FI) — leitura**

Leitura (← CVM) do **cadastro de fundos de investimento** (`cad_fi.csv`), publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/FI/CAD/DADOS/).

> **Veja também:** [Referência da API](../api.md) para cada símbolo público · [Uso](../usage.md)
> para instalação e o conceito geral.

---

## Descrição

`CadastroFiReader` baixa o CSV, valida o **contrato** (as 41 colunas obrigatórias + `CNPJ_FUNDO`
coercível), aplica os **tipos declarados** — nunca a inferência do pandas — e devolve o registro de
todo fundo que a CVM já registrou, com administrador, gestor, auditor, custodiante e situação.

### Sem mês de referência

Diferente de todos os outros leitores desta biblioteca, o CAD/FI é um **retrato do estado atual**,
não um dump mensal: um `.csv` puro, numa URL fixa, sem partição `AAAAMM`. Por isso o construtor
**não aceita `date_ref`** — não há mês a selecionar, e aceitá-lo sugeriria um histórico que o
artefato não carrega.

> **Guarde o `path_raw` a cada execução.** A CVM **sobrescreve** o arquivo no lugar. Um retrato
> gravado em disco é o **único** registro do que o cadastro dizia naquele dia — ele não pode ser
> baixado de novo.

Dois artefatos irmãos carregam histórico e estão **fora do escopo** deste leitor (cada um merece o
seu): `cad_fi_hist.zip` (o log de alterações) e `registro_fundo_classe.zip` (o cadastro de
fundos/classes/subclasses pós-Resolução CVM 175).

### Não há chave única — não use como tabela de consulta

`CNPJ_FUNDO` **não é único**: 10.947 das 46.809 linhas dividem o CNPJ com outra linha. Um fundo
**mantém o seu CNPJ** ao migrar de regime regulatório e é re-registrado com novo `TP_FUNDO` e novo
`CD_CVM`. Então um mesmo CNPJ aparece, por exemplo, como um `FIF` cancelado e um `FI` posterior.
Nem `CD_CVM` sozinho, nem `(CNPJ_FUNDO, TP_FUNDO, DT_REG)` são únicos.

O leitor **não declara granularidade** e **não deduplica**: escolher a linha "atual" de cada CNPJ
(maior `DT_REG`? `SIT != "CANCELADA"`?) é uma decisão de domínio do consumidor, não de um leitor
cuja função é devolver o que a CVM publicou. Um `set_index("CNPJ_FUNDO")` ou um `merge` só por essa
coluna **multiplica linhas silenciosamente**.

A maioria das linhas é histórica: `SIT` é `CANCELADA` em 46.569 delas. **Filtre por `SIT`** antes de
tratar isto como uma lista de fundos vivos.

| Coluna | Tipo | Observação |
|--------|------|-----------|
| As nove `DT_*` | `date` | `DT_REG`, `DT_CONST`, `DT_CANCEL`, `DT_INI_SIT`, `DT_INI_ATIV`, `DT_INI_EXERC`, `DT_FIM_EXERC`, `DT_INI_CLASSE`, `DT_PATRIM_LIQ`. Vazios viram `NaT`. |
| `CNPJ_FUNDO` | `str` | Mascarado na origem. **Não é único.** |
| `CPF_CNPJ_GESTOR` | `str` | Contém um **CPF** quando `PF_PJ_GESTOR == "PF"` (47 linhas), por isso **não** é validado como CNPJ. |
| Todas as demais (32) | `str` | Texto exato da CVM — **nunca `float`**. Inclui `VL_PATRIM_LIQ`, `TAXA_ADM`, `TAXA_PERFM`. |

O mapa de tipos é **derivado do contrato**, não redigitado, de modo que os dois não podem divergir.

---

## Exemplos

### Ler o cadastro

```python
from filings_cvm.ingestion import CadastroFiReader

df_ = CadastroFiReader().read()   # sem date_ref: é um retrato do estado atual
print(df_.shape)                  # (46809, 41)
```

### Obter apenas os fundos em funcionamento

```python
ativos = df_[df_["SIT"] == "EM FUNCIONAMENTO NORMAL"]
```

### Escolher a linha mais recente de cada CNPJ

Como o CNPJ se repete entre regimes, **você** decide o critério:

```python
atual = df_.sort_values("DT_REG").groupby("CNPJ_FUNDO", as_index=False).last()
```

### Persistir o retrato (camada *bronze*)

```python
from datetime import date
from pathlib import Path

df_ = CadastroFiReader(
    path_raw=Path(f"/data/bronze/cvm/cad_fi/{date.today():%Y%m%d}"),
).read()
```

### Timeout

O padrão é `60 s` — maior que o dos leitores mensais, porque o retrato tem ~18 MB e não é zipado.

```python
df_ = CadastroFiReader().read(int_timeout_s=120)
```

O `read` levanta `OSError` (falha de download) ou `ContractError` (CSV viola o contrato) — falha
cedo, sem devolver dados corrompidos.
