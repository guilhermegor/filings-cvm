"""Enforce that ``.coveragerc``'s ``omit`` list never swallows a section's real logic.

Vendored from BlueprintX ``python-common`` and adapted to this library's layout. ``fail_under``
in ``.coveragerc`` is the coverage floor; it is only honest if the ``omit`` list beside it is
accurate — and ``omit`` is a hand-declared list nobody can contradict. Widen one glob (turn
``src/*/_internal/*`` into ``src/*``) and every reader drops out of the denominator:
``fail_under`` still reads 80, the suite is still green, and the code is no longer measured.

The template derives its floor from ``src/capabilities/*/{domain,application}``; this repo has
no capabilities. Its equivalent is the two public sections, ``ingestion/`` and ``submission/``
(the root ``CLAUDE.md``: "every solution lives in one of them"). ``_internal/`` is the one
declared, deliberate exclusion. The floor is CODE-derived: every module under a section that
defines at least one function (read via ``ast``) must stay in the denominator. Any such module
matched by an ``omit`` pattern is a finding.

Discovery matching zero modules is a FAILURE, not a pass: a gate that scanned nothing also
found nothing wrong, and exits 0 forever the day a path is renamed.
"""

import ast
import configparser
import fnmatch
import os
import pathlib
import sys


_COVERAGERC = pathlib.Path(".coveragerc")
_SRC = pathlib.Path("src")
_SECTIONS = ("ingestion", "submission")


def omit_patterns(path_coveragerc: pathlib.Path) -> list[str]:
	"""Return the ``[run] omit`` glob patterns declared in ``.coveragerc``.

	Parameters
	----------
	path_coveragerc : pathlib.Path
		The coverage config to read.

	Returns
	-------
	list of str
		One pattern per non-blank line, in declaration order.
	"""
	cls_parser = configparser.ConfigParser()
	cls_parser.read(path_coveragerc, encoding="utf-8")
	str_raw = cls_parser.get("run", "omit", fallback="")
	return [
		os.path.expandvars(str_line.strip())
		for str_line in str_raw.splitlines()
		if str_line.strip()
	]


def defines_a_function(path_module: pathlib.Path) -> bool:
	"""Return whether a module defines a function or method anywhere in its AST.

	Parameters
	----------
	path_module : pathlib.Path
		The module to inspect.

	Returns
	-------
	bool
		``True`` when the module defines at least one function or method.
	"""
	cls_tree = ast.parse(path_module.read_text(encoding="utf-8"))
	return any(
		isinstance(cls_node, ast.FunctionDef | ast.AsyncFunctionDef)
		for cls_node in ast.walk(cls_tree)
	)


def must_stay_covered(path_src: pathlib.Path) -> list[pathlib.Path]:
	"""Return every section module that defines real behavior.

	Parameters
	----------
	path_src : pathlib.Path
		``src/``; each package under it is searched for the two sections.

	Returns
	-------
	list of pathlib.Path
		Modules under ``<package>/ingestion`` or ``<package>/submission`` defining a function.
	"""
	return [
		path_module
		for str_section in _SECTIONS
		for path_module in sorted(path_src.glob(f"*/{str_section}/**/*.py"))
		if defines_a_function(path_module)
	]


def swallowed_by_omit(
	list_must_stay_covered: list[pathlib.Path], list_patterns: list[str]
) -> list[str]:
	"""Return one message per module the omit list excludes despite defining real behavior.

	Parameters
	----------
	list_must_stay_covered : list of pathlib.Path
		The code-derived floor: modules that must stay in the coverage denominator.
	list_patterns : list of str
		The declared ``omit`` patterns.

	Returns
	-------
	list of str
		Human-readable problems; empty when none are swallowed.
	"""
	list_problems = []
	for path_module in list_must_stay_covered:
		str_posix = path_module.as_posix()
		str_absolute = path_module.resolve().as_posix()
		list_matched = [
			str_pattern
			for str_pattern in list_patterns
			if fnmatch.fnmatch(str_posix, str_pattern)
			or fnmatch.fnmatch(str_absolute, str_pattern)
		]
		if list_matched:
			list_problems.append(
				f"{str_posix}: defines a function but is matched by omit pattern "
				f"'{list_matched[0]}' — dropped out of the coverage floor's denominator"
			)
	return list_problems


def main() -> int:
	"""Run the gate against the current working directory's ``.coveragerc`` and ``src/``.

	Returns
	-------
	int
		``0`` when no logic-bearing module is silently omitted, ``1`` otherwise.
	"""
	if not _COVERAGERC.is_file():
		print(f"check_coverage_floor: {_COVERAGERC} not found", file=sys.stderr)
		return 1
	list_must_stay_covered = must_stay_covered(_SRC)
	if not list_must_stay_covered:
		print(
			f"check_coverage_floor: found ZERO logic-bearing modules under "
			f"{_SRC}/*/{{{','.join(_SECTIONS)}}} — refusing to report success.",
			file=sys.stderr,
		)
		return 1

	list_problems = swallowed_by_omit(list_must_stay_covered, omit_patterns(_COVERAGERC))
	for str_problem in list_problems:
		print(f"❌ {str_problem}", file=sys.stderr)
	if list_problems:
		print(
			f"\n{len(list_problems)} problem(s). Scope the omit pattern to what needs it "
			f"(today only `_internal/` is deliberately excluded).",
			file=sys.stderr,
		)
		return 1

	print(
		f"coverage floor OK: {len(list_must_stay_covered)} ingestion/submission module(s) "
		f"stay in the coverage denominator."
	)
	return 0


if __name__ == "__main__":
	for cls_stream in (sys.stdout, sys.stderr):
		if hasattr(cls_stream, "reconfigure"):
			cls_stream.reconfigure(encoding="utf-8", errors="replace")
	sys.exit(main())
