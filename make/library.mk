# Library-only targets — present only when scaffolded as a distributable library
# (the lib-minimal scaffold copies this into make/ and the Makefile -includes it).
# Not shipped to the service tiers, which are applications, not published packages.
.PHONY: install_dist_locally

# Build the wheel/sdist, install it, and smoke-import the package — catches packaging
# mistakes (missing __init__, unshipped _internal subpackages) that source-tree tests miss.
# Uses `python -m build` (a PEP 517 frontend) so poetry-dynamic-versioning stamps the real
# version into the wheel; `poetry build` would ignore the backend. The editable install resolves
# __version__ to the 0.0.0 placeholder (expected), so we report the built wheel's actual
# tag-derived version rather than that placeholder. The package name is read from pyproject at
# runtime (`poetry version`), so this file needs no per-project substitution.
install_dist_locally:
	@rm -rf dist/* build/ ./*.egg-info/
	@$(POETRY) run python -m build
	@$(POETRY) install
	@pkg=$$($(POETRY) version | awk '{print $$1}' | tr '-' '_'); \
		$(POETRY) run python -c "import importlib, sys; m = importlib.import_module(sys.argv[1]); assert m.__version__; print('Package import works; __version__ resolves')" "$$pkg"
	@$(POETRY) run python -c "import pathlib; print('Built wheel:', sorted(pathlib.Path('dist').glob('*.whl'))[-1].name)"
