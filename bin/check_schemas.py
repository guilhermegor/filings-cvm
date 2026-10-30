"""Enforce that every class in a schema module is a Pydantic model.

``_internal/config/CLAUDE.md`` documents the convention "one file per XML standard, holding a tree
of nested ``pydantic.BaseModel`` classes". Until now that was prose only: nothing stopped a
behavioural class (service, adapter, port) from leaking into a schema file. This hook is the
structural form, in the line of ``bin/check_typing.py`` and ``bin/check_provenance.py``.

Rule, for every ``.py`` under ``src/**/_internal/config/schemas/`` (``__init__.py`` excluded):
**every ``class`` defined in the module must derive from ``BaseModel``** — directly, or
transitively through another class defined in the same file. A domain ``Enum`` / ``StrEnum`` /
``IntEnum`` is allowed (a model field's value set). Re-export aliases (``X = Y`` assignments) are
not classes and are never inspected. Every violation is a hard error (exit 1) naming file, line,
and class.
"""

import ast
import pathlib
import sys


_MODEL_BASES = frozenset({"BaseModel"})
_ENUM_BASES = frozenset({"Enum", "StrEnum", "IntEnum"})


def _base_name(base: ast.expr) -> str | None:
	"""Return the unqualified name of a class base (``a.B`` -> ``B``), or ``None``.

	Parameters
	----------
	base : ast.expr
		One entry of ``ClassDef.bases``.

	Returns
	-------
	str | None
		The base's name, or ``None`` for shapes such as ``Generic[T]``.
	"""
	if isinstance(base, ast.Name):
		return base.id
	if isinstance(base, ast.Attribute):
		return base.attr
	return None


def _offenders(tree: ast.Module) -> list[ast.ClassDef]:
	"""Return the classes of a module that do not derive from ``BaseModel`` (or an Enum).

	Parameters
	----------
	tree : ast.Module
		The parsed module.

	Returns
	-------
	list[ast.ClassDef]
		Offending classes, in source order.
	"""
	classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
	allowed = set(_MODEL_BASES) | _ENUM_BASES
	# Iterate until stable, since a subclass of an allowed in-file class is allowed too.
	grew = True
	good: set[str] = set()
	while grew:
		grew = False
		for cls in classes:
			if cls.name in good:
				continue
			if any(_base_name(b) in allowed for b in cls.bases):
				good.add(cls.name)
				allowed.add(cls.name)
				grew = True
	return sorted((c for c in classes if c.name not in good), key=lambda c: c.lineno)


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
