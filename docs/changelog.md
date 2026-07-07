# **Histórico de versões**

Histórico de releases do projeto. As entradas são geradas a partir das mensagens de commit no
padrão [Conventional Commits](https://www.conventionalcommits.org/) via
[commitizen](https://commitizen-tools.github.io/commitizen/), então os cabeçalhos de versão abaixo
refletem o que realmente foi publicado.

**Como é atualizado:** as seções abaixo são geradas a partir das tags git e do histórico de commits
por `cz changelog`. A página publicada é regenerada **do zero a cada build da documentação** (o
workflow de docs roda `cz changelog` antes de `mkdocs build`), então ela sempre reflete a branch
padrão — a CI nunca faz commit de `CHANGELOG.md` de volta no repositório. Você nunca edita à mão.
Regenere ou visualize localmente quando quiser com `make changelog` (ou `bash tasks.sh changelog`).

---

<!-- Fonte única a partir do CHANGELOG.md na raiz do repositório — nunca edite as entradas aqui à mão. -->
--8<-- "CHANGELOG.md"
