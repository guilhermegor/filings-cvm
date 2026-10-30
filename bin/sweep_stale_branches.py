#!/usr/bin/env python
"""Weekly per-BRANCH sweep — delete remote branches whose PR already merged (backstop, #230).

``bin/reconcile_merged_prs.py`` is the primary line: it walks recently-merged **PRs**
(7-day window, 50 per page). A branch whose PR merged more than 7 days ago without being
reconciled is never seen again (the scheduled workflow was auto-disabled after 60 idle days,
the sweep failed for a week, a burst of >50 PRs). This script fails for a *different* reason:
it walks the real list of remote **branches** and asks "should this branch that EXISTS still
exist?".

**The criterion is the PR's ``state == MERGED`` for that head branch — never ancestry.** This repo
squash-merges, so a merged branch's commits are never ancestors of ``main``: ``git branch -d``,
``git log main..branch`` and ``git cherry`` all say "unmerged" for every branch, and an
ancestry-based sweep would exit green forever while deleting nothing.

Safety, in order of precedence (all unit-tested):

* the default branch and ``gh-pages`` are never deleted;
* a branch with **any** ``OPEN`` PR is never deleted, even if an older PR of it merged (it was
  reused);
* the base of an open PR is never deleted: GitHub would close that PR;
* a branch with no PR, or only ``CLOSED`` (unmerged) PRs, is work in progress — kept;
* a merged PR only counts when its head is still the branch tip: commits pushed after the
  merge never reached ``main``, and deleting the branch would lose them;
* deletion needs ``SWEEP_DRY_RUN`` to be explicitly false; the default is **dry run**.

The run always reports how many branches it examined, so a sweep that can delete nothing says so
instead of exiting silently.

**Language.** Machine/maintainer-facing surface — English, like ``bin/reconcile_merged_prs.py``.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any
import urllib.error
import urllib.parse
import urllib.request


# Host-only on purpose (see bin/reconcile_merged_prs.py): no fetchable URL literal in source.
_GH_API = "https://api.github.com"

_PER_PAGE = 100

_TIMEOUT_S = 30

# Branches that are never sweep targets, whatever their PRs say.
_PROTECTED = frozenset({"main", "gh-pages"})


def branch_verdict(list_pr_states: list[str]) -> str:
	"""Classify one branch from the states of the PRs that use it as head.

	Parameters
	----------
	list_pr_states : list of str
		``state`` of every PR with this head branch, as ``OPEN``, ``CLOSED`` or ``MERGED``
		(upper-cased here, so REST's lowercase ``open``/``closed`` is not a trap).

	Returns
	-------
	str
		``"delete"`` only when some PR merged and none is open; otherwise ``"keep-open-pr"``,
		``"keep-no-merged-pr"`` (no PR, or only closed-unmerged ones).
	"""
	set_states = {str_state.upper() for str_state in list_pr_states}
	if "OPEN" in set_states:
		return "keep-open-pr"
	if "MERGED" in set_states:
		return "delete"
	return "keep-no-merged-pr"


def branches_to_delete(
	dict_states_by_branch: dict[str, list[str]], str_default_branch: str
) -> list[str]:
	"""Pick the branches to delete, in the order given.

	Parameters
	----------
	dict_states_by_branch : dict
		Every remote branch name mapped to the states of its PRs.
	str_default_branch : str
		The repository default branch, never deleted.

	Returns
	-------
	list of str
		Branch names whose verdict is ``delete`` and that are not protected.
	"""
	set_protected = _PROTECTED | {str_default_branch}
	return [
		str_branch
		for str_branch, list_states in dict_states_by_branch.items()
		if str_branch not in set_protected and branch_verdict(list_states) == "delete"
	]


def is_dry_run(str_raw: str | None) -> bool:
	"""Return whether deletion is disabled; anything but an explicit false means dry run.

	Parameters
	----------
	str_raw : str or None
		The ``SWEEP_DRY_RUN`` value.

	Returns
	-------
	bool
		``False`` only for ``false``/``0``/``no`` (case-insensitive).
	"""
	return (str_raw or "true").strip().lower() not in ("false", "0", "no")


def _api(str_method: str, str_url: str) -> Any:  # noqa: ANN401
	"""Call the GitHub API with the workflow token and decode the JSON reply.

	Parameters
	----------
	str_method : str
		HTTP method.
	str_url : str
		Absolute API URL.

	Returns
	-------
	Any
		The decoded response (an empty dict for a 204); ``Any`` because it is a JSON boundary.
	"""
	cls_req = urllib.request.Request(str_url, method=str_method)  # noqa: S310
	cls_req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
	cls_req.add_header("Accept", "application/vnd.github+json")
	with urllib.request.urlopen(cls_req, timeout=_TIMEOUT_S) as cls_resp:  # noqa: S310
		bytes_out = cls_resp.read()
	return json.loads(bytes_out) if bytes_out else {}


def _paged(str_url: str) -> list[Any]:
	"""Collect every page of a list endpoint.

	Parameters
	----------
	str_url : str
		Absolute API URL ending in ``?`` or ``&``, ready for the paging parameters.

	Returns
	-------
	list
		The items of all pages; ``Any`` because it is a JSON boundary.
	"""
	list_items: list[Any] = []
	int_page = 1
	while True:
		list_page = _api("GET", f"{str_url}per_page={_PER_PAGE}&page={int_page}")
		list_items.extend(list_page)
		if len(list_page) < _PER_PAGE:
			return list_items
		int_page += 1


def _list_branches(str_api: str) -> dict[str, str]:
	"""Return every remote branch name mapped to its tip SHA.

	Parameters
	----------
	str_api : str
		The ``.../repos/{owner}/{name}`` API base.

	Returns
	-------
	dict
		Branch name to tip commit SHA.
	"""
	return {dict_b["name"]: dict_b["commit"]["sha"] for dict_b in _paged(f"{str_api}/branches?")}


def _open_pr_bases(str_api: str) -> set[str]:
	"""Return the base branches of every open PR.

	Not caught by the caller: without this list no deletion is safe, so a failed read ends the
	run before anything is deleted.

	Parameters
	----------
	str_api : str
		The ``.../repos/{owner}/{name}`` API base.

	Returns
	-------
	set of str
		Branch names that an open PR targets.
	"""
	return {dict_pr["base"]["ref"] for dict_pr in _paged(f"{str_api}/pulls?state=open&")}


def _pr_states(str_api: str, str_owner: str, str_branch: str, str_tip: str) -> list[str]:
	"""Return the states of every same-repo PR whose head is the branch.

	``head=owner:branch`` restricts to this repo's own branches, so a fork PR that happens to
	share the branch name is not counted as evidence. ``merged_at`` distinguishes MERGED from
	CLOSED, since REST reports both as ``closed``. A merged PR whose head is not the branch tip
	counts as ``CLOSED``: the tip holds commits that PR never carried.

	Parameters
	----------
	str_api : str
		The ``.../repos/{owner}/{name}`` API base.
	str_owner : str
		Repository owner.
	str_branch : str
		The branch name.
	str_tip : str
		The branch tip commit SHA.

	Returns
	-------
	list of str
		``OPEN``/``MERGED``/``CLOSED`` per PR.
	"""
	str_head = urllib.parse.quote(f"{str_owner}:{str_branch}", safe="")
	list_prs = _api("GET", f"{str_api}/pulls?head={str_head}&state=all&per_page={_PER_PAGE}")
	return [
		"OPEN"
		if dict_pr["state"] == "open"
		else "MERGED"
		if dict_pr["merged_at"] and dict_pr["head"]["sha"] == str_tip
		else "CLOSED"
		for dict_pr in list_prs
	]


def _already_gone(cls_exc: Exception) -> bool:
	"""Return whether a failed DELETE means the ref no longer exists.

	GitHub answers 422 both for a missing ref and for a refusal such as a ruleset, so a 422
	counts only when its body names the missing ref. Anything else is a real failure.

	Parameters
	----------
	cls_exc : Exception
		The error raised by the DELETE.

	Returns
	-------
	bool
		``True`` for a 404, or a 422 saying ``Reference does not exist``.
	"""
	int_code = getattr(cls_exc, "code", None)
	if int_code == 422:  # noqa: PLR2004
		return b"Reference does not exist" in cls_exc.read()
	return int_code == 404  # noqa: PLR2004


def main() -> int:
	"""Sweep every remote branch; delete (unless dry run) those whose PR merged.

	A single branch's API failure is logged and skipped so one bad lookup never sinks the run —
	and a skipped branch is simply kept, the safe direction. Failures are counted and fail the
	run at the end, so a sweep that could not do its job is not reported green.

	Returns
	-------
	int
		``1`` if any branch lookup or delete failed, otherwise ``0``.
	"""
	str_repo = os.environ["GITHUB_REPOSITORY"]
	str_owner = str_repo.split("/", 1)[0]
	str_api = f"{_GH_API}/repos/{str_repo}"
	bool_dry = is_dry_run(os.environ.get("SWEEP_DRY_RUN"))

	str_default = _api("GET", str_api)["default_branch"]
	dict_tips = _list_branches(str_api)
	set_bases = _open_pr_bases(str_api)
	dict_states: dict[str, list[str]] = {}
	int_lookup_failed = 0
	for str_branch, str_tip in dict_tips.items():
		if str_branch in _PROTECTED | {str_default}:
			continue
		if str_branch in set_bases:
			print(f"branch={str_branch} kept: base of an open PR")
			continue
		try:
			dict_states[str_branch] = _pr_states(str_api, str_owner, str_branch, str_tip)
		except (urllib.error.HTTPError, urllib.error.URLError, OSError) as cls_exc:
			int_lookup_failed += 1
			print(f"branch={str_branch} lookup failed (kept): {cls_exc}", file=sys.stderr)

	list_doomed = branches_to_delete(dict_states, str_default)
	int_delete_failed = 0
	for str_branch in list_doomed:
		if bool_dry:
			print(f"branch={str_branch} would delete (dry run)")
			continue
		try:
			_api("DELETE", f"{str_api}/git/refs/heads/{urllib.parse.quote(str_branch, safe='/')}")
			print(f"branch={str_branch} deleted")
		except (urllib.error.HTTPError, urllib.error.URLError, OSError) as cls_exc:
			if _already_gone(cls_exc):
				print(f"branch={str_branch} already gone", file=sys.stderr)
				continue
			int_delete_failed += 1
			print(f"branch={str_branch} delete failed (kept): {cls_exc}", file=sys.stderr)
	str_mode = "dry run" if bool_dry else "applied"
	print(
		f"examined {len(dict_tips)} branch(es), {len(dict_states)} with PR lookup, "
		f"{len(list_doomed)} stale ({str_mode}), {int_lookup_failed} lookup failure(s), "
		f"{int_delete_failed} delete failure(s)"
	)
	return 1 if int_lookup_failed or int_delete_failed else 0


if __name__ == "__main__":
	raise SystemExit(main())
