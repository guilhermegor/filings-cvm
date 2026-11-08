"""Fail when a tag-versioned project's ``pyproject.toml`` version is not the ``0.0.0`` stub.

A project that sets ``[tool.poetry-dynamic-versioning] enable = true`` takes its published
version from the git tag, so ``[tool.poetry] version`` is only a placeholder. A hand-bump of
that placeholder contradicts the tag and the package index (filings-rfb#30: stub bumped to
``1.0.0`` while ``v1.0.1`` and ``v1.0.2`` shipped from tags).

Conditional by construction: a project without dynamic versioning enabled (the service tiers,
whose ``cz bump`` / ``release.yaml`` write a real static version, and offline-mode libraries)
is a no-op and exits 0.

``pyproject.toml`` is parsed with ``tomllib`` (stdlib).

Usage: ``python bin/check_dynamic_version_stub.py [--root DIR]``
"""

import argparse
import pathlib
import sys
import tomllib


STR_STUB = "0.0.0"
STR_DYNAMIC_SECTION = "tool.poetry-dynamic-versioning"
STR_POETRY_SECTION = "tool.poetry"


def _read_facts(str_text: str) -> tuple[bool, list[str]]:
	"""Read the gate's two facts with a real TOML parser.

	A line scan cannot see that ``[tool."poetry-dynamic-versioning"]`` and ``"enable" = true``
	are the same keys as their bare spellings, so a quoted header would disarm the gate.

	Parameters
	----------
	str_text : str
		Raw ``pyproject.toml`` contents.

	Returns
	-------
	tuple
		``(dynamic_versioning_enabled, [version, ...])``.

	Raises
	------
	tomllib.TOMLDecodeError
		When the text is not valid TOML (a broken pyproject must fail loudly, not pass).
	"""
	dict_tool = tomllib.loads(str_text).get("tool", {})
	bool_enabled = dict_tool.get("poetry-dynamic-versioning", {}).get("enable") is True
	str_version = dict_tool.get("poetry", {}).get("version")
	return bool_enabled, [str_version] if isinstance(str_version, str) else []


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
	bool_enabled, list_versions = _read_facts(str_text)
	if not bool_enabled:
		return ""
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
