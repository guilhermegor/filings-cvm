#!/usr/bin/env python
"""Enforce the type-prefix naming rule from ``.claude/CLAUDE.md`` ("Naming conventions").

Every variable name must start with a type prefix (``str_``, ``int_``, ``df_``, ...), leading
underscores ignored and case ignored, so ``_PATH_BIN`` passes and ``_BIN`` fails. The prefix
vocabulary is read from the Markdown table in ``.claude/CLAUDE.md`` at run time; it is never
duplicated here, so editing the table changes the gate.

Covered binding sites, in ``src/``, ``tests/`` and ``bin/``: assignment targets (module, class
and function scope, annotated and walrus included), ``for`` / comprehension / ``with`` / ``except``
targets and every parameter (positional, keyword-only, ``*args``, ``**kwargs``, lambda).

Exempt, because the code does not choose the name:

- ``self`` / ``cls`` (the receiver), dunders and ``_``;
- a parameter of a ``test_*`` function or ``@pytest.fixture`` function in ``tests/`` whose name
  is a fixture shipped by pytest or by an installed pytest plugin (``pytest11`` entry point).
  The registry is built by parsing those packages for ``@fixture``-decorated functions, so it
  tracks the installed versions; fixtures defined in this repository are NOT exempt, because the
  repository chose those names;
- a parameter of a method that overrides one declared by an imported third-party base class
  (resolved by importing the base and testing ``hasattr``), because the override must keep the
  parent's keyword names.

Prefix-vs-annotation mismatches (``int_x: str``) are measured by ``--mismatches`` and are not
part of the blocking check: the annotation only names a type for the unambiguous builtin and
library types in ``DICT_ANNOTATION_PREFIX``.

Usage::

    python bin/check_type_prefix.py [FILE ...]   # exit 1 on any finding
    python bin/check_type_prefix.py --report     # per-area counts, never fails
    python bin/check_type_prefix.py --mismatches # prefix-vs-annotation disagreements
"""

import ast
import collections
import importlib
import importlib.metadata
import importlib.util
import pathlib
import re
import sys


PATH_ROOT = pathlib.Path(__file__).resolve().parent.parent
PATH_TABLE = PATH_ROOT / ".claude" / "CLAUDE.md"
STR_TABLE_HEADING = "## Naming conventions"
TUPLE_SCAN_DIRS = ("src", "tests", "bin")
STR_PYTEST_PLUGIN_GROUP = "pytest11"
RE_TABLE_PREFIX = re.compile(r"`([a-z]+)_`")
TUPLE_PSEUDO_FIXTURES = ("request",)
TUPLE_RECEIVERS = ("self", "cls", "_")
DICT_ANNOTATION_PREFIX = {
	"str": ("str",),
	"int": ("int",),
	"float": ("float",),
	"bool": ("bool", "is", "has", "can"),
	"bytes": ("bytes",),
	"list": ("list",),
	"tuple": ("tuple",),
	"dict": ("dict", "json"),
	"Decimal": ("decimal",),
	"Path": ("path",),
	"DataFrame": ("df",),
	"Series": ("series",),
	"ndarray": ("arr",),
	"Callable": ("fn",),
	"Pattern": ("re",),
	"datetime": ("dt",),
	"date": ("dt",),
}


def table_prefixes(path_table: pathlib.Path = PATH_TABLE) -> tuple:
	"""Read the prefix vocabulary from the naming-conventions table.

	Parameters
	----------
	path_table : pathlib.Path
		The ``CLAUDE.md`` holding the "Naming conventions" section.

	Returns
	-------
	tuple of str
		Every backticked ``xxx_`` token between the section heading and the next ``## `` heading,
		in order of appearance, without the trailing underscore.

	Raises
	------
	ValueError
		When the section or its table is missing, so the gate cannot pass vacuously.
	"""
	list_lines = path_table.read_text(encoding="utf-8").splitlines()
	list_found = []
	bool_inside = False
	for str_line in list_lines:
		if str_line.startswith(STR_TABLE_HEADING):
			bool_inside = True
			continue
		if bool_inside and str_line.startswith("## "):
			break
		if bool_inside and str_line.startswith("|"):
			list_found.extend(RE_TABLE_PREFIX.findall(str_line))
	if not list_found:
		raise ValueError(f"no prefix table found under '{STR_TABLE_HEADING}' in {path_table}")
	return tuple(dict.fromkeys(list_found))


def has_prefix(str_name: str, tuple_prefixes: tuple) -> bool:
	"""Return whether a name starts with a table prefix, ignoring underscores and case.

	Parameters
	----------
	str_name : str
		The identifier under test.
	tuple_prefixes : tuple of str
		Prefixes without the trailing underscore.

	Returns
	-------
	bool
		True when the name, stripped of leading underscores, begins with ``<prefix>_``.
	"""
	str_stripped = str_name.lstrip("_").lower()
	return any(str_stripped.startswith(f"{str_prefix}_") for str_prefix in tuple_prefixes)


def fixture_names_in(path_dir: pathlib.Path) -> set:
	"""Collect the names of ``@fixture`` / ``@pytest.fixture`` functions under a directory.

	Parameters
	----------
	path_dir : pathlib.Path
		A package directory, parsed statically (never imported).

	Returns
	-------
	list of str
		Function names carrying a ``fixture`` decorator, bare, attribute or called.
	"""
	list_names = []
	for path_file in path_dir.rglob("*.py"):
		try:
			cls_tree = ast.parse(path_file.read_text(encoding="utf-8"))
		except (SyntaxError, UnicodeDecodeError):
			continue
		for cls_node in ast.walk(cls_tree):
			if isinstance(cls_node, ast.FunctionDef | ast.AsyncFunctionDef) and any(
				is_fixture_decorator(cls_dec) for cls_dec in cls_node.decorator_list
			):
				list_names.append(cls_node.name)
	return list_names


def is_fixture_decorator(cls_dec: ast.expr) -> bool:
	"""Return whether a decorator expression is ``fixture`` or ``pytest.fixture``.

	Parameters
	----------
	cls_dec : ast.expr
		One entry of a function's ``decorator_list``.

	Returns
	-------
	bool
		True for ``@fixture``, ``@pytest.fixture`` and their called forms.
	"""
	cls_target = cls_dec.func if isinstance(cls_dec, ast.Call) else cls_dec
	if isinstance(cls_target, ast.Attribute):
		return cls_target.attr == "fixture"
	return isinstance(cls_target, ast.Name) and cls_target.id == "fixture"


def pytest_fixture_registry() -> tuple:
	"""Build the set of fixture names pytest and installed pytest plugins inject.

	Returns
	-------
	tuple of str
		Names defined by ``_pytest`` (plus ``request``, which pytest injects without a
		``@fixture`` function, hence ``TUPLE_PSEUDO_FIXTURES``) plus every top-level package
		behind a ``pytest11``
		entry point, so the set follows the installed versions without a hand list.
	"""
	list_names = []
	list_dirs = []
	cls_spec = importlib.util.find_spec("_pytest")
	if cls_spec and cls_spec.submodule_search_locations:
		list_dirs.extend(pathlib.Path(str_loc) for str_loc in cls_spec.submodule_search_locations)
	for cls_entry in importlib.metadata.entry_points(group=STR_PYTEST_PLUGIN_GROUP):
		str_top = cls_entry.value.split(":")[0].split(".")[0]
		cls_plugin_spec = importlib.util.find_spec(str_top)
		if cls_plugin_spec and cls_plugin_spec.submodule_search_locations:
			list_dirs.extend(
				pathlib.Path(str_loc) for str_loc in cls_plugin_spec.submodule_search_locations
			)
	for path_dir in list_dirs:
		list_names.extend(fixture_names_in(path_dir))
	return tuple(dict.fromkeys([*list_names, *TUPLE_PSEUDO_FIXTURES]))


def import_map(cls_tree: ast.Module) -> dict:
	"""Map each imported local alias to its ``(module, attribute)`` origin.

	Parameters
	----------
	cls_tree : ast.Module
		A parsed source file.

	Returns
	-------
	dict
		``alias -> (module, attribute)``; ``attribute`` is ``""`` for ``import a.b as x``.
	"""
	dict_map = {}
	for cls_node in ast.walk(cls_tree):
		if isinstance(cls_node, ast.ImportFrom) and cls_node.module and cls_node.level == 0:
			for cls_alias in cls_node.names:
				dict_map[cls_alias.asname or cls_alias.name] = (cls_node.module, cls_alias.name)
		elif isinstance(cls_node, ast.Import):
			for cls_alias in cls_node.names:
				dict_map[cls_alias.asname or cls_alias.name.split(".")[0]] = (cls_alias.name, "")
	return dict_map


def external_base(cls_base: ast.expr, dict_imports: dict) -> object:
	"""Import and return a third-party base class, or ``None`` when it is local or unresolvable.

	Parameters
	----------
	cls_base : ast.expr
		One entry of a ``ClassDef.bases``.
	dict_imports : dict
		The file's ``import_map``.

	Returns
	-------
	object
		The imported class, or ``None`` for local bases and for imports that fail.
	"""
	if isinstance(cls_base, ast.Name):
		tuple_origin = dict_imports.get(cls_base.id)
		if not tuple_origin or not tuple_origin[1]:
			return None
		str_module, str_attr = tuple_origin
	elif isinstance(cls_base, ast.Attribute) and isinstance(cls_base.value, ast.Name):
		tuple_origin = dict_imports.get(cls_base.value.id)
		if not tuple_origin:
			return None
		str_module, str_attr = tuple_origin[0], cls_base.attr
	else:
		return None
	if str_module.split(".")[0] == "filings_cvm":
		return None
	try:
		return getattr(importlib.import_module(str_module), str_attr, None)
	except Exception:  # noqa: BLE001
		return None


def overrides_external(cls_class: ast.ClassDef, str_method: str, dict_imports: dict) -> bool:
	"""Return whether a method overrides one declared by an imported third-party base.

	Parameters
	----------
	cls_class : ast.ClassDef
		The class holding the method.
	str_method : str
		The method name.
	dict_imports : dict
		The file's ``import_map``.

	Returns
	-------
	bool
		True when any third-party base exposes an attribute of that name.
	"""
	for cls_base in cls_class.bases:
		cls_base_type = external_base(cls_base, dict_imports)
		if cls_base_type is not None and hasattr(cls_base_type, str_method):
			return True
	return False


def annotation_key(cls_annotation: ast.expr | None) -> str:
	"""Reduce an annotation to the single type name used to look up expected prefixes.

	Parameters
	----------
	cls_annotation : ast.expr or None
		A parameter or variable annotation.

	Returns
	-------
	str
		The base name (``list[str]`` -> ``list``, ``X | None`` -> ``X``), or ``""`` when absent
		or not a plain type reference.
	"""
	if cls_annotation is None:
		return ""
	if isinstance(cls_annotation, ast.BinOp) and isinstance(cls_annotation.op, ast.BitOr):
		for cls_side in (cls_annotation.left, cls_annotation.right):
			str_key = annotation_key(cls_side)
			if str_key:
				return str_key
		return ""
	if isinstance(cls_annotation, ast.Subscript):
		return annotation_key(cls_annotation.value)
	if isinstance(cls_annotation, ast.Attribute):
		return cls_annotation.attr
	if isinstance(cls_annotation, ast.Name):
		return cls_annotation.id
	return ""


def scope_chain(cls_node: ast.AST, dict_parents: dict) -> tuple:
	"""Return ``(kind, enclosing function, enclosing class)`` for a node.

	Parameters
	----------
	cls_node : ast.AST
		A binding node.
	dict_parents : dict
		Child-to-parent mapping for the tree.

	Returns
	-------
	tuple
		``kind`` is ``module``, ``class`` or ``function``; the other two are the nearest
		enclosing definitions or ``None``.
	"""
	cls_func = None
	cls_class = None
	cls_cur = dict_parents.get(cls_node)
	while cls_cur is not None:
		if cls_func is None and isinstance(cls_cur, ast.FunctionDef | ast.AsyncFunctionDef):
			cls_func = cls_cur
		if cls_class is None and isinstance(cls_cur, ast.ClassDef):
			cls_class = cls_cur
		cls_cur = dict_parents.get(cls_cur)
	if cls_func is not None:
		return "function", cls_func, cls_class
	return ("class" if cls_class is not None else "module"), None, cls_class


def is_fixture_consumer(
	cls_func: ast.FunctionDef | ast.AsyncFunctionDef, path_file: pathlib.Path
) -> bool:
	"""Return whether pytest injects this function's parameters by name.

	Parameters
	----------
	cls_func : ast.FunctionDef or ast.AsyncFunctionDef
		The function owning a parameter.
	path_file : pathlib.Path
		The file holding it; only files under a ``tests`` directory qualify.

	Returns
	-------
	bool
		True for ``test_*`` functions and ``@fixture`` functions inside ``tests/``.
	"""
	if "tests" not in path_file.parts:
		return False
	return cls_func.name.startswith("test_") or any(
		is_fixture_decorator(cls_dec) for cls_dec in cls_func.decorator_list
	)


def binding_sites(cls_tree: ast.Module) -> list:
	"""List every name the source binds, with its line and node context.

	Parameters
	----------
	cls_tree : ast.Module
		A parsed source file.

	Returns
	-------
	list of tuple
		``(name, lineno, source, node)`` where ``source`` is ``param``, ``assign``, ``loop``,
		``comp``, ``with`` or ``except``.
	"""
	dict_parents = {
		cls_child: cls_parent
		for cls_parent in ast.walk(cls_tree)
		for cls_child in ast.iter_child_nodes(cls_parent)
	}
	dict_source = {ast.For: "loop", ast.comprehension: "comp", ast.withitem: "with"}
	list_sites = []
	for cls_node in ast.walk(cls_tree):
		if isinstance(cls_node, ast.Name) and isinstance(cls_node.ctx, ast.Store):
			str_source = dict_source.get(type(dict_parents.get(cls_node)), "assign")
			list_sites.append((cls_node.id, cls_node.lineno, str_source, cls_node))
		elif isinstance(cls_node, ast.arg):
			list_sites.append((cls_node.arg, cls_node.lineno, "param", cls_node))
		elif isinstance(cls_node, ast.ExceptHandler) and cls_node.name:
			list_sites.append((cls_node.name, cls_node.lineno, "except", cls_node))
	return [(*tuple_site, dict_parents) for tuple_site in list_sites]


def owner_function(cls_arg: ast.arg, dict_parents: dict) -> ast.AST | None:
	"""Return the function or lambda whose signature declares a parameter.

	Parameters
	----------
	cls_arg : ast.arg
		A parameter node.
	dict_parents : dict
		Child-to-parent mapping for the tree.

	Returns
	-------
	ast.AST or None
		The ``arguments`` node's parent.
	"""
	return dict_parents.get(dict_parents.get(cls_arg))


def is_exempt(
	str_name: str,
	str_source: str,
	cls_node: ast.AST,
	dict_parents: dict,
	path_file: pathlib.Path,
	dict_imports: dict,
	tuple_fixtures: tuple,
) -> bool:
	"""Return whether a name is one the code does not choose.

	Parameters
	----------
	str_name : str
		The bound name.
	str_source : str
		The binding kind from ``binding_sites``.
	cls_node : ast.AST
		The binding node.
	dict_parents : dict
		Child-to-parent mapping for the tree.
	path_file : pathlib.Path
		The file under test.
	dict_imports : dict
		The file's ``import_map``.
	tuple_fixtures : tuple of str
		The pytest-injected fixture names.

	Returns
	-------
	bool
		True for receivers, dunders, injected fixtures and overridden third-party parameters.
	"""
	if str_name in TUPLE_RECEIVERS or (str_name.startswith("__") and str_name.endswith("__")):
		return True
	if str_source != "param":
		return False
	cls_owner = owner_function(cls_node, dict_parents)
	if not isinstance(cls_owner, ast.FunctionDef | ast.AsyncFunctionDef):
		return False
	if str_name in tuple_fixtures and is_fixture_consumer(cls_owner, path_file):
		return True
	_, _, cls_class = scope_chain(cls_owner, dict_parents)
	return cls_class is not None and overrides_external(cls_class, cls_owner.name, dict_imports)


def file_findings(path_file: pathlib.Path, tuple_prefixes: tuple, tuple_fixtures: tuple) -> list:
	"""Return every unprefixed, non-exempt binding in one file.

	Parameters
	----------
	path_file : pathlib.Path
		A ``.py`` file.
	tuple_prefixes : tuple of str
		The table vocabulary.
	tuple_fixtures : tuple of str
		The pytest-injected fixture names.

	Returns
	-------
	list of tuple
		``(lineno, name, scope_kind, source)`` per finding.
	"""
	try:
		cls_tree = ast.parse(path_file.read_text(encoding="utf-8"), filename=str(path_file))
	except SyntaxError:
		return [(0, "<unparsable>", "module", "syntax")]
	dict_imports = import_map(cls_tree)
	list_found = []
	for str_name, int_line, str_source, cls_node, dict_parents in binding_sites(cls_tree):
		if has_prefix(str_name, tuple_prefixes):
			continue
		if is_exempt(
			str_name, str_source, cls_node, dict_parents, path_file, dict_imports, tuple_fixtures
		):
			continue
		str_kind = "function" if str_source == "param" else scope_chain(cls_node, dict_parents)[0]
		list_found.append((int_line, str_name, str_kind, str_source))
	return list_found


def mismatch_findings(path_file: pathlib.Path, tuple_prefixes: tuple) -> list:
	"""Return annotated bindings whose prefix disagrees with their annotation.

	Parameters
	----------
	path_file : pathlib.Path
		A ``.py`` file.
	tuple_prefixes : tuple of str
		The table vocabulary.

	Returns
	-------
	list of tuple
		``(lineno, name, annotation_type)`` for each prefixed name annotated with a different
		known type.
	"""
	try:
		cls_tree = ast.parse(path_file.read_text(encoding="utf-8"))
	except SyntaxError:
		return []
	list_found = []
	list_variadic = [
		cls_args.vararg for cls_args in ast.walk(cls_tree) if isinstance(cls_args, ast.arguments)
	] + [cls_args.kwarg for cls_args in ast.walk(cls_tree) if isinstance(cls_args, ast.arguments)]
	for cls_node in ast.walk(cls_tree):
		if any(cls_node is cls_var for cls_var in list_variadic):
			continue
		if isinstance(cls_node, ast.arg):
			str_name, cls_ann, int_line = cls_node.arg, cls_node.annotation, cls_node.lineno
		elif isinstance(cls_node, ast.AnnAssign) and isinstance(cls_node.target, ast.Name):
			str_name, cls_ann, int_line = cls_node.target.id, cls_node.annotation, cls_node.lineno
		else:
			continue
		str_key = annotation_key(cls_ann)
		tuple_expected = DICT_ANNOTATION_PREFIX.get(str_key)
		if not tuple_expected or not has_prefix(str_name, tuple_prefixes):
			continue
		str_stripped = str_name.lstrip("_").lower()
		if not any(str_stripped.startswith(f"{str_pre}_") for str_pre in tuple_expected):
			list_found.append((int_line, str_name, str_key))
	return list_found


def python_files(list_argv: list) -> list:
	"""Resolve the files to check.

	Parameters
	----------
	list_argv : list of str
		Explicit filenames (as pre-commit passes them); empty means every ``.py`` under
		``src/``, ``tests/`` and ``bin/``.

	Returns
	-------
	list of pathlib.Path
		Sorted ``.py`` paths.
	"""
	if list_argv:
		return sorted(
			pathlib.Path(str_arg).resolve() for str_arg in list_argv if str_arg.endswith(".py")
		)
	list_paths = []
	for str_dir in TUPLE_SCAN_DIRS:
		list_paths.extend((PATH_ROOT / str_dir).rglob("*.py"))
	return sorted(path_file for path_file in list_paths if "__pycache__" not in path_file.parts)


def area_of(path_file: pathlib.Path) -> str:
	"""Name the report bucket a file belongs to.

	Parameters
	----------
	path_file : pathlib.Path
		An absolute file path under the repository root.

	Returns
	-------
	str
		``src/filings_cvm/ingestion/<root>``, ``src/filings_cvm/<section>``, ``tests/<kind>``
		or ``bin``.
	"""
	tuple_parts = pathlib.Path(show(path_file)).parts
	if tuple_parts[:3] == ("src", "filings_cvm", "ingestion") and len(tuple_parts) > 4:
		return "/".join(tuple_parts[:4])
	if tuple_parts[0] == "src":
		return "/".join(tuple_parts[:3])
	if tuple_parts[0] == "tests":
		return "/".join(tuple_parts[:2])
	return tuple_parts[0]


def show(path_file: pathlib.Path) -> str:
	"""Return a repo-relative path when possible, the absolute one otherwise.

	Parameters
	----------
	path_file : pathlib.Path
		A file path.

	Returns
	-------
	str
		The path text used in findings.
	"""
	try:
		return str(path_file.relative_to(PATH_ROOT))
	except ValueError:
		return str(path_file)


def print_report(list_paths: list, tuple_prefixes: tuple, tuple_fixtures: tuple) -> None:
	"""Print unprefixed counts per area and per binding kind.

	Parameters
	----------
	list_paths : list of pathlib.Path
		Files to measure.
	tuple_prefixes : tuple of str
		The table vocabulary.
	tuple_fixtures : tuple of str
		The pytest-injected fixture names.
	"""
	dict_area = collections.Counter()
	dict_kind = collections.Counter()
	for path_file in list_paths:
		for _, _, str_kind, str_source in file_findings(path_file, tuple_prefixes, tuple_fixtures):
			dict_area[area_of(path_file)] += 1
			dict_kind[f"{str_kind}/{str_source}"] += 1
	print("unprefixed bindings per area")
	for str_area, int_count in sorted(dict_area.items()):
		print(f"{int_count:7}  {str_area}")
	print("\nunprefixed bindings per kind")
	for str_kind, int_count in sorted(dict_kind.items()):
		print(f"{int_count:7}  {str_kind}")
	print(f"\nTOTAL {sum(dict_area.values())} across {len(list_paths)} file(s)")


def main(list_argv: list) -> int:
	"""Run the gate, the report or the mismatch measurement.

	Parameters
	----------
	list_argv : list of str
		``--report``, ``--mismatches`` or filenames.

	Returns
	-------
	int
		1 when the check finds an unprefixed name, otherwise 0.
	"""
	bool_report = "--report" in list_argv
	bool_mismatches = "--mismatches" in list_argv
	list_files = [str_arg for str_arg in list_argv if not str_arg.startswith("--")]
	tuple_prefixes = table_prefixes()
	tuple_fixtures = pytest_fixture_registry()
	list_paths = python_files(list_files)
	if bool_report:
		print_report(list_paths, tuple_prefixes, tuple_fixtures)
		return 0
	if bool_mismatches:
		int_total = 0
		for path_file in list_paths:
			for int_line, str_name, str_key in mismatch_findings(path_file, tuple_prefixes):
				print(f"{show(path_file)}:{int_line}: {str_name} annotated {str_key}")
				int_total += 1
		print(f"{int_total} mismatch(es)")
		return 0
	int_total = 0
	for path_file in list_paths:
		for int_line, str_name, str_kind, str_source in file_findings(
			path_file, tuple_prefixes, tuple_fixtures
		):
			print(
				f"{show(path_file)}:{int_line}: {str_name} ({str_kind} {str_source}) lacks prefix"
			)
			int_total += 1
	if int_total:
		print(f"\n{int_total} unprefixed name(s). Prefixes come from .claude/CLAUDE.md.")
		return 1
	print(f"✅ type prefixes OK ({len(list_paths)} file(s) checked)")
	return 0


if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))
