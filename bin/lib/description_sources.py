"""Read the project description from its manifest or from ``mkdocs.yml``.

Used by ``bin/check_description_sync.sh``. Subcommands ``manifest ROOT`` and
``mkdocs FILE`` print the description on stdout. The exit status separates an
absent source (3 for the manifest, 4 for mkdocs) from a present source that cannot
be read (5), so the caller can skip the first and fail the second.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys


try:
	import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
	import tomli as tomllib  # type: ignore[no-redef]


INT_EXIT_NO_MANIFEST = 3
INT_EXIT_NO_MKDOCS = 4
INT_EXIT_UNREADABLE = 5

RE_SITE_DESCRIPTION = re.compile(r"^site_description:\s*(.*?)\s*$", re.MULTILINE)
RE_SINGLE_QUOTED = re.compile(r"'((?:[^']|'')*)'(.*)$")


class UnreadableDescriptionError(ValueError):
	"""A description source exists but its value cannot be parsed."""


def manifest_description(path_root: Path) -> str | None:
	"""Return the description from ``pyproject.toml`` or ``package.json``.

	Parameters
	----------
	path_root : Path
		The project root.

	Returns
	-------
	str or None
			The description (empty when the key is absent), or ``None`` when neither
			manifest exists.
	"""
	path_toml = path_root / "pyproject.toml"
	path_json = path_root / "package.json"
	if path_toml.is_file():
		dict_toml = tomllib.loads(path_toml.read_text(encoding="utf-8"))
		dict_meta = dict_toml.get("project") or dict_toml.get("tool", {}).get("poetry", {})
		return str(dict_meta.get("description", ""))
	if path_json.is_file():
		return str(json.loads(path_json.read_text(encoding="utf-8")).get("description", ""))
	return None


def parse_yaml_scalar(str_raw: str) -> str:
	"""Parse one YAML scalar that may be followed by a ``#`` comment.

	Parameters
	----------
	str_raw : str
		The text after ``site_description:``, stripped.

	Returns
	-------
	str
			The scalar's value.

	Raises
	------
	UnreadableDescriptionError
		When the scalar is malformed or followed by anything but a comment.
	"""
	if str_raw.startswith('"'):
		try:
			str_value, int_end = json.JSONDecoder().raw_decode(str_raw)
		except ValueError as exc:
			raise UnreadableDescriptionError(str_raw) from exc
		str_rest = str_raw[int_end:]
	elif str_raw.startswith("'"):
		match_quoted = RE_SINGLE_QUOTED.match(str_raw)
		if match_quoted is None:
			raise UnreadableDescriptionError(str_raw)
		str_value, str_rest = match_quoted.group(1).replace("''", "'"), match_quoted.group(2)
	else:
		str_value, str_rest = str_raw.split(" #", 1)[0].rstrip(), ""
	if str_rest.strip() and not str_rest.strip().startswith("#"):
		raise UnreadableDescriptionError(str_raw)
	return str(str_value)


def mkdocs_description(path_mkdocs: Path) -> str | None:
	"""Return ``site_description`` from an ``mkdocs.yml``.

	Parameters
	----------
	path_mkdocs : Path
		The ``mkdocs.yml`` file.

	Returns
	-------
	str or None
			The description, or ``None`` when the file or the key is absent.
	"""
	if not path_mkdocs.is_file():
		return None
	match = RE_SITE_DESCRIPTION.search(path_mkdocs.read_text(encoding="utf-8"))
	return None if match is None else parse_yaml_scalar(match.group(1))


def main(list_argv: list[str]) -> int:
	"""Print the requested description and return the matching exit status.

	Parameters
	----------
	list_argv : list of str
		``["manifest", ROOT]`` or ``["mkdocs", FILE]``.

	Returns
	-------
	int
			0 when printed, 3 or 4 when the source is absent, 5 when it is unreadable.
	"""
	str_kind, str_path = list_argv
	fn_read = manifest_description if str_kind == "manifest" else mkdocs_description
	int_absent = INT_EXIT_NO_MANIFEST if str_kind == "manifest" else INT_EXIT_NO_MKDOCS
	try:
		str_value = fn_read(Path(str_path))
	except ValueError:
		return INT_EXIT_UNREADABLE
	if str_value is None:
		return int_absent
	sys.stdout.write(str_value)
	return 0


if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))
