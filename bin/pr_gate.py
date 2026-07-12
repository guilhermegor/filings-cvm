#!/usr/bin/env python
"""PR quality gate — label, report, and (only for low-risk classes) hand the merge to GitHub.

Three things happen here, in order:

1. **Classify** the PR from its changed paths (**risk class**) and its diff volume (**size
   bucket**), and apply the corresponding labels — ``risk:*``, ``size:*``, ``gate:*``.
2. **Report**: publish/update ONE sticky comment carrying the per-axis table (tests, lint, types,
   CodeQL, docs build), so the state of the gate is readable without opening the checks tab.
3. **Auto-merge**: when the class is auto-mergeable AND the author opted in with the ``automerge``
   label, enable GitHub's *native* auto-merge (``PUT .../pulls/:n/merge`` is NOT used — the
   ``enablePullRequestAutoMerge`` mutation is). GitHub then holds the merge until **every required
   check of the `pr-quality-gate` ruleset is green** and merges by itself.

**Why auto-MERGE and not auto-APPROVE.** The ruleset requires *0* approvals (a solo maintainer
cannot approve their own PR), so a bot approval would unblock nothing — it would be decorative.
Native auto-merge bypasses nothing either: the ruleset stays the single source of truth for what
must pass; this script only decides *eligibility*, never *whether the checks passed*.

**Why risk-by-PATH and not by diff size.** A small diff is not a safe diff here. The real failure
mode is semantic — a ``FileContract`` column grounded wrong, a ``date_ref`` selecting the wrong
partition, a money column parsed to ``float``. A **one-character** change under
``_internal/config/contracts/`` is tiny *and* catastrophic, and **every test still passes**,
because the tests assert the contract that was written. So ``src/`` is **never** auto-merged, at
any size.

Pure classification lives in module-level functions (unit-tested); every GitHub call is confined to
:func:`main` and the thin helpers it calls, so the logic is testable without a network.

**Language.** Everything this bot emits — the comment, the axis names, the labels — is **English**,
like every other contributor/machine-facing surface here (code, commit messages, CI output). Only
the **published documentation** follows the site's own language (`mkdocs.yml` ``theme.language``,
pt-BR). The boundary is the *audience*, not the repository.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any
import urllib.error
import urllib.request


# Risk classes, most dangerous first — the PR's class is the FIRST one any changed path matches, so
# a PR touching both docs and src is classified `src`. Only the classes in AUTO_MERGEABLE may ever
# be merged without a human; `src` and `tests` always wait for review.
_RISK_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
	("src", ("src/",)),
	("tests", ("tests/",)),
	("deps", ("poetry.lock", "pyproject.toml")),
	(
		"ci",
		(
			".github/",
			"bin/",
			"Makefile",
			"tasks.sh",
			".pre-commit-config.yaml",
			".coveragerc",
			".codespellrc",
			".yamllint",
		),
	),
	("docs", ("docs/", "mkdocs.yml", "README.md", ".md")),
)

# Change classes a machine may merge. `src` and `tests` are deliberately absent: source needs eyes.
AUTO_MERGEABLE: frozenset[str] = frozenset({"docs", "ci", "deps"})

# Opt-in / opt-out labels. Auto-merge NEVER happens without OPT_IN_LABEL — the classification alone
# is not consent.
OPT_IN_LABEL = "automerge"
BLOCK_LABEL = "do-not-merge"

# Diff-volume buckets, by (additions + deletions). XL is never auto-merged regardless of class: a
# huge docs/CI diff still deserves a look.
_SIZE_BUCKETS: tuple[tuple[str, int], ...] = (
	("XS", 10),
	("S", 50),
	("M", 200),
	("L", 500),
)
MAX_AUTO_MERGE_SIZE = "L"

_MARKER = "<!-- pr-quality-gate -->"


def classify_risk(list_paths: list[str]) -> str:
	"""Return the PR's risk class from the paths it changes.

	The class is the most dangerous one any changed path matches (rules are ordered), so a PR that
	touches both ``docs/`` and ``src/`` is ``src`` — never the safer of the two.

	Parameters
	----------
	list_paths : list of str
		Repo-relative paths changed by the pull request.

	Returns
	-------
	str
		One of ``src``, ``tests``, ``deps``, ``ci``, ``docs``, or ``other`` when nothing matches
		(``other`` is not auto-mergeable, so an unknown path is treated as unsafe).
	"""
	for str_class, tuple_prefixes in _RISK_RULES:
		for str_path in list_paths:
			if any(str_path.startswith(p) or str_path.endswith(p) for p in tuple_prefixes):
				return str_class
	return "other"


def size_bucket(int_additions: int, int_deletions: int) -> str:
	"""Return the size bucket for a diff volume.

	Parameters
	----------
	int_additions : int
		Lines added.
	int_deletions : int
		Lines removed.

	Returns
	-------
	str
		``XS``, ``S``, ``M``, ``L`` or ``XL``.
	"""
	int_total = int_additions + int_deletions
	for str_bucket, int_ceiling in _SIZE_BUCKETS:
		if int_total < int_ceiling:
			return str_bucket
	return "XL"


def is_auto_mergeable(str_risk: str, str_size: str, list_labels: list[str]) -> bool:
	"""Decide whether this PR may be handed to GitHub's native auto-merge.

	All four conditions must hold: the class is auto-mergeable, the diff is not ``XL``, the author
	opted in, and nobody blocked it. **This says nothing about whether the checks passed** — the
	ruleset enforces that, and GitHub holds the merge until they are green.

	Parameters
	----------
	str_risk : str
		Risk class from :func:`classify_risk`.
	str_size : str
		Size bucket from :func:`size_bucket`.
	list_labels : list of str
		Labels currently on the pull request.

	Returns
	-------
	bool
		True when auto-merge should be enabled.
	"""
	if str_risk not in AUTO_MERGEABLE:
		return False
	if str_size == "XL":
		return False
	if BLOCK_LABEL in list_labels:
		return False
	return OPT_IN_LABEL in list_labels


def gate_state(list_axes: list[tuple[str, str, str]]) -> str:
	"""Fold the axes into the gate's overall state.

	**Pending is not failing.** A check that is still running says nothing about the outcome, and
	reporting it as ``failing`` would cry wolf on every freshly-opened PR (a real defect caught on
	this gate's own first live run). So a red axis wins over a pending one, but a pending one wins
	over green — the gate only claims ``passing`` once every axis has actually finished green.

	Parameters
	----------
	list_axes : list of tuple of (str, str, str)
		One ``(name, icon, detail)`` per checked axis.

	Returns
	-------
	str
		``passing``, ``pending`` or ``failing``.
	"""
	list_icons = [str_icon for _, str_icon, _ in list_axes]
	if "❌" in list_icons:
		return "failing"
	if "⏳" in list_icons or not list_icons:
		return "pending"
	return "passing"


def render_comment(
	str_risk: str,
	str_size: str,
	list_axes: list[tuple[str, str, str]],
	bool_auto_merge: bool,
) -> str:
	"""Render the sticky gate comment.

	Parameters
	----------
	str_risk : str
		Risk class from :func:`classify_risk`.
	str_size : str
		Size bucket from :func:`size_bucket`.
	list_axes : list of tuple of (str, str, str)
		One ``(name, icon, detail)`` per checked axis.
	bool_auto_merge : bool
		Whether native auto-merge was enabled for this PR.

	Returns
	-------
	str
		The full Markdown body, carrying the hidden marker used to find and update it in place.
	"""
	str_state = gate_state(list_axes)
	dict_headline = {
		"passing": "✅ **Gate green** — every axis passed.",
		"pending": "⏳ **Running** — waiting on the required checks.",
		"failing": "❌ **Blocked** — an axis of the gate did not pass.",
	}
	str_headline = dict_headline[str_state]
	list_rows = [f"| {name} | {icon} {detail} |" for name, icon, detail in list_axes]

	if bool_auto_merge:
		str_merge = (
			"🤖 **Auto-merge enabled** — GitHub merges on its own as soon as the required checks "
			"go green."
		)
	elif str_risk not in AUTO_MERGEABLE:
		str_merge = (
			f"👤 **Human review required** — class `{str_risk}` is never auto-merged "
			"(a one-character diff in `src/` can break a contract without failing a single test)."
		)
	else:
		str_merge = (
			f"💤 **Auto-merge available** — add the `{OPT_IN_LABEL}` label and GitHub will merge "
			"on its own once the gate is green."
		)

	return "\n".join(
		[
			_MARKER,
			"## 🛡️ Quality Gate",
			"",
			str_headline,
			"",
			"| Axis | Status |",
			"|------|--------|",
			*list_rows,
			"",
			f"**Risk class:** `{str_risk}` · **Size:** `{str_size}`",
			"",
			str_merge,
			"",
			"<sub>Comment generated by the Quality Gate (`bin/pr_gate.py`). "
			"Updated on every push.</sub>",
		]
	)


def _api(str_method: str, str_url: str, dict_body: dict | None = None) -> Any:  # noqa: ANN401
	"""Call the GitHub REST API with the workflow token.

	The return is ``Any`` on purpose: this is a JSON-decode boundary, and GitHub hands back an
	object here and an array there. Narrowing it to ``dict | list`` would only force a cast at
	every call site without buying any real safety.

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

	Raises
	------
	OSError
		If the request fails.
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


def _axes_from_checks(list_check_runs: list[dict]) -> list[tuple[str, str, str]]:
	"""Fold the head commit's check-runs into the gate's display axes.

	Parameters
	----------
	list_check_runs : list of dict
		Check-run objects for the PR's head SHA.

	Returns
	-------
	list of tuple of (str, str, str)
		One ``(name, icon, detail)`` per axis, in display order.
	"""
	dict_axes = {
		"Tests (3 OSes)": "Run Automated Tests",
		"Docs (build)": "build",
		"Security (CodeQL)": "CodeQL",
	}
	list_out: list[tuple[str, str, str]] = []
	for str_label, str_prefix in dict_axes.items():
		list_matching = [c for c in list_check_runs if c["name"].startswith(str_prefix)]
		if not list_matching:
			list_out.append((str_label, "⏳", "queued"))
			continue
		if any(c["status"] != "completed" for c in list_matching):
			list_out.append((str_label, "⏳", "running"))
		elif all(c["conclusion"] == "success" for c in list_matching):
			list_out.append((str_label, "✅", f"{len(list_matching)} check(s) OK"))
		else:
			list_int_failed = [c for c in list_matching if c["conclusion"] != "success"]
			list_out.append((str_label, "❌", f"{len(list_int_failed)} check(s) failing"))
	return list_out


def main() -> int:
	"""Classify the PR, label it, publish the sticky comment, and enable auto-merge when eligible.

	Returns
	-------
	int
		Process exit code (always 0 — the gate reports, the ruleset blocks).
	"""
	str_repo = os.environ["GITHUB_REPOSITORY"]
	int_pr = int(os.environ["PR_NUMBER"])
	str_api = f"https://api.github.com/repos/{str_repo}"

	dict_pr = _api("GET", f"{str_api}/pulls/{int_pr}")
	list_files = _api("GET", f"{str_api}/pulls/{int_pr}/files?per_page=100")
	list_paths = [f["filename"] for f in list_files]
	list_labels = [lbl["name"] for lbl in dict_pr["labels"]]

	str_risk = classify_risk(list_paths)
	str_size = size_bucket(dict_pr["additions"], dict_pr["deletions"])
	list_checks = _api("GET", f"{str_api}/commits/{dict_pr['head']['sha']}/check-runs")
	list_axes = _axes_from_checks(list_checks["check_runs"])
	str_state = gate_state(list_axes)

	bool_merge = is_auto_mergeable(str_risk, str_size, list_labels)
	if bool_merge:
		_enable_auto_merge(dict_pr["node_id"])

	_apply_labels(str_api, int_pr, list_labels, str_risk, str_size, str_state)
	_upsert_comment(str_api, int_pr, render_comment(str_risk, str_size, list_axes, bool_merge))
	print(f"risk={str_risk} size={str_size} gate={str_state} auto_merge={bool_merge}")
	return 0


def _enable_auto_merge(str_node_id: str) -> None:
	"""Enable GitHub's native auto-merge (squash) for the pull request.

	Native auto-merge bypasses nothing: GitHub holds the merge until every required check of the
	ruleset is green. A failure here is non-fatal — the gate still reports.

	Parameters
	----------
	str_node_id : str
		GraphQL node id of the pull request.
	"""
	str_query = (
		"mutation($id: ID!) { enablePullRequestAutoMerge("
		"input: {pullRequestId: $id, mergeMethod: SQUASH}) { clientMutationId } }"
	)
	try:
		_api(
			"POST",
			"https://api.github.com/graphql",
			{"query": str_query, "variables": {"id": str_node_id}},
		)
	except (urllib.error.HTTPError, urllib.error.URLError, OSError) as cls_exc:
		print(f"auto-merge not enabled: {cls_exc}", file=sys.stderr)


def _apply_labels(
	str_api: str,
	int_pr: int,
	list_current: list[str],
	str_risk: str,
	str_size: str,
	str_state: str,
) -> None:
	"""Replace the gate's own labels, leaving every other label untouched.

	Parameters
	----------
	str_api : str
		Repo API base URL.
	int_pr : int
		Pull-request number.
	list_current : list of str
		Labels currently on the PR.
	str_risk : str
		Risk class.
	str_size : str
		Size bucket.
	str_state : str
		Gate state from :func:`gate_state` — ``passing``, ``pending`` or ``failing``.
	"""
	list_owned = [lbl for lbl in list_current if lbl.startswith(("risk:", "size:", "gate:"))]
	list_wanted = [
		f"risk:{str_risk}",
		f"size:{str_size}",
		f"gate:{str_state}",
	]
	if sorted(list_owned) == sorted(list_wanted):
		return
	list_keep = [lbl for lbl in list_current if lbl not in list_owned]
	_api(
		"PUT",
		f"{str_api}/issues/{int_pr}/labels",
		{"labels": list_keep + list_wanted},
	)


def _upsert_comment(str_api: str, int_pr: int, str_body: str) -> None:
	"""Publish the gate comment, updating the existing one in place instead of stacking new ones.

	Parameters
	----------
	str_api : str
		Repo API base URL.
	int_pr : int
		Pull-request number.
	str_body : str
		Rendered Markdown body (carries the hidden marker).
	"""
	list_comments = _api("GET", f"{str_api}/issues/{int_pr}/comments?per_page=100")
	for dict_comment in list_comments:
		if _MARKER in dict_comment["body"]:
			_api(
				"PATCH",
				f"{str_api}/issues/comments/{dict_comment['id']}",
				{"body": str_body},
			)
			return
	_api("POST", f"{str_api}/issues/{int_pr}/comments", {"body": str_body})


if __name__ == "__main__":
	sys.exit(main())
