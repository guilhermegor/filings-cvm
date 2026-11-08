## genbadge-local_20261030_120000

# genbadge --local (#86)

- [x] Confirm every `genbadge coverage` call on origin/main lacks `--local`
- [x] Add `--local` in tests.yaml, .pre-commit-config.yaml, Makefile, tasks.sh
- [x] Generate a badge locally and check it is valid SVG
- [ ] Merge the PR

No `src/` change, so no package release.

## release-pypi-dist-glob_20260715_154500

# Work ledger — #102 `release-pypi` sobe `dist/.keep` → release fica DRAFT sem tag

Branch `fix/release-pypi-dist-glob-102`. Fecha **#102**. **Sem release** (`ci`, zero diff em `src/`).

## O bug (aconteceu de verdade no 0.25.4)

`release-pypi.yaml:226` subia **`files: dist/*`**. Esse glob pega o **`dist/.keep`** — placeholder de
**0 byte**, trackeado de propósito (`.gitignore`: `dist/*` + `!dist/.keep`) para o diretório existir no
git. **A API do GitHub rejeita asset de 0 byte** (`size must be greater than or equal to 1`).

**Não é bug do `@v3`.** É bug latente que o `@v3` **armou**: o `@v1` ignorava o arquivo (o release
0.25.3 saiu com só os 2 assets, `draft=false`); o `@v3` (que veio no #79) falha duro.

| | v0.25.3 (`@v1`) | v0.25.4 (`@v3`) |
|---|---|---|
| assets | `.whl` + `.tar.gz` | tentou subir o `.keep` |
| resultado | `draft=false`, tag criada ✅ | **job falhou** ❌ |

## Por que é pior que um X vermelho

O `@v3` cria o release como **draft**, sobe os assets e **só então promove**. Abortou no `.keep` →
ficou `draft=true` → **o GitHub não cria tag de draft**. Estado do 0.25.4: **publicado no PyPI ✅, sem
tag `v0.25.4`** até eu promover à mão (`gh release edit v0.25.4 --draft=false`, que promove **e** cria
a tag).

Sem a tag: o `poetry-dynamic-versioning` **deriva a versão da tag** (para de carimbar) e o release gate
(`git diff v<LAST>..HEAD -- src/`) passa a comparar contra a tag errada. E note a forma:
**`pypi: success` com o release quebrado** — mesma família do #86: **run verde ≠ artefato publicado**.

## Feito

- [x] **`files: dist/*` → `dist/*.whl` + `dist/*.tar.gz`** (`release-pypi.yaml`), com comentário no
  arquivo explicando a restrição para ninguém restaurar o glob "conveniente".
- [x] **Varrido o repo**: era a **única** ocorrência. Os outros `dist/` são `path:` de
  `upload-artifact`/`download-artifact` — ali o `.keep` é inofensivo (os jobs passaram).
- [x] **`dist/.keep` mantido** — é deliberado (`.gitignore` `dist/*` + `!dist/.keep`); o bug era o
  glob, não o placeholder. Apagá-lo trataria o sintoma e voltaria a quebrar no próximo arquivo que
  aparecesse na pasta.
- [x] `.github/CLAUDE.md`: nova secção **"The staging rehearsal only rehearses the steps it SHARES"**
  + **"Never glob a build directory into release assets"**.

## Verificação

- [x] **Simulado o globber REAL da action** (dotfiles incluídos — provado pelo log do CI:
  `⬆️ Uploading .keep...`). ⚠️ O `glob` do Python **esconde** dotfiles, então a 1ª tentativa de teste
  deu falso-negativo e a asserção pegou: **o teste estava errado, não o fix**. Refeito com
  `os.listdir` + `fnmatch`:
  - `dist/*` → `['.keep', '*.whl', '*.tar.gz']` → **0-byte: `['.keep']`** (o que quebrou o 0.25.4);
  - `dist/*.whl` + `dist/*.tar.gz` → só os 2 artefatos → **0-byte: nenhum**.
- [x] Asserção contra o **workflow no disco**, não contra a intenção: `files:` declara exatamente
  `['dist/*.whl', 'dist/*.tar.gz']` e **não resta nenhum `dist/*` cru**.
- [ ] `yamllint` + ruff/format + suíte (nada de Python mudou, mas a paridade de gate manda rodar).
- ⚠️ **Não dá para testar de verdade sem um release**: `release-pypi.yaml` é `workflow_dispatch` e o
  step só existe nele — é **exatamente** o buraco de ensaio que esta PR documenta. A prova real vem
  no **próximo release (CRI/0.25.5)**: o job `Create GitHub Release` tem de ficar **verde** e a tag
  `v0.25.5` tem de nascer **sozinha**, sem `--draft=false` na mão.

## Aberto / próximo

- [ ] PR (`Closes #102`) → aprovação → merge. **Sem release.**
- [ ] **Confirmar no próximo release** que a tag nasce sozinha (é o único teste verdadeiro).
- [x] Lição BlueprintX capturada: `a-rehearsal-only-rehearses-the-steps-it-shares.md` (store global +
  mirror). O scaffold embarca **os dois** lados do bug (o `dist/.keep` **e** o glob), então todo repo
  gerado dele carrega a mina — armada no dia em que chegar no `gh-release@v3`.

## release-python-pin_20261029_143500

# Release workflows: unpin the Python patch (#267)

`ubuntu-latest` is now Ubuntu 26.04, where `actions/setup-python` has no
3.12.8, so both release workflows fail at Set Up Python.

- [x] Change `python-version` from `"3.12.8"` to `"3.12"` in
      `release-test-pypi.yaml` and `release-pypi.yaml`
- [x] Grep every workflow for other exact-patch Python pins (none found)
- [x] Validate with the actionlint and yamllint hooks
- [x] Completed — kept as a record.

Note: the venv cache key embeds `matrix.python-version`, so it moves from
`...-3.12.8-...` to `...-3.12-...`. One-time cache miss; key left untouched.

## venv-cache-lock-key-195_20261029_120000

# Work ledger — #195 cache do venv deixava o `tests.yaml` pular a instalação

Branch `ci/195-venv-cache-lock-key`. Fecha **#195**. Sem release (`ci`, zero diff em `src/`).

## Feito

- [x] Chave do cache passa a hashear o lockfile: `hashFiles('poetry.lock', 'pyproject.toml')`.
  Uma mudança só-de-lock (o diff do `lockfile-only` do Dependabot) agora erra o cache e instala.
- [x] `poetry.lock` removido do `path:` do cache (fica só `.venv`): o restore não sobrescreve mais o
  lockfile versionado.
- [x] `poetry check --lock` promovido a step próprio e incondicional (`Check Lock File Is In Sync`),
  antes do restore do cache e antes da reescrita do `pyproject.toml`.
- [x] `actionlint` (com `SHELLCHECK_OPTS=--severity=warning`, como `bin/lint_actions.sh`) e
  `yamllint` limpos.

## Fora de escopo (follow-up)

- [ ] `release-pypi.yaml` e `release-test-pypi.yaml` têm o mesmo padrão de cache; a issue limita o
  conserto ao `tests.yaml`.

- [x] Completed — kept as a record.

## venv-cache-python-patch_20261031_060000

# Key the venv cache on the resolved Python patch

- [x] Reproduced: Windows jobs on #276, #280 and #283 failed with "did not find executable" after the runner moved from 3.13.16 to 3.13.17
- [x] `tests.yaml`, `release-pypi.yaml` and `release-test-pypi.yaml` key on the `setup-python` output

Completed — kept as a record.
