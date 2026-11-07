## ban-binary-float-dtypes-157_20260724_230214

# Work ledger — #157 banir float binário em valores ingeridos + gate `check_dtypes`

Branch `fix/157-banir-float-binario-gate-check-dtypes`. Fecha **#157**. **Com release** (`fix`, há
diff em `src/`) → PATCH.

## O que a issue pedia, e o que o grounding mudou

A issue afirmava que o boundary JSON era **inexistente** ("blindagem para a primeira fonte JSON").
**Não é.** `_read_raw` já tinha um ramo `.json` vivo:

```python
df_json = pd.read_json(path_file)
return df_json.astype(str_dtype) if str_dtype is not None else df_json
```

Como `read_table` sempre passa `str_dtype="str"`, CSV e Excel são de fato **text-first** e estavam
seguros. O ramo JSON **não estava**: o parser do pandas infere um tipo por coluna **antes** de
qualquer dtype declarado, e o `astype("str")` seguinte apenas **preserva fielmente o estrago**.

Ou seja: era um caminho **lossy de verdade**, não uma hipótese. Corrigido de raiz, não blindado.

## O bug era maior que float

O controle negativo (reverter o fix e exigir que os testes novos falhem) revelou que o
`pd.read_json` corrompia **duas** coisas, não uma:

| entrada JSON | `pd.read_json` (antes) | `json.loads(parse_float=Decimal)` (agora) |
|---|---|---|
| `"code": "007"` | `7` → `"7"` | `"007"` |
| `"amount": 1984223115.42` | float → `"1984223115.4200001"` | `"1984223115.42"` |

O zero-padding é **exatamente** o exemplo que o docstring do próprio módulo usa para explicar por que
o seam nunca confia na inferência do pandas (`"007" vira 7, irrecuperável por um astype posterior`).
O ramo JSON violava o contrato declarado do próprio arquivo.

## O gate se pagou na primeira execução (2ª vez na família `filings-*`)

Rodado contra o `main`, o `bin/check_dtypes.py` acusou **1 violação** — o docstring do próprio
`apply_dtypes`:

```
src/filings_cvm/_internal/utils/dtypes.py:59: ``"int64"``, ``"float64"``). A ``"str"`` declaration…
```

É o **pior lugar possível**, e o mesmo achado do `filings-b3` (lá foi o exemplo de docstring de uma
classe base): todo reader novo nasce copiando um existente, então um exemplo errado no seam
compartilhado ensina o padrão errado para o portal inteiro. Removido.

## Feito

- [x] **`_to_decimal`** (`_internal/utils/dtypes.py`) — texto/`int`/`Decimal` entram; **`float` é
  RECUSADO, não convertido** (converter lavaria um valor já perdido num tipo que anuncia exatidão).
  `NaN` é reconhecido como **ausente antes** da recusa (NaN é float e é o marcador de ausente do
  pandas) — senão toda célula vazia levantaria.
- [x] **`list_decimal_cols`** em `apply_dtypes`, entrando na validação de disjunção (agora **4**
  conjuntos, não 3) e na checagem de colunas ausentes.
- [x] **Propagado** por `read_table`, `read_query` e `_finalize` — arquivo e DB não podem divergir.
- [x] **Boundary JSON corrigido de raiz**: `json.loads(..., parse_float=Decimal)` + `pd.DataFrame`,
  no lugar de `pd.read_json`. Encoding passa a honrar `str_encoding` (BOM), documentado.
- [x] **`bin/check_dtypes.py`** — gate textual no padrão de `check_typing.py`/`check_provenance.py`.
  Ruff **não** dá conta: `banned-api` casa import e acesso a atributo, não um literal `"float64"`
  dentro de um dict. Escape hatch `# dtype-ok: <razão>` com motivo obrigatório.
- [x] **Gate parity**: registrado em `.pre-commit-config.yaml` (`check-dtypes`) **E** em
  `.github/workflows/tests.yaml` (step `Run Binary-Float Dtype Ban`) — hook sozinho é burlado por
  `--no-verify`, e a branch protection roda o *workflow*.
- [x] Docstrings do módulo/`apply_dtypes`/`read_table`/`read_query` apontam `list_decimal_cols` e o
  gate; o exemplo `"float64"` saiu.

## Verificação

- [x] **Gate por MUTAÇÃO, não só caminho feliz** (critério de aceite explícito da issue):
  - contra o `main` → **1 violação** (o docstring), provando que não é gate vazio;
  - float deliberado em `src/` → **EXIT=1**;
  - a mesma linha com `# dtype-ok: <razão>` → **EXIT=0**;
  - `src/` como entregue → **EXIT=0**.
- [x] **Controle negativo dos testes de JSON**: revertido o ramo para `pd.read_json`, **os 2 testes
  novos falham**; restaurado, passam. Não são tautologia.
- [x] ⚠️ **Um teste meu passou no código quebrado e foi corrigido**: `Decimal("10.5") ==
  Decimal("10.50")` é **`True`** — a igualdade de `Decimal` compara valor numérico e **ignora a
  escala**. Asserção de escala trocada para `str(...)`. É a mesma armadilha do `pytest.approx`, um
  nível abaixo: a igualdade exata não bastava, precisava ser exata **na representação**.
- [x] Igualdade **exata** nos testes de decimal (`==` contra `Decimal("…")`, nunca `pytest.approx`),
  incluindo a asserção de que `value != Decimal(1984223115.42)` — o round-trip binário que o seam
  existe para excluir.
- [x] `ruff check` + `ruff format --check` limpos; `mypy` **347** arquivos OK; `check_typing`,
  `check_provenance`, `check_dtypes` OK; **1850 unit** (era 1828, +22).
- [x] ⚠️ **`ruff format bin/` reformatou 4 scripts pré-existentes** (`check_docstrings`,
  `check_backlog_ledger`, `check_typing`, `check_provenance` — ~1560 linhas de churn). É a **dívida
  conhecida de `bin/`** registrada no checkpoint, **não** desta issue → revertidos, commit atômico.
  Segue valendo um PR de chore separado.
- [x] 2 falsos-positivos de lint resolvidos **sem suprimir**: `S105` (o nome `_ALLOW_TOKEN` lido como
  credencial → renomeado `_ALLOW_MARKER`) e `ERA001` (`"reader: it infers…"` lido como anotação de
  variável → comentário reescrito).

## Aberto / próximo

- [ ] PR (`Closes #157`) → aprovação → merge → **release PATCH**.
- [ ] Nenhum reader usa `list_decimal_cols` hoje — a convenção do repo é devolver monetários como
  **texto decimal exato** (`str`), e isso continua correto e lossless. O novo seam é para quando um
  reader precisar do `Decimal` tipado, e o gate é o que impede o atalho `float64` nesse dia.
- [ ] Retomar a sweep do #41 (Wave 4): os 7 datasets `CIA_ABERTA/DOC` + `EVENTOS`, um PR por dataset
  — agora protegidos pelo gate.

## cnpj-empty-partition-317_20261031_120000

# Work ledger — #317 CNPJ check on empty partitions

Branch `fix/317-cnpj-empty-partition`. Closes **#317**. Release: `fix` touching `src/` → PATCH.

## Done

- [x] Reproduced on `origin/main` (`8171df8`): a header-only `DFP_CIA_ABERTA_DFC_MD_CON` frame
  returned `["Column 'CNPJ_CIA' ... holds no valid CNPJ (unexpected data type)"]`.
- [x] Regression tests first (`tests/unit/test_tabular_reader.py`): 7 of 8 red before the fix
  (header-only DFP/ITR `DFC_MD_con`/`_ind`; all-NaN/blank/whitespace column). The guard
  "non-empty values with no valid CNPJ still fail" was green before and after.
- [x] `find_contract_problems` drops NaN and blank cells before the CNPJ check; nothing present
  → pass. No existing test expectation changed (IPE "only placeholders raises" still holds).
- [x] Live check against CVM: DFP `DFC_MD_con`/`_ind` 2026 read as 0 rows, no error; ITR
  `DFC_MD_con`/`_ind` 2026 have rows (810/948) and read fine.

## ⚠️ Finding — Complemento FI is NOT an empty-column case

`ComplFiReader` at 2019-04 still raises, and correctly under the rule this issue keeps:
`CNPJ_AG_RISCO` is **not empty** there — 199 × `00.000.000/0000-00` + 1 × `11.111.111/1111-11`.
Measured over the whole series (201801–201904): the column holds sentinels
(`00.000.000/0000-00`, `99.999.999/0001-99`, `11.111.111/1111-11`) and has **one** valid CNPJ in
16 months (201808). So `ComplFiReader` raises on 15 of 16 partitions on `main`, and the
`compl_fi.py` docstring ("well-formed otherwise") is wrong.

- [x] Coordinator extended the surface and decided to fix it here: `CNPJ_AG_RISCO` dropped
  from `COMPL_FI.tuple_cnpj_cols`, docstring and `docs/ingestion/compl_fi.md` corrected,
  `test_compl_fi_ingestion.py` expectation changed (data disproves it) plus a placeholder-only
  test (red under the old contract). Live: `ComplFiReader` 2019-04 reads 200 rows.

Completed — kept as a record.

## header-only-cnpj-320_20261031_141809

# Validate CNPJ on the header-only CRI/FCA members (#320)

- [x] Confirmed #317 (PR #319) on origin/main: `check_cnpj` skips a column with no non-empty values
- [x] Grounded each column against the pinned header fixture and the dataset META (`varchar(18)`, only CNPJ/CPF column)
- [x] CRI `carteira_modificacao` and `responsavel` declare `CNPJ_Emissora`
- [x] FCA `departamento_acionistas` declares `CNPJ_Companhia`
- [x] Tests per member: header-only reads, valid CNPJ passes, no valid CNPJ raises
- [x] Docs and CLAUDE.md lines describing the old `()` workaround updated

Completed — kept as a record.

## portal-root-public-surface-91_20260801_170000

# Portal-root packages são a superfície pública (slim top-level `__all__`) — #91

Branch: `refactor/91-portal-root-packages-public-surface` · Issue: #91 · **BREAKING → 0.26.0**

## Decisão reconfirmada com o user (2026-08-01)

A issue registrava a versão **dura** e pedia para reconfirmar no início do PR. Perguntei; o user
escolheu a **dura**: os leitores saem de vez do topo, `from filings_cvm import XReader` levanta
`ImportError`.

⚠️ **O user acrescentou uma regra que a issue NÃO tinha:** *"submission should be imported from the
submission folder, not from filings_cvm"*. A issue previa manter os 4 nomes de submission no topo.
Com isso a regra ficou **simétrica** e muito mais fácil de enunciar: **cada seção é dona dos seus
nomes**, e o topo guarda só o que não pertence a nenhuma (`RetryPolicy`, `__version__`).

| o que | importa de |
|---|---|
| leitor | `filings_cvm.ingestion.<portal_root>` (22 roots) |
| serializador | `filings_cvm.submission` |
| `RetryPolicy` | `filings_cvm` |

## Feito

- [x] **Provei a precondição ANTES de apagar:** os 216 leitores do `__all__` plano são exatamente
      os 216 alcançáveis pelos 22 roots — bijeção, zero órfão, zero nome em 2 roots.
- [x] `filings_cvm/__init__.py` → só `RetryPolicy` + `__version__` (de 222 nomes para 2).
- [x] `filings_cvm/ingestion/__init__.py` → exporta os **22 root packages**, não os leitores.
- [x] Migração mecânica dos imports por script (ast para `.py`, linha a linha para `.md`):
      **23 arquivos de teste + 43 de docs/README**.
- [x] `_internal/utils/introspection.py` — `iter_public_readers()` / `iter_root_packages()`.
- [x] 4 seams de descoberta religados a ele (3 testes + `bin/check_contract_drift.py`).
- [x] `tests/unit/test_public_surface.py` — 17 testes, pinando nas **2 direções**.
- [x] Docs: `api.md`, `ingestion/index.md`, `CLAUDE.md` (Layout + Public vs private), README.
- [x] Gates: ruff, mypy **398**, 4 check_*, **2199 unit** (+17), 4 integration, codespell,
      mkdocs --strict.

## ⚠️ O erro que quase passou: a cobertura caiu 40% e a suíte continuou verde

Depois de remover o `__all__` plano, a suíte passou de **2182** para **1311** testes — **sem uma
única falha nova de coleção**. Causa: 4 gates descobriam os leitores varrendo o `__all__` plano
(`test_reader_retry_policy`, `test_meta_readers` ×3 sites, `test_check_contract_drift`,
`bin/check_contract_drift.py`). Com o namespace vazio, a varredura devolvia **zero** e os testes
parametrizados **colapsaram para nenhum caso** — verde, inerte e silencioso.

**Só foi visto porque conferi a CONTAGEM, não o resultado.** É exatamente a lição
`docs-that-enumerate-code-need-a-gate` ("um gate que pode casar zero em silêncio é pior que gate
nenhum") aparecendo do lado do *código*. Por isso `iter_public_readers()` **levanta** em vez de
devolver vazio, e `test_reader_retry_policy` agora afirma `len(roots) == 22` e `len(readers) > 200`.

## Controles negativos (2 mutações, ambas vermelhas antes do fix)

- [x] **Deixar 1 leitor reexportado no topo** (refactor pela metade) → falham 2 testes, nas 2
      direções. Sem isso, um leitor esquecido no topo não quebraria nada.
- [x] **Tirar 1 root do `ingestion.__all__`** → falham 3 testes, incluindo o guard de contagem do
      retry-policy. É a mutação que reproduz o colapso silencioso acima.

## Aberto / próximo

- [x] **Release 0.26.0** (MINOR em 0.x = breaking) com a nota de migração — publicado, tag
      `v0.26.0`, install-verified nos 2 índices. O `BREAKING CHANGE:` no corpo do commit é o que o
      `cz changelog` publica.
- [x] Fatia **3/4** (diversidade, 11 membros) — #183 / PR #184, saiu na 0.26.2.
- [ ] Fatia **4/4** (remuneração + val. mobiliários + transações, 10 membros) — **fecha o FRE**.
- [x] ⚠️ **CORREÇÃO (fatia 3, #183): o bônus NÃO é "2 `__init__`".** Este ledger dizia que um leitor
      novo passa a tocar **2** (dataset + root) — **errado para um root aninhado**. `cia_aberta` tem
      uma camada `doc/`, então a cadeia é `doc/fre/` → `doc/` → `cia_aberta/` = **3**. A regra certa
      é **contar os pacotes no caminho até o root**, não presumir 2 (o `ImportError` apareceu na hora
      na fatia 3). ⚠️ E **o contract também entra em `contracts/__init__.py`** — esquecer isso **não
      quebra nada** (o reader importa o contract do módulo direto), só a **contagem exportada**
      denuncia. Ambas as regras já corrigidas no `CLAUDE.md`; esta linha fica como registro de que a
      afirmação original estava errada. O bônus real segue valendo: **não são mais 4**.

## Fora de escopo (dívida pré-existente, deliberadamente não tocada)

4 scripts em `bin/` (`check_backlog_ledger`, `check_docstrings`, `check_provenance`,
`check_typing`) seguem fora do formato do ruff. É dívida conhecida e **não é deste PR** — formatar
a pasta inteira inflaria o diff com ~1560 linhas alheias. Só o arquivo tocado foi formatado.

## refactor-nest-ingestion_20260710_233000

# Work ledger — nest the ingestion/ folder by CVM portal path (#44)

Branch `refactor/nest-ingestion-by-portal-path` · issue **#44**.

## Why

`ingestion/` had grown to 27 reader modules + 1 base flat (19 were the `cad_fi_hist_*` family).
User chose **option A (by CVM portal path) + per-dataset sub-folders** for multi-file datasets.

## Target tree (built)

The portal path is `dados.cvm.gov.br/dados/<ROOT>/…` where `FI/` is **one root among
siblings** (`FIDC/`, `FII/`, `AUDITOR/`, `INVNR/`, … — all pending in the catalog). So the
nesting carries the `fi/` root level; `doc/`/`cad/` are `FI/DOC` and `FI/CAD` beneath it, and
future roots become siblings of `fi/`, not name-collisions with it.

```
ingestion/
  __init__.py                 # FLAT public API — re-exports every reader (unchanged import path)
  fi/                         # FI/ — Fundos de Investimento (one portal root)
    __init__.py               #   aggregates all 28 FI readers
    doc/                      #   FI/DOC/*
      informe_diario.py
      cda.py
      lamina/                 #   FI/DOC/LAMINA (one ZIP, two members)
        lamina.py
        lamina_carteira.py
    cad/                      #   FI/CAD
      cadastro_fi.py          #   cad_fi.csv
      registro/               #   registro_fundo_classe.zip (3 members)
        registro_fundo.py  registro_classe.py  registro_subclasse.py
      cad_fi_hist/            #   cad_fi_hist.zip (19 members)
        _base_cad_fi_hist_reader.py
        cad_fi_hist_*.py  (19)
```

## Key property — public API unchanged

`from filings_cvm.ingestion import XReader` still works for all 28 readers. Each sub-package's
`__init__` re-exports its readers; `ingestion/__init__` imports from the sub-packages. Verified:
`filings_cvm.__all__` still 32 symbols. A **pure internal move** (like the PR #39 ports/schemas
reorg) — zero public API change.

## Execution

- [x] `git mv` 28 files into the tree (clean renames).
- [x] 5 new sub-package `__init__.py` (doc/, doc/lamina/, cad/, cad/registro/, cad/cad_fi_hist/),
  each re-exporting its readers.
- [x] Rewrote the 19 readers' base import to `…cad.cad_fi_hist._base_cad_fi_hist_reader` (+ the
  docstring `:mod:` refs, shortened to `` ``_base_cad_fi_hist_reader`` `` to stay under 99 cols).
- [x] Rewrote `ingestion/__init__` to import from the sub-packages.
- [x] Rewrote test internal module paths (monkeypatch targets + private imports) with anchored
  seds (name + delimiter, so substrings can't collide), verified by the suite.
- [x] Root `CLAUDE.md` catalog source paths + Layout tree updated to the nested structure.
- [x] **Review feedback (portal has many roots besides FI):** added the `fi/` root level above
  `doc/`/`cad/` so `doc/`/`cad/` are `FI/DOC`/`FI/CAD` and future roots (`FIDC/`, `AUDITOR/`, …)
  are siblings of `fi/`. New `fi/__init__.py` aggregates all 28; `ingestion/__init__` re-exports
  from `.fi`. Second commit on the same branch.

## Verification

- [x] 213 unit tests green under **pandas 3.0.3 and 2.3.3**.
- [x] ruff check + format, `bin/check_typing.py`, `bin/check_provenance.py`, `mypy` (70 files),
  `check_docstrings.py`, `mkdocs build --strict` — all clean.

## Open / follow-up

- [ ] PR opened; awaiting user review/merge + release.
- [ ] **Mirror the test-folder hierarchy** (`tests/unit/doc/…`, `tests/unit/cad/…`) to match the
  package structure, per the CLAUDE.md convention. Deferred: tests are already one-per-reader and
  clearly named; moving them is churn without functional value. Do it as a small follow-up if the
  mirror convention is to be enforced strictly.

## refactor-per-module-retry-policy_20260711_083904

# Work ledger — per-module `_RETRY_POLICY` as the project standard (issue #53)

Branch: `refactor/53-per-module-retry-policy`. Generalizes the pattern proven by the FIDC
readers (#52 / PR #54) to **every** ingestion reader.

## Done

- [x] Retrofitted the **9 constructor-bearing** reader modules with the pattern (module
      `_DEFAULT_RETRY_POLICY` literal → `_RETRY_POLICY` ClassVar → ctor fallback):
      `informe_diario`, `cda`, `lamina`, `lamina_carteira`, `cadastro_fi`,
      `registro_{fundo,classe,subclasse}`, and `_base_cad_fi_hist_reader` (which covers its 19
      change-log subclasses). FIDC's 17 already had it.
- [x] **Per-family literal** chosen over one shared library-wide constant (user decision): each
      family declares its own `_DEFAULT_RETRY_POLICY`, mirroring FIDC exactly. Keeps the patience
      co-located with the dataset; no change to FIDC or to `http_downloader`'s own fallback.
- [x] Ctor docstrings updated — the old "by default the seam's throttle-tolerant policy" wording
      was inaccurate once the reader owns the default.
- [x] **Structural test** `tests/unit/test_reader_retry_policy.py` — cross-cutting and
      **introspective**: it discovers readers from `ingestion.__all__` rather than listing them, so
      a *future* reader that forgets `_RETRY_POLICY` fails automatically. Asserts, per reader:
      declares a `RetryPolicy`, exposes `retry_policy`, defaults to the module policy, and lets a
      per-instance policy override. 177 tests over all 44 readers.
- [x] Docs: fixed the **`api.md` signature drift** (7 reader ctors omitted `retry_policy`) and added
      a `retry_policy` row to each param table; documented the standard in `ingestion/index.md`
      (new "Política de retry" section beside provenance / `path_raw`).
- [x] Gates: ruff, ruff format, `check_typing`, `check_provenance`, mypy (97 files),
      `pytest tests/unit` (**482 passed**), `mkdocs build --strict` — all green (pandas 3.0.3;
      pandas 2.x via CI matrix).
- [x] Ticked the #52 ledger's remaining boxes (PR #54 merged, 0.13.0 released) — carried here.

## Open / next

- [ ] User review of the PR (approval gate — do not start the next task until merged).
- [ ] After merge: release (minor bump → 0.14.0) Test PyPI → verify by install → PyPI → verify.
- [ ] Then resume Wave 1 of the #41 sweep: FII → FIP → FIAGRO → FIE, then Waves 2–5.

## Notes

- The introspective test is the thing that makes this a *standard* rather than a convention nine
  files happen to follow — it is the structural guard, analogous to `bin/check_provenance.py`.
- Related but separate: the pending dotfiles-dev lesson `autowrap-commit-body-pretooluse-hook.md`
  (auto-wrap commit bodies ≤72 before gitlint) — toolchain, not this repo.
