"""Enforce that every class in a schema module is a Pydantic model.

``_internal/config/CLAUDE.md`` documents the convention "one file per XML standard, holding a tree
of nested ``pydantic.BaseModel`` classes". Until now that was prose only: nothing stopped a
behavioural class (service, adapter, port) from leaking into a schema file. This hook is the
structural form, in the line of ``bin/check_typing.py`` and ``bin/check_provenance.py``.

Rule, for every ``.py`` under ``src/**/_internal/config/schemas/`` (``__init__.py`` excluded):
**every ``class`` defined in the module must derive from ``pydantic.BaseModel``** — directly, or
transitively through another class defined in the same file. A domain ``Enum`` / ``StrEnum`` /
``IntEnum`` is allowed (a model field's value set). Bases are resolved through the module's
imports, so an unrelated class that is merely named ``BaseModel`` fails. Re-export aliases
(``X = Y`` assignments) are not classes and are never inspected. Every violation is a hard error
(exit 1) naming file, line, and class.
"""

import ast
import pathlib
import sys


_ALLOWED_IMPORTS = {
	"pydantic": frozenset({"BaseModel"}),
	"enum": frozenset({"Enum", "StrEnum", "IntEnum"}),
}


def _imported_bases(tree: ast.Module) -> tuple[set[str], dict[str, frozenset[str]]]:
	"""Resolve which local names are bound to an allowed base by the module's imports.

	Parameters
	----------
	tree : ast.Module
		The parsed module.

	Returns
	-------
	tuple[set[str], dict[str, frozenset[str]]]
		Names bound by ``from pydantic import BaseModel [as X]`` and the like, and the module
		aliases bound by ``import pydantic [as p]`` with the attributes each one allows.
	"""
	names: set[str] = set()
	modules: dict[str, frozenset[str]] = {}
	for node in ast.walk(tree):
		if (
			isinstance(node, ast.ImportFrom)
			and node.level == 0
			and node.module in _ALLOWED_IMPORTS
		):
			names |= {
				alias.asname or alias.name
				for alias in node.names
				if alias.name in _ALLOWED_IMPORTS[node.module]
			}
		elif isinstance(node, ast.Import):
			for alias in node.names:
				if alias.name in _ALLOWED_IMPORTS:
					modules[alias.asname or alias.name] = _ALLOWED_IMPORTS[alias.name]
	return names, modules


def _is_allowed(base: ast.expr, names: set[str], modules: dict[str, frozenset[str]]) -> bool:
	"""Return whether a class base resolves to an allowed base or an allowed in-file class.

	Parameters
	----------
	base : ast.expr
		One entry of ``ClassDef.bases``.
	names : set[str]
		Local names known to be allowed.
	modules : dict[str, frozenset[str]]
		Module aliases and the attributes each one allows.

	Returns
	-------
	bool
		``True`` for an allowed base; ``False`` for anything else, ``Generic[T]`` included.
	"""
	if isinstance(base, ast.Name):
		return base.id in names
	if isinstance(base, ast.Attribute) and isinstance(base.value, ast.Name):
		return base.attr in modules.get(base.value.id, frozenset())
	return False


def _offenders(tree: ast.Module) -> list[ast.ClassDef]:
	"""Return the classes of a module that do not derive from ``BaseModel`` (or an Enum).

	Acceptance is per definition, not per name, so a later non-model class cannot hide behind an
	earlier model of the same name.

	Parameters
	----------
	tree : ast.Module
		The parsed module.

	Returns
	-------
	list[ast.ClassDef]
		Offending classes, in source order.
	"""
	names, modules = _imported_bases(tree)
	classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
	good: set[ast.ClassDef] = set()
	# Iterate until stable, since a subclass of an allowed in-file class is allowed too.
	grew = True
	while grew:
		grew = False
		for cls in classes:
			if cls not in good and any(_is_allowed(b, names, modules) for b in cls.bases):
				good.add(cls)
				names.add(cls.name)
				grew = True
	return sorted((c for c in classes if c not in good), key=lambda c: c.lineno)


def check_file(filepath: str) -> int:
	"""Check that every class in a schema module is a Pydantic model or Enum.

	Parameters
	----------
	filepath : str
		Path to a schema module.

	Returns
	-------
	int
		Number of offending classes found.
	"""
	with open(filepath, encoding="utf-8") as fh:
		tree = ast.parse(fh.read(), filename=filepath)
	bad = _offenders(tree)
	for cls in bad:
		print(
			f"❌ {filepath}:{cls.lineno}: class {cls.name} does not derive from BaseModel — "
			f"a schema module holds only pydantic models (and domain Enums); put behaviour in "
			f"ports/ or the section package."
		)
	return len(bad)


def _schema_files() -> list[pathlib.Path]:
	"""Collect every schema module under ``src/**/_internal/config/schemas/``.

	Returns
	-------
	list[pathlib.Path]
		Schema modules, ``__init__.py`` excluded.
	"""
	return sorted(
		p
		for p in pathlib.Path("src").rglob("_internal/config/schemas/*.py")
		if p.name != "__init__.py"
	)


if __name__ == "__main__":
	files = _schema_files()
	n_classes = sum(
		isinstance(n, ast.ClassDef)
		for p in files
		for n in ast.walk(ast.parse(p.read_text(encoding="utf-8")))
	)
	total_errors = sum(check_file(str(p)) for p in files)
	print(f"check_schemas: inspected {len(files)} files, {n_classes} classes")
	sys.exit(1 if total_errors > 0 else 0)
