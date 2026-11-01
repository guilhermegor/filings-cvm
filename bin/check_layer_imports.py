"""Enforce the per-layer import policy: a vendor lives behind a seam, not in a layer.

The prose rule ("every third-party dependency is reached through a seam in ``utils/``") is
only a suggestion until something reads it. This gate reads it.

Three classifications, in order:

1. **stdlib** — always allowed, in every layer. It carries no coupling risk.
2. **first-party** — always allowed here. Direction between layers is a separate concern.
3. **third-party** — allowed only if the file's layer names it in ``allow``, WITH a reason.

Two properties are deliberate, because both are how the rule gets evaded in practice:

- **Scope is irrelevant to the verdict.** An import inside a function is judged exactly like
  one at the top of the file. Deferring an import does not undo the layer's knowledge of the
  vendor, so scope only changes where this gate has to LOOK, never what it decides. It does
  change the message, because that is the form that used to pass unnoticed.
- **A vendor may be allowed as a TYPE and denied as an API.** ``pandas`` is the vocabulary the
  layers speak: ``-> pd.DataFrame`` in a signature couples nothing, while ``pd.read_sql(...)``
  couples everything. A module under ``annotation_only`` may appear in annotations and
  nowhere else; the construction and reading live behind the ``utils/`` seams.

The policy lives in ``.layer-policy.yaml`` at the project root. No file, no gate — the check
exits 0, so a tier that has not adopted it is not blocked.
"""

from __future__ import annotations

import ast
import fnmatch
import pathlib
import sys


try:
	import yaml
except ModuleNotFoundError:  # pragma: no cover - the gate self-skips without its parser
	yaml = None  # type: ignore[assignment]


_POLICY_FILE = ".layer-policy.yaml"
_SRC_ROOT = "src"
_ROOT_LAYER = "__root__"


class _StrictLoader(yaml.SafeLoader if yaml is not None else object):  # type: ignore[misc]
	"""SafeLoader that REFUSES a duplicate mapping key instead of silently keeping the last.

	⚠️ This is a security-relevant file: a repeated ``deny_layers:`` under one layer makes YAML
	keep only the last map, so every rule in the earlier one disappears — no error, no warning,
	and a policy that still parses and still reports success while enforcing less than it says.
	Hit for real while writing this very policy: a second ``deny_layers`` block silently erased
	three layer denials, and the file looked correct in the diff.
	"""

	def construct_mapping(self, node: object, deep: bool = False) -> dict:
		"""Build a mapping, raising on any key that appears twice.

		Parameters
		----------
		node : object
			The YAML mapping node.
		deep : bool, optional
			Passed through to the base loader.

		Returns
		-------
		dict
			The constructed mapping.

		Raises
		------
		ValueError
			When a key appears more than once in the same mapping.
		"""
		list_keys = [self.construct_object(cls_key, deep=deep) for cls_key, _ in node.value]
		set_dupes = {str_key for str_key in list_keys if list_keys.count(str_key) > 1}
		if set_dupes:
			raise ValueError(
				f"{_POLICY_FILE}: duplicate key(s) {sorted(set_dupes)} — YAML keeps only the "
				f"last, so the earlier rules would be dropped in silence."
			)
		return super().construct_mapping(node, deep=deep)


def load_policy(path_root: pathlib.Path) -> dict | None:
	"""Read the layer policy, or ``None`` when the project has not adopted one.

	Parameters
	----------
	path_root : pathlib.Path
		The project root holding ``.layer-policy.yaml``.

	Returns
	-------
	dict or None
		The parsed policy, or ``None`` when the file is absent or empty.
	"""
	path_policy = path_root / _POLICY_FILE
	if yaml is None or not path_policy.is_file():
		return None
	return (
		yaml.load(  # noqa: S506 — SafeLoader-derived; it only ADDS a duplicate-key check
			path_policy.read_text(encoding="utf-8"), Loader=_StrictLoader
		)
		or None
	)


def first_party_roots(path_src: pathlib.Path, dict_policy: dict) -> set[str]:
	"""Return the top-level package names that belong to this project.

	Includes ``first_party_extra`` from the policy, which exists for the **layout shim**: the
	shared helpers ship to both tiers and import their engine as

	``try: from utils.typing import … except ModuleNotFoundError: from chassis.typing import …``

	``chassis`` is first-party — just first-party in the OTHER layout — so a directory scan of
	this tier alone would report all 23 shipped helpers as reaching for a vendor.

	Parameters
	----------
	path_src : pathlib.Path
		The ``src/`` directory.
	dict_policy : dict
		The parsed policy, read for ``first_party_extra``.

	Returns
	-------
	set of str
		Directory names under ``src/``, ``src`` itself, and any declared extras.
	"""
	set_scanned = {p.name for p in path_src.iterdir() if p.is_dir()} | {_SRC_ROOT}
	return set_scanned | set(dict_policy.get("first_party_extra") or [])


def annotation_node_ids(cls_tree: ast.Module) -> set[int]:
	"""Collect the ids of every AST node that sits inside a type annotation.

	Includes ``if TYPE_CHECKING:`` bodies, which exist precisely to hold imports that are
	only ever referenced from annotations.

	Parameters
	----------
	cls_tree : ast.Module
		The parsed module.

	Returns
	-------
	set of int
		``id()`` of each node reachable from an annotation or a TYPE_CHECKING block.
	"""
	set_ids: set[int] = set()

	def _mark(cls_node: ast.AST | None) -> None:
		if cls_node is None:
			return
		for cls_child in ast.walk(cls_node):
			set_ids.add(id(cls_child))

	for cls_node in ast.walk(cls_tree):
		_mark(getattr(cls_node, "annotation", None))
		_mark(getattr(cls_node, "returns", None))
		if isinstance(cls_node, ast.If) and _is_type_checking_test(cls_node.test):
			for cls_stmt in cls_node.body:
				_mark(cls_stmt)
	return set_ids


def _is_type_checking_test(cls_test: ast.expr) -> bool:
	"""Return whether an ``if`` test is exactly the TYPE_CHECKING guard.

	⚠️ Matched STRUCTURALLY, never as a substring of ``ast.dump``. The substring form also
	matched ``if not TYPE_CHECKING:`` — whose body runs at RUNTIME — and any unrelated name
	containing the word, so a vendor imported under either would have been treated as
	annotation-only and escaped the check entirely.

	Parameters
	----------
	cls_test : ast.expr
		The ``if`` statement's test expression.

	Returns
	-------
	bool
		``True`` only for bare ``TYPE_CHECKING`` or ``<module>.TYPE_CHECKING``.
	"""
	if isinstance(cls_test, ast.Name):
		return cls_test.id == "TYPE_CHECKING"
	return isinstance(cls_test, ast.Attribute) and cls_test.attr == "TYPE_CHECKING"


def imported_names(cls_node: ast.Import | ast.ImportFrom) -> list[tuple[str, str]]:
	"""Return ``(root_module, local_alias)`` for each name an import statement binds.

	Parameters
	----------
	cls_node : ast.Import or ast.ImportFrom
		The import statement.

	Returns
	-------
	list of tuple of (str, str)
		One entry per bound name; the alias is what the module body refers to.
	"""
	list_out: list[tuple[str, str]] = []
	if isinstance(cls_node, ast.Import):
		for cls_alias in cls_node.names:
			str_local = cls_alias.asname or cls_alias.name.split(".")[0]
			list_out.append((cls_alias.name.split(".")[0], str_local))
		return list_out
	if cls_node.level:
		return list_out
	str_root = (cls_node.module or "").split(".")[0]
	for cls_alias in cls_node.names:
		list_out.append((str_root, cls_alias.asname or cls_alias.name))
	return list_out


def resolve_layer(tuple_rel: tuple, dict_policy: dict) -> str:
	"""Return the policy key governing a file, preferring the most SPECIFIC match.

	A layer is normally the first path component, but a nested architecture needs finer keys:
	the DDD tiers put ``domain/``, ``application/`` and ``infrastructure/`` inside each
	capability, and those three have genuinely different rules — the tier's own CLAUDE.md says
	domain depends on *nothing*, application on the domain only, and infrastructure on domain
	ports plus external libs. Collapsed to one ``capabilities`` key, that table is unenforceable.

	A policy may therefore declare a **glob** key (``capabilities/*/domain``), matched against
	the file's directory path. The longest matching glob wins, so a specific rule overrides the
	broad one; with no glob key the behaviour is exactly the first-component one.

	Parameters
	----------
	tuple_rel : tuple of str
		The file's path components below the source root, filename last.
	dict_policy : dict
		The parsed policy.

	Returns
	-------
	str
		The policy key to apply.
	"""
	str_broad = tuple_rel[0] if len(tuple_rel) > 1 else _ROOT_LAYER
	tuple_dirs = tuple_rel[:-1]
	list_keys = [str_key for str_key in (dict_policy.get("layers") or {}) if "*" in str_key]

	for int_depth in range(len(tuple_dirs), 0, -1):
		str_prefix = "/".join(tuple_dirs[:int_depth])
		list_hits = [str_key for str_key in list_keys if fnmatch.fnmatch(str_prefix, str_key)]
		if list_hits:
			return max(list_hits, key=len)
	return str_broad


def resolve_layer_policy(dict_policy: dict, str_layer: str) -> tuple[dict, dict]:
	"""Return the allow-list and annotation-only map that govern one layer.

	The annotation-only map is layered: a file-wide default, overridden per layer. A layer
	may narrow a vendor to annotations even where a sibling layer legitimately calls it.
	Measured: the ORM tier's controller names ``Engine`` only in signatures, while its model
	genuinely CONSTRUCTS with ``DeclarativeBase``/``mapped_column`` — one global verdict
	cannot serve both, and the loose one would be the one that survives.

	Parameters
	----------
	dict_policy : dict
		The parsed ``.layer-policy.yaml``.
	str_layer : str
		The layer being checked.

	Returns
	-------
	tuple of dict
		``(dict_allow, dict_annotation_only)`` for this layer.
	"""
	dict_layer = (dict_policy.get("layers", {}) or {}).get(str_layer) or {}
	dict_annotation_only = {
		**(dict_policy.get("annotation_only") or {}),
		**(dict_layer.get("annotation_only") or {}),
	}
	return dict_layer.get("allow") or {}, dict_annotation_only


def function_line_spans(cls_tree: ast.AST) -> list:
	"""Return the (first, last) line of every function in the tree.

	Parameters
	----------
	cls_tree : ast.AST
		The parsed module.

	Returns
	-------
	list of tuple
		One ``(int_first, int_last)`` pair per function, used only to phrase the message —
		an import deferred into a function is judged exactly like a top-level one.
	"""
	return [
		(cls_n.lineno, max(getattr(c, "lineno", cls_n.lineno) for c in ast.walk(cls_n)))
		for cls_n in ast.walk(cls_tree)
		if isinstance(cls_n, ast.FunctionDef | ast.AsyncFunctionDef)
	]


def _star_import_problem(path_file: pathlib.Path, int_line: int, str_root: str) -> str:
	"""Return the message for a star import of an annotation-only vendor.

	Parameters
	----------
	path_file : pathlib.Path
		The offending module.
	int_line : int
		The import's line number.
	str_root : str
		The vendor's top-level module name.

	Returns
	-------
	str
		A message naming why the star form cannot be annotation-only.
	"""
	return (
		f"{path_file}:{int_line}: 'from {str_root} import *' cannot be annotation-only — the "
		f"names it binds are unknowable, so every use of {str_root!r} would pass unchecked. "
		f"Import the names you annotate with."
	)


def disallowed_import_problems(
	cls_tree: ast.AST,
	path_file: pathlib.Path,
	str_layer: str,
	dict_allow: dict,
	dict_annotation_only: dict,
	set_first_party: set[str],
) -> tuple[list, dict]:
	"""Report every import this layer may not take, and collect the annotation-only aliases.

	Parameters
	----------
	cls_tree : ast.AST
		The parsed module.
	path_file : pathlib.Path
		The module being checked, for the message.
	str_layer : str
		The layer the file belongs to.
	dict_allow : dict
		Vendors this layer may import outright.
	dict_annotation_only : dict
		Vendors this layer may name in annotations only.
	set_first_party : set of str
		Top-level package names that belong to this project.

	Returns
	-------
	tuple
		``(list_problems, dict_annotation_aliases)`` — the findings, and the local names
		bound to annotation-only vendors, for the second pass to police.
	"""
	list_functions = function_line_spans(cls_tree)
	list_problems: list[str] = []
	dict_annotation_aliases: dict[str, str] = {}
	set_reported: set[tuple[int, str]] = set()

	for cls_node in ast.walk(cls_tree):
		if not isinstance(cls_node, ast.Import | ast.ImportFrom):
			continue
		for str_root, str_alias in imported_names(cls_node):
			if (
				str_root in sys.stdlib_module_names
				or str_root in set_first_party
				or str_root in dict_allow
			):
				continue
			if str_root in dict_annotation_only and str_alias != "*":
				dict_annotation_aliases[str_alias] = str_root
				continue
			if (cls_node.lineno, str_root) in set_reported:
				continue
			set_reported.add((cls_node.lineno, str_root))

			bool_in_function = any(a < cls_node.lineno <= b for a, b in list_functions)
			str_where = " (inside a function — deferring the import does not change the verdict)"
			if str_alias == "*" and str_root in dict_annotation_only:
				list_problems.append(_star_import_problem(path_file, cls_node.lineno, str_root))
				continue
			list_problems.append(
				f"{path_file}:{cls_node.lineno}: '{str_root}' is not allowed in layer "
				f"'{str_layer}'{str_where if bool_in_function else ''}. "
				f"Reach it through a seam in utils/, or add it to '{str_layer}'.allow in "
				f"{_POLICY_FILE} with a written reason."
			)
	return list_problems, dict_annotation_aliases


def annotation_only_misuse_problems(
	cls_tree: ast.AST,
	path_file: pathlib.Path,
	str_layer: str,
	dict_annotation_aliases: dict,
	dict_annotation_only: dict,
) -> list:
	"""Report every use of an annotation-only vendor that is not an annotation.

	``-> pd.DataFrame`` in a signature is the vocabulary the layers share and couples
	nothing; ``pd.read_sql(...)`` is a call every copied file inherits.

	Parameters
	----------
	cls_tree : ast.AST
		The parsed module.
	path_file : pathlib.Path
		The module being checked, for the message.
	str_layer : str
		The layer the file belongs to.
	dict_annotation_aliases : dict
		Local name → vendor root, for vendors restricted to annotations.
	dict_annotation_only : dict
		Vendor root → the written reason, quoted back in the message.

	Returns
	-------
	list of str
		Human-readable problems; empty when every use is an annotation.
	"""
	set_annotation_ids = annotation_node_ids(cls_tree)
	list_problems: list[str] = []

	for str_alias, str_root in dict_annotation_aliases.items():
		for cls_node in ast.walk(cls_tree):
			if not isinstance(cls_node, ast.Name) or cls_node.id != str_alias:
				continue
			if id(cls_node) in set_annotation_ids:
				continue
			list_problems.append(
				f"{path_file}:{cls_node.lineno}: '{str_root}' may be used as a TYPE only in "
				f"layer '{str_layer}' — this is a call/attribute use. "
				f"{dict_annotation_only.get(str_root, '')}"
			)
	return list_problems


def find_file_problems(
	path_file: pathlib.Path,
	str_layer: str,
	dict_policy: dict,
	set_first_party: set[str],
	tuple_pkg_parts: tuple = (),
) -> list[str]:
	"""Return every import-policy violation in one file (never raises).

	Parameters
	----------
	path_file : pathlib.Path
		The module to check.
	str_layer : str
		The layer the file belongs to (its first path component under ``src/``).
	dict_policy : dict
		The parsed ``.layer-policy.yaml``.
	set_first_party : set of str
		Top-level package names that belong to this project.
	tuple_pkg_parts : tuple of str, optional
		The file's package path below the layer root, e.g. ``("utils", "sub")``. Needed only
		to resolve RELATIVE imports for ``deny_layers``; empty leaves them unresolved.

	Returns
	-------
	list of str
		Human-readable problems; empty when the file complies.
	"""
	try:
		cls_tree = ast.parse(path_file.read_text(encoding="utf-8"))
	except SyntaxError as cls_exc:
		return [f"{path_file}: could not parse ({cls_exc})"]

	dict_allow, dict_annotation_only = resolve_layer_policy(dict_policy, str_layer)
	list_problems, dict_annotation_aliases = disallowed_import_problems(
		cls_tree, path_file, str_layer, dict_allow, dict_annotation_only, set_first_party
	)
	list_problems += annotation_only_misuse_problems(
		cls_tree, path_file, str_layer, dict_annotation_aliases, dict_annotation_only
	)
	return list_problems + direction_problems(
		cls_tree, path_file, str_layer, dict_policy, tuple_pkg_parts
	)


def relative_import_target(tuple_pkg_parts: tuple, cls_node: ast.ImportFrom) -> str | None:
	"""Resolve a RELATIVE import to the layer it actually targets.

	⚠️ ``imported_names`` deliberately yields nothing for a relative import, because for the
	VENDOR half that is correct: a relative import is first-party by construction. For
	DIRECTION it is the opposite — ``from ..model import Entity`` inside ``utils/`` is exactly
	the coupling ``deny_layers`` exists to forbid, and it was passing unseen.

	Resolution follows Python's own rule: level 1 is the module's own package, and each extra
	level climbs one more, then ``module`` is appended. So the answer depends on how DEEP the
	file sits, not only on the dot count — from ``utils/mod.py`` a two-dot import reaches a
	sibling layer, while from ``utils/sub/mod.py`` the same statement stays inside ``utils``.

	Parameters
	----------
	tuple_pkg_parts : tuple of str
		The file's package path below the layer root, e.g. ``("utils", "sub")``. Empty when
		the caller cannot supply it, in which case no relative import is resolved.
	cls_node : ast.ImportFrom
		The relative import statement (``level`` >= 1).

	Returns
	-------
	str or None
		The target's FULL dotted path, or ``None`` when it cannot be resolved.

		⚠️ Dotted, not just the first component. ``_matching_deny_key`` accepts a dotted key
		(``chassis.db_schema``), and returning only ``chassis`` made every such rule miss —
		so the ABSOLUTE form of an import was rejected while its relative twin passed, which
		is worse than not having the rule at all.
	"""
	if not tuple_pkg_parts:
		return None
	int_climb = cls_node.level - 1
	tuple_base = (
		tuple_pkg_parts[: len(tuple_pkg_parts) - int_climb] if int_climb else tuple_pkg_parts
	)
	if int_climb and len(tuple_pkg_parts) < int_climb:
		return None
	tuple_full = tuple_base + tuple(cls_node.module.split(".")) if cls_node.module else tuple_base
	return ".".join(tuple_full) if tuple_full else None


def direction_problems(
	cls_tree: ast.Module,
	path_file: pathlib.Path,
	str_layer: str,
	dict_policy: dict,
	tuple_pkg_parts: tuple = (),
) -> list[str]:
	"""Return every import that points the WRONG WAY between first-party layers.

	The vendor half of this gate asks "may this layer reach outside the project?". This half
	asks the opposite question — "may this layer reach that layer?" — and they are genuinely
	different: ``utils/`` importing ``model/`` involves no vendor at all, yet it is the design
	error that turns a seam into a cycle. Both rules were prose only
	(``src/utils/CLAUDE.md``: *"utils/ is imported by them, never the reverse"*), and prose
	does not fail a build.

	⚠️ Silent when a layer declares no ``deny_layers``. That is deliberate and is NOT the
	self-skip this gate was just fixed for: the vendor policy is deny-by-default because the
	set of vendors is open-ended, while the set of layers is small, named in the same file,
	and each project decides its own direction. An absent entry means "this layer may reach
	its siblings", which is a real answer rather than an unasked question.

	Parameters
	----------
	cls_tree : ast.Module
		The parsed module.
	path_file : pathlib.Path
		The module's path, for the message.
	str_layer : str
		The layer the file belongs to.
	dict_policy : dict
		The parsed ``.layer-policy.yaml``.
	tuple_pkg_parts : tuple of str, optional
		The file's package path below the layer root, e.g. ``("utils", "sub")``. Needed only
		to resolve RELATIVE imports for ``deny_layers``; empty leaves them unresolved.

	Returns
	-------
	list of str
		Human-readable problems; empty when the file complies.
	"""
	dict_layer = (dict_policy.get("layers", {}) or {}).get(str_layer) or {}
	dict_deny = dict_layer.get("deny_layers") or {}
	if not dict_deny:
		return []

	list_targets = [
		(cls_node, str_module)
		for cls_node in ast.walk(cls_tree)
		for str_module in imported_modules(cls_node)
	]
	list_targets += [
		(cls_node, str_target)
		for cls_node in ast.walk(cls_tree)
		if isinstance(cls_node, ast.ImportFrom) and cls_node.level
		for str_target in [relative_import_target(tuple_pkg_parts, cls_node)]
		if str_target is not None
	]
	return [
		f"{path_file}:{cls_node.lineno}: layer '{str_layer}' must not import "
		f"'{str_target}'. {dict_deny[str_key]}"
		for cls_node, str_target in list_targets
		for str_key in [_matching_deny_key(str_target, dict_deny)]
		if str_key is not None
	]


def imported_modules(cls_node: ast.AST) -> list[str]:
	"""Return the full dotted module path of every absolute import in one statement.

	Relative imports are excluded — they are resolved separately, from the file's own position.

	Parameters
	----------
	cls_node : ast.AST
		Any AST node; non-import nodes yield nothing.

	Returns
	-------
	list of str
		Dotted module paths, e.g. ``["chassis.typing"]``.
	"""
	if isinstance(cls_node, ast.Import):
		return [cls_alias.name for cls_alias in cls_node.names]
	if isinstance(cls_node, ast.ImportFrom) and not cls_node.level:
		return [cls_node.module] if cls_node.module else []
	return []


def _matching_deny_key(str_target: str, dict_deny: dict) -> str | None:
	"""Return the deny entry a module matches, or ``None``.

	A key without a dot matches the module's top-level package; a dotted key must match the
	module itself or be a prefix of it, so ``chassis.db_schema`` forbids the providers while
	leaving ``chassis.typing`` alone.

	Parameters
	----------
	str_target : str
		The imported module's dotted path.
	dict_deny : dict
		The layer's ``deny_layers`` map.

	Returns
	-------
	str or None
		The matching key, or ``None`` when the import is allowed.
	"""
	list_hits = [
		str_key
		for str_key in dict_deny
		if (str_target == str_key or str_target.startswith(f"{str_key}."))
		if "." in str_key or str_target.split(".")[0] == str_key
	]
	return max(list_hits, key=len) if list_hits else None


def _report_absent_policy(int_modules: int) -> int:
	"""Explain a missing policy and return the exit code it deserves.

	⚠️ A tree WITH modules and NO policy is a FAILURE, not a skip. The gate used to return 0
	in silence here, so three of the five Python tiers shipped with no import boundary at all
	while their CI stayed green — a gate reporting its own blindness as OK, which is the exact
	failure mode this repo writes gates to prevent. A tree with nothing in it is different:
	nothing to check is not the same as failing to check.

	The two causes of "no policy" are told apart because the remedies differ — an unimportable
	parser is a broken environment, an absent file is a tier nobody wrote one for.

	Parameters
	----------
	int_modules : int
		How many modules were discovered under the source root.

	Returns
	-------
	int
		``1`` when there was code to check, ``0`` when there was not.
	"""
	if int_modules == 0:
		print(f"No {_POLICY_FILE} and no modules to check — nothing to do.")
		return 0
	if yaml is None:
		print(
			"❌ PyYAML is not importable, so the layer policy cannot be read. The gate "
			"checked NOTHING. Install it (it is a declared dependency) rather than letting "
			"an unreadable policy pass for a satisfied one."
		)
	else:
		print(
			f"❌ {int_modules} module(s) under {_SRC_ROOT}/ and no {_POLICY_FILE}. "
			f"Deny-by-default cannot deny anything without a policy, so this tree has no "
			f"import boundary. Add {_POLICY_FILE} at the project root."
		)
	return 1


def main() -> int:
	"""Check every module under ``src/`` against the layer policy.

	Returns
	-------
	int
		``0`` when the tree complies (or no policy is present), ``1`` otherwise.
	"""
	path_root = pathlib.Path.cwd()
	path_src = path_root / _SRC_ROOT
	if not path_src.is_dir():
		print(f"No {_SRC_ROOT}/ directory — skipping the layer-import check.")
		return 0

	list_modules = [
		path_file
		for path_file in sorted(path_src.rglob("*.py"))
		if "__pycache__" not in path_file.parts
	]
	try:
		dict_policy = load_policy(path_root)
	except ValueError as cls_err:
		print(f"❌ {cls_err}")
		return 1
	if dict_policy is None:
		return _report_absent_policy(len(list_modules))

	int_prefix = int(dict_policy.get("src_prefix_depth", 0))

	set_first_party = first_party_roots(path_src, dict_policy)
	list_all: list[str] = []
	for path_file in list_modules:
		tuple_rel = path_file.relative_to(path_src).parts[int_prefix:]
		str_layer = resolve_layer(tuple_rel, dict_policy)
		list_all.extend(
			find_file_problems(path_file, str_layer, dict_policy, set_first_party, tuple_rel[:-1])
		)

	for str_problem in list_all:
		print(f"❌ {str_problem}")
	if list_all:
		print(f"\n{len(list_all)} layer-import violation(s).")
		return 1
	print(f"✅ layer-import policy OK ({len(list_modules)} module(s) checked).")
	return 0


if __name__ == "__main__":
	for cls_stream in (sys.stdout, sys.stderr):
		if hasattr(cls_stream, "reconfigure"):
			cls_stream.reconfigure(encoding="utf-8", errors="replace")

	sys.exit(main())
