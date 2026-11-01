"""Fail when a required status check is not emitted by a job that runs on every PR.

Vendored from BlueprintX's ``bin/ci/check_required_checks_sync.py``, trimmed to its
generated-project mode (``--required-list``) — the JSON/policy/``--live`` modes target
BlueprintX's own repository and are not carried. Adapted in one place: a ``pull_request``
``branches:`` filter that names the protected branch (``main``) is NOT a filter for this
purpose, because the ruleset only ever evaluates PRs whose base is ``main``.

A required context that no unconditional PR job emits leaves every PR "Expected — waiting"
forever; it is the drift that appears silently when a job is renamed, a matrix value
changes, or a job gains an ``if:``. ``bin/required-checks.txt`` mirrors the ruleset on
``main``; this gate never reads or changes the live settings.
"""

import argparse
import itertools
import pathlib
import re
import sys

import yaml


PR_TYPES = {"opened", "reopened", "synchronize"}
PROTECTED_BRANCH = "main"
FILTERS = ("branches", "branches-ignore", "paths", "paths-ignore")
RE_EVENT_CLAUSE = re.compile(r"^github\.event_name\s*(==|!=)\s*'([a-z_]+)'$")


class UnsupportedError(Exception):
	"""A workflow shape this gate cannot expand; reported per workflow, never fatal."""


def event_clause_true(str_clause: str) -> bool:
	"""Return whether a bare ``github.event_name ==/!= 'x'`` clause holds on a PR.

	Parameters
	----------
	str_clause : str
		One ``||`` alternative of a job's ``if:``.

	Returns
	-------
	bool
		``True`` only for a clause that is provably true on ``pull_request``.
	"""
	match = RE_EVENT_CLAUSE.match(str_clause.strip())
	if not match:
		return False
	return (match.group(2) == "pull_request") == (match.group(1) == "==")


def if_always_true(str_if: object) -> bool:
	"""Return whether a job ``if:`` holds on a pull_request (a true ``||`` alternative).

	Parameters
	----------
	str_if : object
		The job's ``if:`` value, ``None`` when absent.

	Returns
	-------
	bool
		``True`` when the job runs on every PR.
	"""
	if str_if is None:
		return True
	str_expr = re.sub(r"^\$\{\{\s*(.*?)\s*\}\}$", r"\1", str(str_if).strip(), flags=re.S)
	return any(event_clause_true(c) for c in str_expr.split("||"))


def as_event_map(dict_on: object) -> dict:
	"""Normalise a workflow ``on:`` (string, list or mapping) to a mapping.

	Parameters
	----------
	dict_on : object
		The parsed ``on:`` value.

	Returns
	-------
	dict
		Event name -> its config (``None`` when bare).
	"""
	if isinstance(dict_on, str):
		return {dict_on: None}
	if isinstance(dict_on, list):
		return dict.fromkeys(dict_on)
	return dict_on if isinstance(dict_on, dict) else {}


def event_unfiltered(dict_event: dict | None) -> bool:
	"""Return whether one event's config runs on every PR to ``main``.

	Parameters
	----------
	dict_event : dict or None
		The ``pull_request`` config.

	Returns
	-------
	bool
		``True`` with no narrowing filter and ``types:`` covering new pushes.
	"""
	dict_event = dict_event or {}
	list_filters = [k for k in FILTERS if k in dict_event]
	if list_filters == ["branches"] and PROTECTED_BRANCH in (dict_event["branches"] or []):
		list_filters = []
	if list_filters:
		return False
	list_types = dict_event.get("types")
	if list_types is None:
		return True
	list_types = [list_types] if isinstance(list_types, str) else list_types
	return set(list_types) >= PR_TYPES


def matrix_text(value: object) -> str:
	"""Render a matrix value as GitHub renders it (booleans lowercase).

	Parameters
	----------
	value : object
		One matrix value.

	Returns
	-------
	str
		The rendered value.
	"""
	return str(value).lower() if isinstance(value, bool) else str(value)


def expand_name(str_name: str, dict_job: dict) -> list:
	"""Return a job's check names; interpolates ``${{ matrix.k }}`` or appends ``(v1, v2)``.

	Parameters
	----------
	str_name : str
		The job's ``name:`` (or id).
	dict_job : dict
		The job mapping.

	Returns
	-------
	list of str
		Every check name the job emits.

	Raises
	------
	UnsupportedError
		On a matrix shape that cannot be expanded statically.
	"""
	dict_strategy = dict_job.get("strategy") or {}
	dict_matrix = dict_strategy.get("matrix") if isinstance(dict_strategy, dict) else None
	if dict_matrix is None:
		return [str_name]
	if not isinstance(dict_matrix, dict):
		raise UnsupportedError(f"job '{str_name}': dynamic matrix (fromJSON) is not expandable")
	if "include" in dict_matrix or "exclude" in dict_matrix:
		raise UnsupportedError(f"job '{str_name}': matrix include/exclude is not expandable")
	list_keys = list(dict_matrix)
	if not all(isinstance(dict_matrix[k], list) for k in list_keys):
		raise UnsupportedError(f"job '{str_name}': a non-list matrix dimension is not expandable")
	list_combos = list(itertools.product(*(dict_matrix[k] for k in list_keys)))
	if "matrix." not in str_name:
		return [f"{str_name} ({', '.join(matrix_text(v) for v in t)})" for t in list_combos]
	list_names = []
	for tuple_vals in list_combos:
		str_out = str_name
		for str_key, str_val in zip(list_keys, tuple_vals, strict=True):
			str_out = re.sub(
				r"\$\{\{\s*matrix\.%s\s*\}\}".replace("%s", re.escape(str_key)),
				matrix_text(str_val),
				str_out,
			)
		list_names.append(str_out)
	return list_names


def job_flags(dict_job_map: dict, bool_wf: bool) -> dict:
	"""Return ``{job id: unconditional}``; a job that ``needs`` a conditional job is conditional.

	Parameters
	----------
	dict_job_map : dict
		The workflow's ``jobs:``.
	bool_wf : bool
		Whether the workflow itself triggers on every PR.

	Returns
	-------
	dict
		Job id -> runs on every PR.

	Raises
	------
	UnsupportedError
		On a reusable-workflow job, whose emitted names are not knowable here.
	"""
	dict_flag = {}
	for str_id, dict_job in dict_job_map.items():
		if "uses" in dict_job:
			raise UnsupportedError(f"reusable-workflow job '{str_id}' is unsupported")
		dict_flag[str_id] = bool_wf and if_always_true(dict_job.get("if"))
	bool_changed = True
	while bool_changed:
		bool_changed = False
		for str_id, dict_job in dict_job_map.items():
			list_needs = dict_job.get("needs") or []
			list_needs = [list_needs] if isinstance(list_needs, str) else list_needs
			if dict_flag[str_id] and not all(dict_flag.get(n, False) for n in list_needs):
				dict_flag[str_id] = False
				bool_changed = True
	return dict_flag


def pr_jobs(path_dir: pathlib.Path) -> tuple:
	"""Return ``({emitted name: unconditional on every PR}, [per-workflow problems])``.

	Parameters
	----------
	path_dir : pathlib.Path
		The workflows directory.

	Returns
	-------
	tuple
		The name map and the list of unsupported-shape problems.
	"""
	dict_jobs, list_problems = {}, []
	for path_file in sorted(path_dir.glob("*.y*ml")):
		dict_wf = yaml.safe_load(path_file.read_text(encoding="utf-8")) or {}
		dict_on = as_event_map(dict_wf.get("on", dict_wf.get(True)))
		if not {"pull_request", "pull_request_target"} & set(dict_on):
			continue
		bool_wf = "pull_request" in dict_on and event_unfiltered(dict_on["pull_request"])
		dict_job_map = dict_wf.get("jobs") or {}
		try:
			dict_flag = job_flags(dict_job_map, bool_wf)
			for str_id, dict_job in dict_job_map.items():
				for str_name in expand_name(str(dict_job.get("name", str_id)), dict_job):
					dict_jobs[str_name] = dict_jobs.get(str_name, False) or dict_flag[str_id]
		except UnsupportedError as exc:
			list_problems.append(f"{path_file.name}: {exc}")
	return dict_jobs, list_problems


def read_required(path_list: pathlib.Path) -> set:
	"""Return the required contexts listed one per line (``#`` comments skipped).

	Parameters
	----------
	path_list : pathlib.Path
		``bin/required-checks.txt``.

	Returns
	-------
	set of str
		The required contexts.
	"""
	list_lines = path_list.read_text(encoding="utf-8").splitlines()
	return {s.strip() for s in list_lines if s.strip() and not s.lstrip().startswith("#")}


def main() -> int:
	"""Compare the required list with the unconditional PR jobs.

	Returns
	-------
	int
		0 in sync, 1 on any finding (including an empty required list).
	"""
	parser = argparse.ArgumentParser()
	parser.add_argument("--workflows", default=".github/workflows")
	parser.add_argument("--required-list", default="bin/required-checks.txt")
	args = parser.parse_args()
	set_req = read_required(pathlib.Path(args.required_list))
	if not set_req:
		print(f"::error::{args.required_list} lists no check — refusing to pass vacuously")
		return 1
	dict_jobs, list_err = pr_jobs(pathlib.Path(args.workflows))
	set_always = {n for n, bool_flag in dict_jobs.items() if bool_flag}
	list_err += [
		f"required but no unconditional PR job emits it: {n}" for n in sorted(set_req - set_always)
	]
	for str_msg in list_err:
		print(f"::error::{str_msg}", file=sys.stderr)
	print(f"required-checks sync: {len(set_req)} required, findings={len(list_err)}")
	return 1 if list_err else 0


if __name__ == "__main__":
	sys.exit(main())
