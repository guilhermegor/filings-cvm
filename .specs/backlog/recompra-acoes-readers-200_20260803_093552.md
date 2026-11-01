# RECOMPRA_ACOES — 3 membros — **FECHA O ROOT `cia_aberta/`** — #200

Branch: `feat/200-recompra-acoes-readers` · Issue: #200 · **Inaugura o sub-root `eventos/`** e
**completa o maior root do portal** (`CAD` 1/1 + `DOC` 7/7 + `EVENTOS` 1/1).

## Feito

- [x] **Descoberta do artefato pela listagem do portal** — eu não sabia o nome do arquivo; a
      listagem de `DADOS/` deu `cia_aberta_recompra_acoes.zip`, e a de `EVENTOS/` confirmou que
      `RECOMPRA_ACOES` é o **único** dataset do sub-root.
- [x] Grounding contra os bytes reais — membros, cols **e** linhas, ragged, valores (**sobre
      distintos**, aplicando a lição do ITR) e a **META medida de 2 formas independentes**.
- [x] 3 fixtures header-only + 3 contracts **gerados dos headers**.
- [x] 3 readers sobre `_base_recompra_acoes_reader.py` (molde do CROWDFUNDING: snapshot ZIP
      multi-membro, sem `date_ref`) + `MetaRecompraAcoesReader` (46º).
- [x] Registro: **novo sub-root `eventos/`** + `cia_aberta/` + os 2 contracts; `_META_MEMBERS`.
- [x] **Contagens RE-MEDIDAS:** **283 readers** (era 279), **46 Meta = 17 `.txt` + 29 `.zip`**.
- [x] 27 testes no arquivo do RECOMPRA; suíte **2827** unit + 4 integration.
- [x] Docs: página nova + `nav`, seção em `api.md`, roster/contagens em `meta.md`, catálogo +
      layout + contagens no `CLAUDE.md`.
- [x] ⚠️ **Cabeçalho do root corrigido** — dizia que os 7 `DOC` e o `EVENTOS` estavam **pendentes**,
      o que virou falso. É o texto que uma próxima sessão lê primeiro.

## Medições

**ZIP snapshot, 0,09 MB, 3 membros, nenhum ragged**, todos ligados por `ID_Programa` (único no
registro: 1.916 distintos em 1.916 linhas; repete nos satélites).

| membro | cols | linhas | date cols | cnpj cols |
|---|---|---|---|---|
| `cia_aberta_recompra_acoes` | 11 | 1.916 | 2 | `CNPJ_Companhia` (355/355 distintos válidos) |
| `..._intermediarios` | 3 | 4.269 | **0** | `CNPJ_Intermediario` (116/116) |
| `..._quantidades` | 5 | 2.381 | **0** | **nenhuma** |

## ⚠️⚠️ Achado 1 — não segue os vizinhos do `DOC`, em 4 pontos medidos

1. **Snapshot ⇒ sem `date_ref`** (os 7 do `DOC` são `_AAAA.zip`). **Um arquivo cobre de 1997 até
   hoje**, e a CVM sobrescreve no lugar — só `path_raw` guarda o retrato do dia.
2. **Nome INVERTIDO:** `cia_aberta_recompra_acoes.zip` põe o **root primeiro**; `dfp_cia_aberta_AAAA.zip`
   põe o **dataset**. Derivar do padrão do `DOC` erraria.
3. **CamelCase** (`CNPJ_Companhia`/`Data_Deliberacao`), como o CGVN e **não** como DFP/ITR/FCA.
   DFP pinado como **contra-exemplo vivo**.
4. **2 dos 3 membros sem NENHUMA coluna de data.**

## ⚠️⚠️ Achado 2 — `quantidades` não declara CNPJ porque não tem

`tuple_cnpj_cols=()` é **decisão medida**, não esquecimento: o membro identifica só o programa.
Declarar inventaria coluna inexistente (e o contrato falharia toda leitura).

⚠️ **Vazio e esquecido são indistinguíveis num diff**, então o teste afirma os **3 membros juntos** —
o vazio **e** os dois que declaram. Controle negativo: dar CNPJ ao `quantidades` → **7 falhas**.

## Nota de método — um mutante que "passou" e não tinha mutado

A 3ª mutação (trocar `CNPJ_Companhia` por `CNPJ_CIA`) veio como **27 passed**. Não era mutante
sobrevivente: o script assertava `count(...) == 1` e o nome aparece **2 vezes** no arquivo
(`tuple_required` **e** `tuple_cnpj_cols`), então o `assert` explodiu e **nada foi escrito**.

Re-rodada com as 2 ocorrências → **3 falhas**. É exatamente a armadilha já registrada: **um controle
que passa por não ter feito nada é pior que um que falha.** O assert de contagem é o que a expôs —
sem ele, teria virado "a suíte não pega a convenção do DOC".

## Controles negativos (3, todos vermelhos)

Baseline **27 passed**, restore por cópia de snapshot.

- [x] `quantidades` ganha coluna de CNPJ → **7 falhas**.
- [x] Registro lendo o membro do satélite → **6 falhas** (a defesa de identidade do membro,
      nascida no DFP, já vem de série).
- [x] Adotar a convenção do `DOC` (`CNPJ_CIA`) → **3 falhas** (ver nota de método).

## Aberto / próximo

- [ ] **Release PATCH** ao mergear (`feat`, `src/` muda).
- [ ] 🎉 **O root `cia_aberta/` está COMPLETO.** Próximo alvo sai do inventário do **#122** /
      survey do **#41** — decidir com o user qual root atacar.
- [ ] #192 (testes dos 3 `bin/check_*` sem cobertura) segue em Ready.
