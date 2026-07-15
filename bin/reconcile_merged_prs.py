#!/usr/bin/env python
"""Reconcile the board after a PR merges — close its linked issues, delete its branch.

GitHub normally does this itself: merging a PR whose body says ``Closes #N`` closes ``#N`` and,
with ``delete_branch_on_merge``, removes the head branch. **Neither fires when the merge is done by
the ``GITHUB_TOKEN`` bot** — the same family as "events triggered by the
``GITHUB_TOKEN`` do not create new workflow runs". Since ``bin/pr_gate.py`` arms native auto-merge
with ``github.token``, every ``ci``/``deps``/``docs`` PR merges **as the bot**, so its
linked issues stay open and its branch survives (seen on #103/#102 and #106/#105). The kanban
card then freezes in "In review" forever, because the native "closed → Done" workflow keys on the
*issue* closing, which never happens.

This script closes that gap idempotently:

* **Event path** — ``on: pull_request: [closed]`` sets ``PR_NUMBER``; reconcile it. This is
  immediate, but is itself subject to the same suppression: a run may not start for a bot merge.
* **Sweep path** — the ``schedule`` / ``workflow_dispatch`` triggers set no ``PR_NUMBER``; walk the
  recently-merged PRs and reconcile each. ``schedule`` is **exempt** from the ``GITHUB_TOKEN``
  suppression, so this path is the *guaranteed* backstop — it runs whether or not the event did.

Everything is idempotent: an already-closed issue is skipped (only ``OPEN`` linked issues are
closed), and deleting an absent branch is treated as a no-op. Pure decision logic lives in
module-level functions (unit-tested, no network); every GitHub call is confined to the thin
``_api``/``_graphql`` seam and the helpers that call them.

**Language.** Machine/maintainer-facing surface — English, like ``bin/pr_gate.py`` and every other
CI output here. Only the published docs follow the site's pt-BR.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
import sys
from typing import Any
import urllib.error
import urllib.request


# GitHub API host. Kept host-only (no path) as its own constant so no full, *fetchable* URL
# literal ever appears in source — the `check-urls` pre-commit hook fetches every non-host-only URL
# it finds and fails on the 403/404 that `…/graphql` and `…/repos/` return. Paths are concatenated.
_GH_API = "https://api.github.com"

# How many of the most-recently-updated closed PRs the sweep inspects per run. The daily cadence
# means only a handful can have merged since the last run; 50 is generous slack for a burst.
_SWEEP_PER_PAGE = 50

# The REST endpoint does not expose a PR's linked issues, so this one query carries both the
# reconcile inputs (merged?, head branch, fork?, linked issues + their state) and the repo default
# branch (the branch we must never delete).
_PR_QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef { name }
    pullRequest(number: $number) {
      merged
      headRefName
      isCrossRepository
      closingIssuesReferences(first: 50) { nodes { number state } }
    }
  }
}
"""


def issues_to_close(list_refs: list[dict]) -> list[int]:
	"""Return the numbers of the linked issues that are still open.

	A merged PR may link issues that a human already closed by hand (the manual chore this script
	retires), or that were deliberately re-opened after the merge. Only the ``OPEN`` ones are acted
	on, so re-closing is never forced on an issue someone reopened.

	Parameters
	----------
	list_refs : list of dict
		``closingIssuesReferences.nodes`` — each ``{"number": int, "state": "OPEN"|"CLOSED"}``.

	Returns
	-------
	list of int
		Issue numbers whose state is ``OPEN``, in the order given.
	"""
	return [dict_ref["number"] for dict_ref in list_refs if dict_ref["state"] == "OPEN"]


def branch_to_delete(dict_pr: dict, str_default_branch: str) -> str | None:
	"""Decide whether a merged PR's head branch should be deleted, and which.

	Guard clauses first: an unmerged PR keeps its branch; a **fork** branch is not ours to touch;
	and the repository's default branch is never a deletion target even if a PR points at it.

	Parameters
	----------
	dict_pr : dict
		The ``pullRequest`` node — ``merged``, ``isCrossRepository``, ``headRefName``.
	str_default_branch : str
		The repository's default branch name, which must never be deleted.

	Returns
	-------
	str or None
		The head branch name to delete, or ``None`` when nothing should be deleted.
	"""
	if not dict_pr["merged"]:
		return None
	if dict_pr["isCrossRepository"]:
		return None
	str_ref = dict_pr["headRefName"]
	if str_ref == str_default_branch:
		return None
	return str_ref


def recently_merged_numbers(list_prs: list[dict], dt_now: datetime, int_days: int) -> list[int]:
	"""Filter a closed-PR listing down to those merged within the trailing window.

	Bounding the sweep to a recent window keeps every run cheap and, more importantly, keeps this
	janitor from re-closing an issue reopened long after its PR merged: only PRs merged
	in the last ``int_days`` are eligible.

	Parameters
	----------
	list_prs : list of dict
		Closed pull requests from the REST list endpoint; each carries ``number`` and ``merged_at``
		(``None`` for a PR that was closed without merging).
	dt_now : datetime
		The tz-aware reference "now".
	int_days : int
		Trailing window size in days.

	Returns
	-------
	list of int
		PR numbers merged at or after ``dt_now - int_days``.
	"""
	dt_floor = dt_now - timedelta(days=int_days)
	list_out: list[int] = []
	for dict_pr in list_prs:
		str_merged = dict_pr.get("merged_at")
		if str_merged is None:
			continue
		dt_merged = datetime.fromisoformat(str_merged.replace("Z", "+00:00"))
		if dt_merged >= dt_floor:
			list_out.append(dict_pr["number"])
	return list_out


def _api(str_method: str, str_url: str, dict_body: dict | None = None) -> Any:  # noqa: ANN401
	"""Call the GitHub API with the workflow token and decode the JSON reply.

	No retry loop, on purpose: this is an idempotent janitor whose ``schedule`` trigger *is* the
	retry — a transient failure today is simply reconciled tomorrow, and the sweep already skips a
	PR whose reconcile raises. The return is ``Any`` because this is a JSON boundary (an object
	here, an array there); narrowing would only force casts at every call site.

	Parameters
	----------
	str_method : str
		HTTP method.
	str_url : str
		Absolute API URL.
	dict_body : dict, optional
		JSON payload, when the method takes one.

	Returns
	-------
	Any
		The decoded response (an empty dict for a 204).
	"""
	bytes_body = json.dumps(dict_body).encode() if dict_body is not None else None
	cls_req = urllib.request.Request(str_url, data=bytes_body, method=str_method)  # noqa: S310
	cls_req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
	cls_req.add_header("Accept", "application/vnd.github+json")
	if bytes_body is not None:
		cls_req.add_header("Content-Type", "application/json")
	with urllib.request.urlopen(cls_req) as cls_resp:  # noqa: S310
		bytes_out = cls_resp.read()
	return json.loads(bytes_out) if bytes_out else {}


def _graphql(str_query: str, dict_vars: dict) -> dict:
	"""Run a GraphQL query and return its ``data`` block, raising on any GraphQL-level error.

	Parameters
	----------
	str_query : str
		The GraphQL document.
	dict_vars : dict
		Its variables.

	Returns
	-------
	dict
		The ``data`` object.

	Raises
	------
	OSError
		If the response carries an ``errors`` array (GraphQL returns HTTP 200 for these).
	"""
	dict_resp = _api(
		"POST",
		f"{_GH_API}/graphql",
		{"query": str_query, "variables": dict_vars},
	)
	if "errors" in dict_resp:
		raise OSError(f"GraphQL error: {dict_resp['errors']}")
	return dict_resp["data"]


def _delete_branch(str_api: str, str_branch: str) -> None:
	"""Delete a branch ref, treating an already-gone branch as success.

	Parameters
	----------
	str_api : str
		The ``.../repos/{owner}/{name}`` API base.
	str_branch : str
		The branch name (no ``refs/heads/`` prefix).
	"""
	try:
		_api("DELETE", f"{str_api}/git/refs/heads/{str_branch}")
	except urllib.error.HTTPError as cls_exc:
		if cls_exc.code not in (404, 422):
			raise
		print(f"branch {str_branch} already gone ({cls_exc.code})", file=sys.stderr)


def reconcile_pr(
	str_api: str, str_owner: str, str_name: str, int_pr: int
) -> tuple[list[int], str | None]:
	"""Close a merged PR's still-open linked issues and delete its head branch.

	A no-op for an unmerged PR. Returns what it actually did so the caller can log only the PRs
	that needed reconciling.

	Parameters
	----------
	str_api : str
		The ``.../repos/{owner}/{name}`` API base.
	str_owner, str_name : str
		Repository owner and name (for the GraphQL query).
	int_pr : int
		The pull request number.

	Returns
	-------
	tuple of (list of int, str or None)
		The issue numbers closed, and the branch deleted (or ``None``).
	"""
	dict_repo = _graphql(_PR_QUERY, {"owner": str_owner, "name": str_name, "number": int_pr})[
		"repository"
	]
	dict_pr = dict_repo["pullRequest"]
	if dict_pr is None or not dict_pr["merged"]:
		return [], None

	list_closed: list[int] = []
	for int_num in issues_to_close(dict_pr["closingIssuesReferences"]["nodes"]):
		_api(
			"PATCH",
			f"{str_api}/issues/{int_num}",
			{"state": "closed", "state_reason": "completed"},
		)
		list_closed.append(int_num)

	str_branch = branch_to_delete(dict_pr, dict_repo["defaultBranchRef"]["name"])
	if str_branch is not None:
		_delete_branch(str_api, str_branch)
	return list_closed, str_branch


def main() -> int:
	"""Reconcile one PR (event path) or every recently-merged PR (sweep path).

	The trigger decides the mode: ``pull_request: closed`` sets ``PR_NUMBER`` → reconcile that PR;
	``schedule``/``workflow_dispatch`` leave it empty → sweep the trailing window. In the sweep, a
	single PR's failure is logged and skipped so one bad PR never sinks the whole run.

	Returns
	-------
	int
		Process exit code (0 unless the single-PR event path itself raises).
	"""
	str_repo = os.environ["GITHUB_REPOSITORY"]
	str_owner, str_name = str_repo.split("/", 1)
	str_api = f"{_GH_API}/repos/{str_repo}"

	str_pr = os.environ.get("PR_NUMBER", "").strip()
	if str_pr:
		list_closed, str_branch = reconcile_pr(str_api, str_owner, str_name, int(str_pr))
		print(f"pr={str_pr} closed_issues={list_closed} deleted_branch={str_branch}")
		return 0

	int_days = int(os.environ.get("SWEEP_DAYS", "7"))
	list_prs = _api(
		"GET",
		f"{str_api}/pulls?state=closed&sort=updated&direction=desc&per_page={_SWEEP_PER_PAGE}",
	)
	list_numbers = recently_merged_numbers(list_prs, datetime.now(timezone.utc), int_days)
	for int_num in list_numbers:
		try:
			list_closed, str_branch = reconcile_pr(str_api, str_owner, str_name, int_num)
		except (urllib.error.HTTPError, urllib.error.URLError, OSError) as cls_exc:
			print(f"pr={int_num} reconcile failed (skipped): {cls_exc}", file=sys.stderr)
			continue
		if list_closed or str_branch is not None:
			print(f"pr={int_num} closed_issues={list_closed} deleted_branch={str_branch}")
	print(f"swept {len(list_numbers)} merged PR(s) from the last {int_days} day(s)")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
