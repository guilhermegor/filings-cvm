# Isolate GIT_* env in tests (#374)

- [x] Autouse fixture in `tests/conftest.py` drops the git-hook `GIT_*` variables.
- [x] `tests/unit/test_conftest_git_isolation.py` proves it in a subprocess, one case per variable.
