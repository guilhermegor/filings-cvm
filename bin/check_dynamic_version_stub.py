"""Fail when a tag-versioned project's ``pyproject.toml`` version is not the ``0.0.0`` stub.

A project that sets ``[tool.poetry-dynamic-versioning] enable = true`` takes its published
version from the git tag, so ``[tool.poetry] version`` is only a placeholder. A hand-bump of
that placeholder contradicts the tag and the package index (filings-rfb#30: stub bumped to
``1.0.0`` while ``v1.0.1`` and ``v1.0.2`` shipped from tags).

Conditional by construction: a project without dynamic versioning enabled (the service tiers,
whose ``cz bump`` / ``release.yaml`` write a real static version, and offline-mode libraries)
is a no-op and exits 0.

``pyproject.toml`` is read line by line rather than through ``tomllib``: the templates target
Python 3.10, which has no ``tomllib``, and ``tomli`` is not a direct dependency.

Usage: ``python bin/check_dynamic_version_stub.py [--root DIR]``
"""

import argparse
import pathlib
import re
import sys


STR_STUB = "0.0.0"
STR_DYNAMIC_SECTION = "tool.poetry-dynamic-versioning"
STR_POETRY_SECTION = "tool.poetry"

RE_SECTION = re.compile(r"^\s*\[([^\[\]]+)\]\s*(?:#.*)?$")
RE_ENABLE = re.compile(r"^\s*enable\s*=\s*true\s*(?:#.*)?$")
RE_VERSION = re.compile(r"""^\s*version\s*=\s*["']([^"']*)["']\s*(?:#.*)?$""")


def read_key_lines(str_text: str) -> dict:
	"""Group the lines of a TOML document by their ``[section]`` header.

	Parameters
	----------
	str_text : str
		Raw ``pyproject.toml`` contents.

	Returns
	-------
	dict
		Section name to the list of lines under it (the preamble is keyed ``""``).
	"""
	dict_sections: dict = {"": []}
	str_current = ""
	for str_line in str_text.splitlines():
		re_match = RE_SECTION.match(str_line)
		if re_match:
			str_current = re_match.group(1).strip()
			dict_sections.setdefault(str_current, [])
		else:
			dict_sections[str_current].append(str_line)
	return dict_sections


def find_problem(str_text: str) -> str:
	"""Return the gate's finding for one ``pyproject.toml``, or ``""`` when it is clean.

	Parameters
	----------
	str_text : str
		Raw ``pyproject.toml`` contents.

	Returns
	-------
	str
		A finding message, empty when the project is a no-op or carries the stub.
	"""
	dict_sections = read_key_lines(str_text)
	list_dynamic = dict_sections.get(STR_DYNAMIC_SECTION, [])
	if not any(RE_ENABLE.match(str_line) for str_line in list_dynamic):
		return ""
	list_versions = [
		re_match.group(1)
		for re_match in map(RE_VERSION.match, dict_sections.get(STR_POETRY_SECTION, []))
		if re_match
	]
	if list_versions == [STR_STUB]:
		return ""
	str_found = list_versions[0] if list_versions else "<missing>"
	return (
		f"[{STR_POETRY_SECTION}] version is {str_found!r} but "
		f"[{STR_DYNAMIC_SECTION}] is enabled: the version comes from the git tag, so it must "
		f"stay {STR_STUB!r}. Revert the hand-bump; see docs/contributing.md#releasing."
	)


def main(list_argv: list) -> int:
	"""Run the gate against ``<root>/pyproject.toml``.

	Parameters
	----------
	list_argv : list of str
		Arguments after the program name; only ``--root DIR`` is accepted.

	Returns
	-------
	int
		0 when clean or not applicable, 1 on a finding (argparse exits 2 on bad usage).
	"""
	cls_parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
	cls_parser.add_argument("--root", default=".", help="project root holding pyproject.toml")
	path_root = pathlib.Path(cls_parser.parse_args(list_argv).root)
	path_pyproject = path_root / "pyproject.toml"
	if not path_pyproject.is_file():
		print(f"{path_pyproject} not found; nothing to check")
		return 0
	str_problem = find_problem(path_pyproject.read_text(encoding="utf-8"))
	if str_problem:
		print(f"{path_pyproject}: {str_problem}")
		return 1
	print("dynamic version stub OK")
	return 0


if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))
