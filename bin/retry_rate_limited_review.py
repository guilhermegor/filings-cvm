#!/usr/bin/env python3
"""Re-ask for a review on any open PR whose reviewer was RATE LIMITED, not absent.

The review gate (``bin/check_review_threads.py``) correctly fails a PR that no declared
reviewer has looked at. But one cause of that state is transient and self-clearing: the
reviewer answered *"Review rate limited"* and will accept the request again in a few
minutes. Measured upstream over 112 PRs: **19 hit a rate limit and 18 of them were reviewed
in the end** — so a rate limit is a DELAY, not an unavailability.

That single number decides the design. An unavailability would need an escape hatch in the
gate; a delay needs the *asking* automated. So this script leaves the gate's verdict exactly
as strict as it was and removes the only part a human was doing by hand: waiting for the
window to pass, then re-typing the request. The PR then goes green on its own — the stale red
runs are cleared by ``bin/rerun_stale_gate_runs.sh`` (blueprintx#263), which already runs
from the passing gate.

⚠️ WHY A RATE-LIMIT DETECTOR IS SOUND HERE WHEN THE "ALREADY REVIEWED" ONE WAS NOT.
blueprintx#259 established that a reviewer notice's TEXT cannot decide a verdict: the
"already reviewed / does not re-review" sentence is a standing footnote about the product,
appended to every outcome. Re-measured over 132 notices before writing this file, and the
two phrases behave oppositely:

    phrase              performed   failed   not-completed
    "already reviewed"      24/25      3/3           55/59   <- useless, every outcome
    "rate limit"             0/25      0/3           57/59   <- clean separation

So keying on the rate-limit wording really does isolate one outcome. It is used here anyway
in the safest possible position: this script's only action is to ASK FOR A REVIEW. A false
positive costs one redundant request; it can never pass a gate or merge anything. Nothing in
this file is allowed to become an input to a verdict — that is what #259 forbids.

⚠️ IT NEEDS THE USER PAT, NOT ``GITHUB_TOKEN`` — same measurement as
``.github/workflows/coderabbit_trigger.yaml``. CodeRabbit IGNORES bot-authored comments: a
comment posted with ``GITHUB_TOKEN`` is authored by ``github-actions[bot]`` and is silently
dropped. Only a user PAT produces a comment the reviewer answers.

⚠️ IT IS A JANITOR, SO IT EXITS 0 EVEN WHEN IT CANNOT DO ITS JOB — see the section in
``bin/CLAUDE.md``. If this fails, the PR stays blocked behind a red gate, which is the status
quo and fully visible; nothing is hidden. Failing the step would only add a red run to a
board whose point is to tell a human where to look.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import types


_STR_MARKER = "<!-- retry-rate-limited-review -->"

_STR_REQUEST = f"@coderabbitai full review\n\n{_STR_MARKER}"

_RE_RATE_LIMIT = re.compile(r"rate[\s-]?limit", re.IGNORECASE)

_RE_DECLARED_WAIT = re.compile(
	r"next\s+included\s+review\s+will\s+be\s+available\s+in\s+(\d+)\s+minute", re.IGNORECASE
)

_RE_INCLUDED_QUOTA = re.compile(r"included\s+review\s+limit|fair\s+usage", re.IGNORECASE)

_INT_COOLDOWN_MIN = 40

_INT_MAX_ATTEMPTS_PER_PR = 5


def _gh_json(list_args: list[str]) -> object:
	"""Run a ``gh`` command and parse its stdout as JSON, or return ``None`` on any failure.

	Parameters
	----------
	list_args : list of str
		Arguments after ``gh``.

	Returns
	-------
	object
		The parsed JSON, or ``None`` when the call or the parse failed.
	"""
	str_gh = shutil.which("gh") or "gh"
	cls_done = subprocess.run(  # noqa: S603
		[str_gh, *list_args], capture_output=True, text=True, check=False
	)
	if cls_done.returncode != 0:
		print(f"::warning::gh {' '.join(list_args[:2])} failed: {cls_done.stderr.strip()[:200]}")
		return None
	try:
		return json.loads(cls_done.stdout or "null")
	except json.JSONDecodeError:
		print(f"::warning::gh {' '.join(list_args[:2])} returned unparsable JSON")
		return None


def load_gate(path_bin: pathlib.Path) -> types.ModuleType | None:
	"""Import ``check_review_threads.py`` by path, to reuse its roster and review helpers.

	The gate is a script rather than a package, so it is loaded the way
	``bin/check_backlog_ledger.py`` already loads ``bin/pr_gate.py``. Reusing it is the point:
	the roster format, the ``[bot]`` login normalisation and "did anyone review THIS commit"
	must not be re-implemented here, or the two files answer the same question differently.

	Parameters
	----------
	path_bin : pathlib.Path
		The ``bin/`` directory holding both scripts.

	Returns
	-------
	types.ModuleType or None
		The imported module, or ``None`` when it cannot be loaded.
	"""
	path_gate = path_bin / "check_review_threads.py"
	cls_spec = importlib.util.spec_from_file_location("check_review_threads", path_gate)
	if cls_spec is None or cls_spec.loader is None:
		print(f"::warning::cannot load the review gate from {path_gate}")
		return None
	cls_module = importlib.util.module_from_spec(cls_spec)
	try:
		cls_spec.loader.exec_module(cls_module)
	except Exception as cls_error:  # noqa: BLE001 - an unimportable gate is not this job's crash
		print(
			f"::warning::the review gate at {path_gate} failed to import: {str(cls_error)[:200]}"
		)
		return None
	return cls_module


def newest_roster_comment(
	list_comments: list[dict], set_roster: set[str], fn_norm: Callable[[str], str]
) -> dict | None:
	"""Return the newest roster-authored comment, whole.

	The declared-wait clock starts when the REVIEWER spoke, not when we last asked, so the
	caller needs that comment's timestamp as well as its body — hence the whole comment.

	Parameters
	----------
	list_comments : list of dict
		Normalised comments (``login``/``body``/``created_at``), oldest first.
	set_roster : set of str
		Already-normalised reviewer logins.
	fn_norm : Callable[[str], str]
		The gate's ``normalise_login``.

	Returns
	-------
	dict or None
		The newest roster comment, or ``None`` when the roster has said nothing.
	"""
	for dict_comment in reversed(list_comments):
		if (
			fn_norm(dict_comment.get("login") or "") in set_roster
			and dict_comment.get("type") == "Bot"
		):
			return dict_comment
	return None


def newest_roster_notice(
	list_comments: list[dict], set_roster: set[str], fn_norm: Callable[[str], str]
) -> str:
	"""Return the newest roster-authored comment body, untruncated.

	Parameters
	----------
	list_comments : list of dict
		Normalised comments (``login``/``body``/``created_at``), oldest first.
	set_roster : set of str
		Already-normalised reviewer logins.
	fn_norm : Callable[[str], str]
		The gate's ``normalise_login``.

	Returns
	-------
	str
		The newest roster comment's body, or ``""`` when the roster has said nothing.
	"""
	dict_comment = newest_roster_comment(list_comments, set_roster, fn_norm)
	if dict_comment is None:
		return ""
	return dict_comment.get("body") or ""


def parse_declared_wait(str_notice: str) -> int | None:
	"""Return the wait in minutes the reviewer declared, or ``None`` when it declared none.

	Parameters
	----------
	str_notice : str
		The reviewer's refusal body.

	Returns
	-------
	int or None
		Minutes to wait, or ``None`` when the notice states no number.
	"""
	cls_match = _RE_DECLARED_WAIT.search(str_notice)
	if cls_match is None:
		return None
	try:
		int_wait = int(cls_match.group(1))
		timedelta(minutes=int_wait)
	except (ValueError, OverflowError):
		return None
	return int_wait


def declared_wait_still_open(dict_notice: dict | None, dt_now: datetime) -> bool:
	"""Return whether the reviewer's own declared wait has yet to elapse.

	⚠️ Measured from the NOTICE, never from our last request. The reviewer says "available in N
	minutes" at the moment it refuses, so the deadline is *its* timestamp plus N. Anchoring on
	our marker instead would restart the clock every time we asked — which is the same
	self-referential mistake the ordering-vs-cooldown block above documents, one layer up.

	⚠️ **No declared number, no opinion.** When the notice states no wait this returns ``False``
	and the marker cooldown decides alone, exactly as before. Inventing a deadline from a
	refusal that named none would suppress the retry on evidence the reviewer never gave —
	changing behaviour nobody asked to change, on the one path that has no measurement behind
	it. This function speaks only when the reviewer did.

	Parameters
	----------
	dict_notice : dict or None
		The newest roster comment, or ``None``.
	dt_now : datetime.datetime
		The current time, timezone-aware.

	Returns
	-------
	bool
		``True`` only while a wait the reviewer actually declared is still open.
	"""
	if dict_notice is None:
		return False
	int_wait = parse_declared_wait(dict_notice.get("body") or "")
	if int_wait is None:
		return False
	dt_said = parse_timestamp(dict_notice.get("created_at") or "")
	if dt_said is None:
		return False
	return (dt_now - dt_said) < timedelta(minutes=int_wait)


def asked_recently(
	list_comments: list[dict],
	str_self_login: str,
	fn_norm: Callable[[str], str],
	dt_now: datetime,
	int_cooldown_min: int = _INT_COOLDOWN_MIN,
) -> bool:
	"""Return whether we posted a request within the cooldown window.

	Parameters
	----------
	list_comments : list of dict
		Normalised comments (``login``/``body``/``created_at``), oldest first.
	str_self_login : str
		The login the retry posts as. A marker from any other author is ignored; an empty
		value trusts no marker at all, so the worst case is asking twice.
	fn_norm : Callable[[str], str]
		The gate's ``normalise_login``.
	dt_now : datetime.datetime
		The current time, timezone-aware. Passed in rather than read, so a test states the
		moment it is testing instead of depending on the clock.
	int_cooldown_min : int, optional
		Minutes to wait between requests.

	Returns
	-------
	bool
		``True`` when our own marker comment is younger than the cooldown.
	"""
	str_self = fn_norm(str_self_login)
	if not str_self:
		return False

	for dict_comment in reversed(list_comments):
		if _STR_MARKER not in (dict_comment.get("body") or ""):
			continue
		if fn_norm(dict_comment.get("login") or "") != str_self:
			continue
		dt_posted = parse_timestamp(dict_comment.get("created_at") or "")
		if dt_posted is None:
			return True
		return (dt_now - dt_posted) < timedelta(minutes=int_cooldown_min)
	return False


def parse_timestamp(str_stamp: str) -> datetime | None:
	"""Parse a GitHub ISO-8601 timestamp into an aware datetime.

	Parameters
	----------
	str_stamp : str
		A timestamp such as ``2026-08-24T23:50:41Z``.

	Returns
	-------
	datetime.datetime or None
		The parsed value, or ``None`` when it cannot be read.
	"""
	try:
		return datetime.fromisoformat(str_stamp.replace("Z", "+00:00"))
	except ValueError:
		return None


def fetch_comments(str_repo: str, int_number: int) -> list[dict]:
	"""Return one PR's issue comments, oldest first, normalised with timestamps.

	Parameters
	----------
	str_repo : str
		``owner/repo``.
	int_number : int
		The PR number.

	Returns
	-------
	list of dict
		Comments as ``{"login", "type", "body", "created_at"}``, oldest first; empty when
		unreadable.
	"""
	list_raw = _gh_json(
		[
			"api",
			"--paginate",
			"--slurp",
			f"repos/{str_repo}/issues/{int_number}/comments?per_page=100",
		]
	)
	if not isinstance(list_raw, list):
		return []
	return [
		{
			"login": (dict_c.get("user") or {}).get("login") or "",
			"type": (dict_c.get("user") or {}).get("type") or "",
			"body": dict_c.get("body") or "",
			"created_at": dict_c.get("created_at") or "",
		}
		for list_page in list_raw
		if isinstance(list_page, list)
		for dict_c in list_page
		if isinstance(dict_c, dict)
	]


def pr_needs_retry(
	dict_pr: dict,
	list_comments: list[dict],
	set_reviewers: set[str],
	cls_gate: types.ModuleType,
	str_self_login: str = "",
	dt_now: datetime | None = None,
) -> bool:
	"""Return whether this PR is waiting on a rate-limited reviewer and should be re-asked.

	Parameters
	----------
	dict_pr : dict
		The ``pullRequest`` node from the gate's own query, for reviews and the head oid.
	list_comments : list of dict
		Normalised comments (``login``/``body``/``created_at``), oldest first.
	set_reviewers : set of str
		Logins that can actually submit a review.
	cls_gate : types.ModuleType
		The imported gate module.
	str_self_login : str, optional
		The login the retry posts as, used to tell OUR marker from anyone else's. Defaults to
		empty, which trusts no marker: the safe default is to ask twice, never to fall silent.
	dt_now : datetime.datetime or None, optional
		The current time; defaults to now in UTC.

	Returns
	-------
	bool
		``True`` when nothing has reviewed the head commit, the reviewer's newest word is a
		rate limit, and we have not asked within the cooldown.
	"""
	list_reviews = ((dict_pr.get("reviews") or {}).get("nodes")) or []
	str_head = dict_pr.get("headRefOid") or ""
	if cls_gate.reviewers_who_reported(list_reviews, set_reviewers, str_head):
		return False

	dict_notice = newest_roster_comment(list_comments, set_reviewers, cls_gate.normalise_login)
	str_notice = (dict_notice or {}).get("body") or ""
	if not _RE_RATE_LIMIT.search(str_notice):
		return False

	dt_when = dt_now or datetime.now(timezone.utc)

	if declared_wait_still_open(dict_notice, dt_when):
		return False

	return not asked_recently(
		list_comments,
		str_self_login,
		cls_gate.normalise_login,
		dt_when,
	)


def request_review(str_repo: str, int_number: int) -> bool:
	"""Post the full-review request on one PR.

	Parameters
	----------
	str_repo : str
		``owner/repo``.
	int_number : int
		The PR number.

	Returns
	-------
	bool
		``True`` when the comment was posted.
	"""
	dict_posted = _gh_json(
		[
			"api",
			f"repos/{str_repo}/issues/{int_number}/comments",
			"-f",
			f"body={_STR_REQUEST}",
			"--jq",
			"{login: .user.login, type: .user.type}",
		]
	)
	if not isinstance(dict_posted, dict):
		print(f"::warning::could not request a review on #{int_number}")
		return False

	if dict_posted.get("type") == "Bot":
		print(
			f"::warning::the request on #{int_number} was authored by "
			f"{dict_posted.get('login')} [Bot], which the reviewer IGNORES — set "
			"GH_PAT_REVIEW_TRIGGER to a user PAT (see coderabbit_trigger)."
		)
		return False

	print(f"requested a full review on #{int_number} as {dict_posted.get('login')}")
	return True


def flatten_open_prs(list_pages: list) -> list[dict]:
	"""Flatten ``gh api --paginate --slurp`` output into open PRs, oldest first.

	Parameters
	----------
	list_pages : list
		A list of pages, each a list of pull-request objects.

	Returns
	-------
	list of dict
		``{"number", "created_at"}`` for every PR across every page, sorted ascending by
		``created_at`` — the FIFO order the retry serves.
	"""
	list_flat = [
		{"number": dict_pr["number"], "created_at": dict_pr.get("created_at") or ""}
		for list_page in list_pages
		if isinstance(list_page, list)
		for dict_pr in list_page
		if isinstance(dict_pr, dict) and dict_pr.get("number")
	]
	return sorted(list_flat, key=lambda dict_item: dict_item["created_at"])


def resolve_self_login() -> str:
	"""Return the login the configured token authenticates as, or ``""`` when unknown.

	Returns
	-------
	str
		The login, or ``""`` when it cannot be resolved — which trusts no marker at all.
	"""
	dict_user = _gh_json(["api", "user", "--jq", "{login: .login}"])
	if not isinstance(dict_user, dict) or not dict_user.get("login"):
		print(
			"::warning::could not resolve the token's own login, so no marker is trusted — "
			"a review may be requested more than once per window."
		)
		return ""
	return str(dict_user["login"])


def build_candidate(
	str_repo: str,
	int_number: int,
	str_created_at: str,
	set_reviewers: set[str],
	cls_gate: types.ModuleType,
) -> dict | None:
	"""Fetch one PR and return its record when it is waiting on a rate-limited reviewer.

	Parameters
	----------
	str_repo : str
		``owner/repo``.
	int_number : int
		The PR number.
	str_created_at : str
		The PR's ``created_at``, carried through for FIFO ordering.
	set_reviewers : set of str
		Logins that can actually submit a review.
	cls_gate : types.ModuleType
		The imported gate module.

	Returns
	-------
	dict or None
		``{"number", "created_at", "pr", "comments", "notice"}``, or ``None`` when this PR's
		head commit has already been reviewed, nothing has been said about it, or it could not
		be read at all.
	"""
	str_owner, _, str_name = str_repo.partition("/")
	try:
		dict_pr = cls_gate.fetch_pull_request(
			str_owner, str_name, int_number, frozenset(set_reviewers)
		)
		list_comments = fetch_comments(str_repo, int_number)
	except Exception as cls_error:  # noqa: BLE001 - see the block above: degrade per PR
		print(f"::warning::could not read #{int_number}, skipping it: {str(cls_error)[:200]}")
		return None

	list_reviews = ((dict_pr.get("reviews") or {}).get("nodes")) or []
	str_head = dict_pr.get("headRefOid") or ""
	if cls_gate.reviewers_who_reported(list_reviews, set_reviewers, str_head):
		return None

	dict_notice = newest_roster_comment(list_comments, set_reviewers, cls_gate.normalise_login)
	if not _RE_RATE_LIMIT.search((dict_notice or {}).get("body") or ""):
		return None

	return {
		"number": int_number,
		"created_at": str_created_at,
		"pr": dict_pr,
		"comments": list_comments,
		"notice": dict_notice,
	}


def count_self_asks(
	list_comments: list[dict], str_self_login: str, fn_norm: Callable[[str], str]
) -> int:
	"""Count how many times we have already posted the marker on this PR.

	The starvation guard (``_INT_MAX_ATTEMPTS_PER_PR``) needs this; nothing else does, which is
	why it stayed uncounted before blueprintx#280.

	Parameters
	----------
	list_comments : list of dict
		Normalised comments (``login``/``body``/``created_at``).
	str_self_login : str
		The login the retry posts as. Empty trusts no marker, so the count is always ``0``.
	fn_norm : Callable[[str], str]
		The gate's ``normalise_login``.

	Returns
	-------
	int
		How many of our own marker comments this PR carries.
	"""
	str_self = fn_norm(str_self_login)
	if not str_self:
		return 0
	return sum(
		1
		for dict_comment in list_comments
		if _STR_MARKER in (dict_comment.get("body") or "")
		and fn_norm(dict_comment.get("login") or "") == str_self
	)


def notice_deadline(dict_notice: dict, dt_now: datetime) -> datetime | None:
	"""Return the moment a notice's declared wait elapses, or ``None`` when it is not binding.

	``None`` covers every case that carries no ongoing deadline: no declared wait, an unreadable
	timestamp, or a wait that has already elapsed — deliberately the same set
	``declared_wait_still_open`` treats as "not open", read from the same two parsers.

	Parameters
	----------
	dict_notice : dict
		A roster comment (``login``/``body``/``created_at``).
	dt_now : datetime.datetime
		The current time, timezone-aware.

	Returns
	-------
	datetime.datetime or None
		The deadline, only while it is still in the future.
	"""
	int_wait = parse_declared_wait(dict_notice.get("body") or "")
	if int_wait is None:
		return None
	dt_said = parse_timestamp(dict_notice.get("created_at") or "")
	if dt_said is None:
		return None
	dt_deadline = dt_said + timedelta(minutes=int_wait)
	return dt_deadline if dt_deadline > dt_now else None


def account_blocked_until(list_notices: list[dict], dt_now: datetime) -> datetime | None:
	"""Return when the account-level quota frees up, or ``None`` when nothing is blocking.

	Parameters
	----------
	list_notices : list of dict
		The newest roster comment for each PR still waiting on a review (one per PR).
	dt_now : datetime.datetime
		The current time, timezone-aware.

	Returns
	-------
	datetime.datetime or None
		The moment the account frees up, or ``None`` when no notice is currently blocking.
	"""
	list_deadlines = [
		dt_deadline
		for dict_notice in list_notices
		if dict_notice
		for dt_deadline in (notice_deadline(dict_notice, dt_now),)
		if dt_deadline is not None
	]
	return max(list_deadlines, default=None)


def select_pr_for_retry(
	list_candidates: list[dict],
	set_reviewers: set[str],
	cls_gate: types.ModuleType,
	str_self_login: str,
	dt_now: datetime,
	int_max_attempts: int = _INT_MAX_ATTEMPTS_PER_PR,
) -> int | None:
	"""Pick the oldest waiting PR that is eligible to be asked right now.

	Parameters
	----------
	list_candidates : list of dict
		Records from :func:`build_candidate`.
	set_reviewers : set of str
		Logins that can actually submit a review.
	cls_gate : types.ModuleType
		The imported gate module.
	str_self_login : str
		The login the retry posts as.
	dt_now : datetime.datetime
		The current time, timezone-aware.
	int_max_attempts : int, optional
		Attempts after which a PR is skipped past, rather than blocking the queue.

	Returns
	-------
	int or None
		The chosen PR number, or ``None`` when every candidate is either still cooling down or
		has exhausted its attempts.
	"""
	for dict_candidate in sorted(list_candidates, key=lambda d: d["created_at"]):
		if not pr_needs_retry(
			dict_candidate["pr"],
			dict_candidate["comments"],
			set_reviewers,
			cls_gate,
			str_self_login,
			dt_now,
		):
			continue
		int_attempts = count_self_asks(
			dict_candidate["comments"], str_self_login, cls_gate.normalise_login
		)
		if int_attempts >= int_max_attempts:
			print(
				f"::warning::#{dict_candidate['number']} has been asked {int_attempts} times "
				"and is still unreviewed — skipping past the FIFO head so newer PRs are not "
				"starved; this PR needs a human look."
			)
			continue
		return int(dict_candidate["number"])
	return None


def _resolve_gate_dir(path_own_bin: pathlib.Path) -> pathlib.Path:
	"""Return the directory holding ``check_review_threads.py``.

	The gate's single source is ``templates/common/bin/`` (blueprintx#175 follow-up), a
	SIBLING of ``templates/python-common/bin/`` where this script lives — but every scaffold
	copies the gate into the generated project's own flat ``bin/``, alongside this script.
	Both layouts have to resolve from the one runtime call site (``main``, below).

	Parameters
	----------
	path_own_bin : pathlib.Path
		This script's own ``bin/`` directory.

	Returns
	-------
	pathlib.Path
		``path_own_bin`` when the gate is co-located there (every generated project);
		otherwise ``templates/common/bin/``, for when this script runs straight out of the
		BlueprintX template tree (``templates/python-common/bin/``).
	"""
	if (path_own_bin / "check_review_threads.py").is_file():
		return path_own_bin
	return path_own_bin.parents[1] / "common" / "bin"


def resolve_setup(path_bin: pathlib.Path) -> tuple[types.ModuleType, set[str]] | None:
	"""Load the gate and the roster, or report why nothing can be done.

	Parameters
	----------
	path_bin : pathlib.Path
		The ``bin/`` directory holding the gate.

	Returns
	-------
	tuple of (types.ModuleType, set of str), or None
		The gate module and the logins that can submit a review, or ``None`` when either
		cannot be resolved.
	"""
	cls_gate = load_gate(path_bin)
	if cls_gate is None:
		return None

	try:
		dict_roster = cls_gate.load_roster(pathlib.Path.cwd())
		set_reviewers = cls_gate.reviewer_logins(dict_roster)
	except Exception as cls_error:  # noqa: BLE001 - see the block above: report, never die
		print(f"::warning::could not read the reviewer roster: {str(cls_error)[:200]}")
		return None

	if not set_reviewers:
		print("no reviewer in the roster can submit a review — nothing to re-ask.")
		return None
	return cls_gate, set_reviewers


def collect_waiting_prs(
	str_repo: str, set_reviewers: set, cls_gate: object
) -> tuple[list, list[dict]] | None:
	"""List the open PRs and the subset waiting on a rate-limited review.

	Parameters
	----------
	str_repo : str
		``owner/repo`` for the repository being swept.
	set_reviewers : set
		The reviewer logins from the roster.
	cls_gate : object
		The shared review-thread gate module.

	Returns
	-------
	tuple of (list, list of dict), or None
		All open PRs and the waiting subset; ``None`` when the listing could not be parsed.
	"""
	list_pages = _gh_json(
		["api", "--paginate", "--slurp", f"repos/{str_repo}/pulls?state=open&per_page=100"]
	)
	if not isinstance(list_pages, list):
		return None
	list_open = flatten_open_prs(list_pages)

	list_candidates: list[dict] = []
	for dict_open_pr in list_open:
		dict_candidate = build_candidate(
			str_repo, dict_open_pr["number"], dict_open_pr["created_at"], set_reviewers, cls_gate
		)
		if dict_candidate is not None:
			list_candidates.append(dict_candidate)
	return list_open, list_candidates


def choose_pr_to_retry(
	list_open: list,
	list_candidates: list[dict],
	set_reviewers: set,
	cls_gate: types.ModuleType,
	str_self_login: str,
	dt_now: datetime,
) -> int | None:
	"""Decide which PR, if any, to ask this run.

	Parameters
	----------
	list_open : list
		Every open PR, for the "checked N" log line.
	list_candidates : list of dict
		Records from :func:`build_candidate`.
	set_reviewers : set
		The reviewer logins from the roster.
	cls_gate : types.ModuleType
		The imported gate module.
	str_self_login : str
		The login the retry posts as.
	dt_now : datetime.datetime
		The current time, timezone-aware.

	Returns
	-------
	int or None
		The chosen PR number, or ``None`` when nobody should be asked this run.
	"""
	if not list_candidates:
		print(f"open PRs checked: {len(list_open)}; none are waiting on a rate-limited review.")
		return None

	dt_blocked_until = account_blocked_until([d["notice"] for d in list_candidates], dt_now)
	if dt_blocked_until is not None:
		print(
			f"account-level quota blocked until {dt_blocked_until.isoformat()} (newest refusal "
			f"across {len(list_candidates)} waiting PR(s)) — asking nobody this run."
		)
		return None

	int_chosen = select_pr_for_retry(
		list_candidates, set_reviewers, cls_gate, str_self_login, dt_now
	)
	if int_chosen is None:
		print(
			f"open PRs checked: {len(list_open)}; {len(list_candidates)} waiting, all still "
			"cooling down or past the attempt cap."
		)
	return int_chosen


def main() -> int:
	"""Re-ask for a review on the single oldest open PR still waiting on a rate limit.

	Returns
	-------
	int
		Always ``0`` — this is a janitor, and failing the step would add noise to the very
		signal it exists to clear. Problems are reported as workflow warnings.
	"""
	str_repo = os.environ.get("GITHUB_REPOSITORY", "")
	if not str_repo:
		print("::warning::GITHUB_REPOSITORY is unset — nothing to do.")
		return 0

	tuple_setup = resolve_setup(_resolve_gate_dir(pathlib.Path(__file__).resolve().parent))
	if tuple_setup is None:
		return 0
	cls_gate, set_reviewers = tuple_setup

	tuple_waiting = collect_waiting_prs(str_repo, set_reviewers, cls_gate)
	if tuple_waiting is None:
		return 0
	list_open, list_candidates = tuple_waiting

	str_self_login = resolve_self_login()
	dt_now = datetime.now(timezone.utc)
	int_chosen = choose_pr_to_retry(
		list_open, list_candidates, set_reviewers, cls_gate, str_self_login, dt_now
	)
	if int_chosen is None:
		return 0

	if "--dry-run" in sys.argv:
		print(
			f"[dry-run] would request a review on #{int_chosen} — oldest eligible of "
			f"{len(list_candidates)} waiting PR(s)."
		)
		return 0

	bool_asked = request_review(str_repo, int_chosen)
	print(f"open PRs checked: {len(list_open)}; requested #{int_chosen}: {bool_asked}.")
	return 0


if __name__ == "__main__":
	for cls_stream in (sys.stdout, sys.stderr):
		if hasattr(cls_stream, "reconfigure"):
			cls_stream.reconfigure(encoding="utf-8", errors="replace")

	sys.exit(main())
