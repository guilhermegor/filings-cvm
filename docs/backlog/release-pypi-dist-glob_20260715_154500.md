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
