# docs: adopt the BlueprintX docs layout (#371)

- [x] `docs/api.md` -> `docs/api/reference.md` (+ new `docs/api/index.md`); every `api.md` link fixed
- [x] `docs/examples.md`, `docs/stylesheets/brand.css` (`extra_css`), `docs/assets/logo.png`
- [x] `mkdocs.yml`: tabs/sections, Guia / Referência da API / Projeto, `mike` kept
- [x] `bin/check_docs_sections.py` canonical pages + `docs/.docs-skeleton.yaml` + sync test
- [x] `docs/CLAUDE.md` and `docs/contributing.md` describe the directory layout
- [ ] `incidents.md` nav entry and `architecture.md` skeleton page: not added (files do not exist; #350)

Later writer/reader PRs must add their API entry to `docs/api/reference.md`, not `docs/api.md`.
