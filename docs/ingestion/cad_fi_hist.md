# **Histórico do Cadastro de Fundos (CAD/FI histórico) — leitura**

Leitura (← CVM) do **log de alterações** do cadastro legado de fundos (`cad_fi_hist.zip`),
publicado no [portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/FI/CAD/DADOS/).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md) · o retrato do estado
> atual em [Cadastro de Fundos (CAD/FI)](cadastro_fi.md).

---

## Descrição

`cad_fi_hist.zip` traz **19 membros**, um por atributo mutável do cadastro CAD/FI — cada um é um
**log de alterações** desse atributo. Onde o [`CadastroFiReader`](cadastro_fi.md) dá o *retrato
atual*, estes readers dão a **história**: quando cada valor valeu, e por qual janela.

Cada membro tem a mesma forma: `CNPJ_FUNDO`, `DT_REG`, a(s) coluna(s) de valor do atributo, e as
datas de vigência (`DT_INI_*`, e — na maioria — `DT_FIM_*`). Cada um tem o seu reader:

| Reader | Membro | Atributo |
|--------|--------|----------|
| `CadastroFiHistAdminReader` | `cad_fi_hist_admin` | administrador |
| `CadastroFiHistAuditorReader` | `cad_fi_hist_auditor` | auditor |
| `CadastroFiHistClasseReader` | `cad_fi_hist_classe` | classe |
| `CadastroFiHistCondomReader` | `cad_fi_hist_condom` | condomínio |
| `CadastroFiHistControladorReader` | `cad_fi_hist_controlador` | controlador |
| `CadastroFiHistCustodianteReader` | `cad_fi_hist_custodiante` | custodiante |
| `CadastroFiHistDenomComercReader` | `cad_fi_hist_denom_comerc` | denominação comercial |
| `CadastroFiHistDenomSocialReader` | `cad_fi_hist_denom_social` | denominação social |
| `CadastroFiHistDiretorRespReader` | `cad_fi_hist_diretor_resp` | diretor responsável |
| `CadastroFiHistExclusivoReader` | `cad_fi_hist_exclusivo` | exclusivo |
| `CadastroFiHistExercSocialReader` | `cad_fi_hist_exerc_social` | exercício social |
| `CadastroFiHistFicReader` | `cad_fi_hist_fic` | fundo de cotas |
| `CadastroFiHistGestorReader` | `cad_fi_hist_gestor` | gestor |
| `CadastroFiHistPublicoAlvoReader` | `cad_fi_hist_publico_alvo` | público-alvo |
| `CadastroFiHistRentabReader` | `cad_fi_hist_rentab` | rentabilidade |
| `CadastroFiHistSitReader` | `cad_fi_hist_sit` | situação |
| `CadastroFiHistTaxaAdmReader` | `cad_fi_hist_taxa_adm` | taxa de administração |
| `CadastroFiHistTaxaPerfmReader` | `cad_fi_hist_taxa_perfm` | taxa de performance |
| `CadastroFiHistTribLprazoReader` | `cad_fi_hist_trib_lprazo` | tributação de longo prazo |

Os 19 baixam o **mesmo** ZIP, então um `path_raw` gravado por qualquer um serve aos outros. Como
o CAD/FI, é um **retrato do estado atual** (URL fixa, sem partição `AAAAMM`): os readers **não**
aceitam `date_ref`, e a CVM sobrescreve o arquivo no lugar — grave `path_raw` para guardar o
retrato do dia. Um log de alterações naturalmente tem **muitas linhas por fundo**, então nenhum
reader declara granularidade única.

### Tipagem

Toda coluna é texto (`str`) exceto as `DT_*`, convertidas para `date` puro (vazios viram `NaT`).
`TAXA_ADM` / `VL_TAXA_PERFM` mantêm o texto decimal exato da CVM — **nunca `float`**.
`CPF_CNPJ_GESTOR` (no membro gestor) contém um CPF quando `PF_PJ_GESTOR == "PF"`, por isso **não**
é validado como CNPJ. O mapa de tipos é derivado do contrato, então os dois não podem divergir.

---

## Exemplos

### Reconstruir quando um fundo esteve em funcionamento

```python
from filings_cvm.ingestion import CadastroFiHistSitReader

sit = CadastroFiHistSitReader().read()
# uma linha por (fundo, período de situação); use DT_INI_SIT / DT_FIM_SIT.
janelas = sit[sit["SIT"] == "EM FUNCIONAMENTO NORMAL"]
```

### Histórico de taxa de administração de um fundo

```python
from decimal import Decimal
from filings_cvm.ingestion import CadastroFiHistTaxaAdmReader

taxa = CadastroFiHistTaxaAdmReader().read()
taxa["TAXA"] = taxa["TAXA_ADM"].dropna().map(Decimal)   # texto exato → Decimal
```

### Persistir o retrato (camada *bronze*) uma vez para os 19

```python
from datetime import date
from pathlib import Path

# Um download; o ZIP e os 19 CSVs ficam em disco para os outros readers.
CadastroFiHistSitReader(
    path_raw=Path(f"/data/bronze/cvm/cad_fi_hist/{date.today():%Y%m%d}"),
).read()
```

Cada `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou
`ValueError` (o ZIP não contém o membro esperado) — falha cedo, sem devolver dados corrompidos.
