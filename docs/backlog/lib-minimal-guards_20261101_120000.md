# Work ledger: BlueprintX lib-minimal guards (#367)

- [x] Layer-import policy: `.layer-policy.yaml`, `bin/check_layer_imports.py`, hook + CI step, gate test
- [x] Route the two direct pandas calls in `ingestion/` through the new `utils/frames.py` seam
- [x] Dynamic-version stub gate: script, hook, CI step, test
- [x] Description sync gate: script + `lib/description_sources.py`, hook, CI step; `pyproject.toml` description aligned to `mkdocs.yml`
- [x] `bin/pin_contract_oracle.py` (ISO-8859-1 default) + test against the real `eventual_fi` header fixture
- [x] `[tool.commitizen]` moved to `.cz.toml` (`tag_format = "v$version"`)
- [x] `.vscode/extensions.json`, `tests/unit/test_family_convention_example.py` (reader family discovered via `iter_public_readers`)
- [x] `pyyaml` added as a dev dependency (layer-policy parser)
- [ ] Deferred to follow-up: `CONTRIBUTING.md` one-line-per-guard (held by #364 / PR #378)
- [ ] Owner: gate-integrity change (new hooks) awaits review; `GATE_CHANGE_OK` and `bin/quality_baseline.txt` untouched
