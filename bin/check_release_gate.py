"""Fail a 0.x to 1.0.0 release while open issues lack the ``post-1.0`` label.

Any other version bump passes untouched. The open issues are read through the GitHub
REST API with the workflow token, read-only, and an API error fails CLOSED. The design
record lives in ``docs/releasing-1-0-0.md``.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request


STR_EXEMPT_LABEL = "post-1.0"
STR_FORM_TITLE = "Cut 1.0.0"
INT_PAGE_SIZE = 100
INT_TIMEOUT_S = 30
RE_MAJOR = re.compile(r"^v?(\d+)\.")
RE_FINAL = re.compile(r"^\d+(\.\d+)*$")


class GateError(Exception):
	"""Raised when the open-issue list cannot be read."""


def read_major(str_version: str) -> int:
	"""Return the MAJOR component of a version string.

	Parameters
	----------
	str_version : str
		Version such as ``1.2.3``, ``v0.9.0`` or ``1.0.0rc1``.

	Returns
	-------
	int
		The MAJOR number.

	Raises
	------
	ValueError
		If the string does not start with ``MAJOR.``.
	"""
	cls_match = RE_MAJOR.match(str_version.strip())
	if cls_match is None:
		raise ValueError(f"cannot read a MAJOR from version {str_version!r}")
	return int(cls_match.group(1))


def latest_final(dict_releases: dict) -> str:
	"""Return the newest final, non-yanked release from a PyPI ``releases`` map.

	Prereleases (``1.0.0rc1``) and fully yanked releases are ignored, so neither can hide
	the 0.x to 1.0.0 jump from the gate.

	Parameters
	----------
	dict_releases : dict
		The ``releases`` object of ``https://pypi.org/pypi/<name>/json``.

	Returns
	-------
	str
		The newest qualifying version, or ``0.0.0`` when there is none.
	"""
	list_ok = [
		str_ver
		for str_ver, list_files in dict_releases.items()
		if RE_FINAL.match(str_ver)
		and list_files
		and not all(dict_file.get("yanked") for dict_file in list_files)
	]
	return max(list_ok, key=lambda str_ver: tuple(map(int, str_ver.split("."))), default="0.0.0")


def previous_version(cls_args: argparse.Namespace) -> str:
	"""Return the previous version: given explicitly, else the latest final one in the PyPI JSON.

	Parameters
	----------
	cls_args : argparse.Namespace
		Parsed arguments holding ``previous_version`` or ``pypi_json``.

	Returns
	-------
	str
		The previous published version.
	"""
	if cls_args.previous_version:
		return cls_args.previous_version
	dict_pypi = json.loads(Path(cls_args.pypi_json).read_text(encoding="utf-8"))
	return latest_final(dict_pypi.get("releases") or {})


def gate_applies(str_new: str, str_previous: str) -> bool:
	"""Say whether the move from ``str_previous`` to ``str_new`` is a 0.x to 1+ jump.

	Parameters
	----------
	str_new : str
		The version being released.
	str_previous : str
		The latest version already published.

	Returns
	-------
	bool
		True when the new MAJOR is at least 1 and the previous MAJOR is 0.
	"""
	return read_major(str_new) >= 1 and read_major(str_previous) == 0


def fetch_page(str_repo: str, int_page: int) -> list[dict]:
	"""Read one page of open issues and pull requests.

	Parameters
	----------
	str_repo : str
		``owner/name``.
	int_page : int
		One-based page number.

	Returns
	-------
	list[dict]
		The decoded JSON page.

	Raises
	------
	GateError
		On any transport, HTTP or decoding failure.
	"""
	str_api = os.environ.get("GITHUB_API_URL") or "https://api.github.com"
	str_url = (
		f"{str_api}/repos/{str_repo}/issues?state=open&per_page={INT_PAGE_SIZE}&page={int_page}"
	)
	dict_headers = {
		"Accept": "application/vnd.github+json",
		"Authorization": f"Bearer {os.environ.get('GITHUB_TOKEN', '')}",
		"X-GitHub-Api-Version": "2022-11-28",
	}
	cls_request = urllib.request.Request(str_url, headers=dict_headers)  # noqa: S310
	try:
		with urllib.request.urlopen(cls_request, timeout=INT_TIMEOUT_S) as cls_response:  # noqa: S310
			list_page = json.load(cls_response)
	except (OSError, ValueError, http.client.HTTPException) as cls_error:
		raise GateError(f"cannot read open issues from {str_url}: {cls_error}") from cls_error
	if not isinstance(list_page, list) or not all(isinstance(d, dict) for d in list_page):
		raise GateError(f"unexpected response from {str_url}: {list_page!r}")
	return list_page


def filter_blocking(list_items: list[dict]) -> list[dict]:
	"""Keep the issues that block a 1.0.0 release.

	Parameters
	----------
	list_items : list[dict]
		Raw items from the issues endpoint.

	Returns
	-------
	list[dict]
		Issues that are not pull requests, not labelled ``post-1.0`` and not the
		``Cut 1.0.0`` form itself.
	"""
	return [
		dict_item
		for dict_item in list_items
		if "pull_request" not in dict_item
		and not any(
			dict_label.get("name") == STR_EXEMPT_LABEL
			for dict_label in dict_item.get("labels", [])
		)
		and str(dict_item.get("title", "")).strip() != STR_FORM_TITLE
	]


def open_blockers(str_repo: str) -> list[dict]:
	"""Collect every blocking open issue, following pagination.

	Parameters
	----------
	str_repo : str
		``owner/name``.

	Returns
	-------
	list[dict]
		The blocking issues.
	"""
	list_found: list[dict] = []
	int_page = 1
	while True:
		list_page = fetch_page(str_repo, int_page)
		list_found.extend(filter_blocking(list_page))
		if len(list_page) < INT_PAGE_SIZE:
			return list_found
		int_page += 1


def main(list_argv: list[str] | None = None) -> int:
	"""Run the gate.

	Parameters
	----------
	list_argv : list[str] | None
		Arguments; defaults to ``sys.argv[1:]``.

	Returns
	-------
	int
		0 when the release may proceed, 1 when it is blocked or the gate cannot decide.
	"""
	cls_parser = argparse.ArgumentParser(description=__doc__)
	cls_parser.add_argument("--new-version", required=True)
	cls_group = cls_parser.add_mutually_exclusive_group(required=True)
	cls_group.add_argument("--previous-version")
	cls_group.add_argument(
		"--pypi-json", help="saved PyPI JSON; the previous version is its latest final release"
	)
	cls_args = cls_parser.parse_args(list_argv)
	try:
		str_previous = previous_version(cls_args)
		if not gate_applies(cls_args.new_version, str_previous):
			print(f"1.0.0 gate not applicable: {str_previous} -> {cls_args.new_version}")
			return 0
		list_blockers = open_blockers(os.environ.get("GITHUB_REPOSITORY", ""))
	except (GateError, ValueError, OSError, AttributeError) as cls_error:
		print(f"::error::1.0.0 gate failed closed: {cls_error}", file=sys.stderr)
		return 1
	if not list_blockers:
		print("1.0.0 gate passed: every open issue is labelled post-1.0")
		return 0
	for dict_issue in list_blockers:
		str_title = (
			str(dict_issue["title"]).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
		)
		print(
			f"::error::open issue #{dict_issue['number']} blocks 1.0.0: {str_title}",
			file=sys.stderr,
		)
	print(
		f"Implement or label {len(list_blockers)} issue(s) {STR_EXEMPT_LABEL} before releasing.",
		file=sys.stderr,
	)
	return 1


if __name__ == "__main__":
	sys.exit(main())
