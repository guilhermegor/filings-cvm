# Repo-policy workflows (#366)

- [x] Import the six BlueprintX workflows and their three `bin/` scripts
- [x] Integration tests for the scripts in `tests/integration/test_bin_scripts.py`
- [x] Take the template PR template; merge `SECURITY.md` and Dependabot `cooldown`
- [x] Record the overlap decisions in `.github/CLAUDE.md`
- [ ] Deferred: `.review-bots.yaml` alignment (held by #369) and `CONTRIBUTING.md` (held by #364/#378)
- [ ] Deferred: `pr_gate.py` must skip `dependabot[bot]` PRs so it does not fight the template's major-update disarm
