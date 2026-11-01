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
