"""Fail a PR whose review threads are not FINISHED — answered AND resolved.

A finding takes two actions and this gate requires both:

1. **Reply** on the thread with what changed and why.
2. **Resolve** the conversation once that reply is posted.

A review finding is dealt with in **two** halves — change the code, and **reply on the thread**
— and only the first is visible from the editor. The second is what a future session reads: a
thread holding just "finding" plus "addressed in commit <sha>" records that something changed,
never *why* — that the finding was deeper than reported, that the fix was relocated rather than
applied, that a sibling case was deliberately left alone. That rationale is the asset.

⚠️ ``isResolved`` does **not** answer this. A good review bot closes its own thread the moment
it sees the fix, so the flag measures the BOT's satisfaction, not the author's response.
Measured on the PR that motivated this gate: all 14 threads showed ``isResolved: true`` and
**11 of them held no reply from the author at all**.

The predicate is therefore about **thread content, never resolver identity**:

    a thread is answered when it holds at least one comment from an author OUTSIDE the
    declared review-bot roster, of at least ``int_min_chars`` characters.

That single rule settles three questions at once — what counts as answered (a bot's own
acknowledgement does not), who may resolve (anyone; identity is not the signal), and
bot-replying-to-bot (excluded by construction). Two rules people reach for first —
*"only a human may resolve"* and *"the last comment must be human"* — **fail the best case**,
because a good bot acknowledges the human's reply and then resolves, so the bot's comment is
always last.

**Provider-agnostic by construction.** The roster is data in ``.review-bots.yaml``; no tool is
named in the logic here. Adding a reviewer is adding a row. Note the shapes genuinely differ:
one tool posts inline threads, another posts only a status check and no thread at all — a
roster that assumes "every reviewer speaks in threads" is born broken, which is why an empty
thread list is not a THREAD failure.

⚠️ It is not a pass either, and this paragraph used to say it was. An empty thread list is what
you get both when a reviewer ran and found nothing AND when no reviewer ever ran — opposite
facts, one number. Reading threads alone the gate reported the second as success, and PRs #204
and #213 merged unreviewed with every check green. :func:`find_missing_review_problem` owns that
question separately, keyed on a SUBMITTED REVIEW rather than on threads, so the two outcomes can
print different sentences.

⚠️ A SUBMITTED REVIEW IS NOT ENOUGH EITHER — IT MUST BE A REVIEW OF **THIS** CODE.

A review is pinned to the commit it was written against and nothing re-pins it when the branch
moves, so "a roster member submitted a review" is satisfiable by code nobody looked at (#220,
measured on #219). ``find_missing_review_problem`` therefore requires a review attributed to
``headRefOid``, and prints a DIFFERENT sentence for "reviewed older code" than for "never
reviewed" — those two used to be indistinguishable, and they call for different actions.

⚠️ ``reviews == 0`` HAS SEVERAL CAUSES AND EXACTLY ONE VERDICT.

Nobody ran, the reviewer refused, it was rate-limited, or it declined as redundant — different
remedies, and the reviewer's notice is quoted so the reader can tell which. It is quoted and
never counted: every one of those outcomes carries the same "does not re-review already reviewed
commits" footnote, so the text cannot discriminate between them (#259, measured on #264 — the PR
that first tried to trust it). The failure stands in all four cases, and the message names
``@coderabbitai full review``, which unlike a plain ``review`` does not answer "already
reviewed".
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
import datetime
import functools
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys


try:
	import yaml
except ModuleNotFoundError:  # pragma: no cover - the gate self-skips without its parser
	yaml = None  # type: ignore[assignment]


_ROSTER_FILE = ".review-bots.yaml"

_POSTS_THREADS = "threads"
_POSTS_STATUS = "status"
_POSTS_CAN_REVIEW = {_POSTS_THREADS: True, _POSTS_STATUS: False}
_POSTS_VALID = frozenset(_POSTS_CAN_REVIEW)

_BOT_SUFFIX = "[bot]"


def normalise_login(str_login: str) -> str:
	"""Return a login comparable across GitHub's REST and GraphQL spellings.

	Parameters
	----------
	str_login : str
		A login as either API reports it, e.g. ``coderabbitai[bot]`` or ``coderabbitai``.

	Returns
	-------
	str
		The login without a trailing ``[bot]`` suffix, so the two spellings compare equal.
	"""
	str_clean = (str_login or "").strip()
	return str_clean[: -len(_BOT_SUFFIX)] if str_clean.endswith(_BOT_SUFFIX) else str_clean


_MIN_REPLY_CHARS = 100

_RE_MARKUP = re.compile(r"<!--.*?-->|<[^>]+>", re.DOTALL)

_QUERY = """
query($owner:String!, $repo:String!, $number:Int!, $rc:String, $tc:String, $cc:String) {
  repository(owner:$owner, name:$repo) {
    pullRequest(number:$number) {
      author { login __typename }
      headRefOid
      baseRefOid
      timelineItems(
        last:10,
        itemTypes:[BASE_REF_CHANGED_EVENT, AUTOMATIC_BASE_CHANGE_SUCCEEDED_EVENT]
      ) {
        nodes {
          __typename
          ... on BaseRefChangedEvent { createdAt }
          ... on AutomaticBaseChangeSucceededEvent { createdAt }
        }
      }
      comments(first:100, after:$cc) {
        pageInfo { hasNextPage endCursor }
        nodes { author { login __typename } authorAssociation body createdAt }
      }
      reviews(
        first:100, after:$rc,
        states:[APPROVED, CHANGES_REQUESTED, COMMENTED, DISMISSED]
      ) {
        pageInfo { hasNextPage endCursor }
        nodes { author { login __typename } commit { oid } state body submittedAt }
      }
      commits(last:1) {
        nodes { commit { committedDate checkSuites(first:100) { nodes { createdAt } } } }
      }
      allCommits: commits(first:100) {
        pageInfo { hasNextPage }
        nodes { commit { message author { email } signature { isValid wasSignedByGitHub } } }
      }
      reviewThreads(first:100, after:$tc) {
        pageInfo { hasNextPage endCursor }
        nodes {
          isResolved
          isOutdated
          path
          comments(first:50) { nodes { author { login } body } }
        }
      }
    }
  }
}
"""


def _roster_exists_on_default_branch(path_root: pathlib.Path) -> bool:
	"""Return whether the roster file is present on the repository's default branch.

	Returns
	-------
	bool
		``True`` only when git can prove the file exists there. Any failure (no git, shallow
			clone, no remote) returns ``False``, so an unresolvable state never
			invents a violation.

	Notes
	-----
	The repo-locating ``GIT_*`` variables are dropped from the child's environment because git
	exports them to hooks and ``GIT_DIR`` overrides ``-C``, so inside a pre-commit run the probe
	would otherwise answer for the enclosing repository instead of ``path_root``.
	"""
	dict_env = {
		str_key: str_value
		for str_key, str_value in os.environ.items()
		if str_key not in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE")
	}
	for str_ref in ("origin/HEAD", "origin/main", "origin/master"):
		cls_run = subprocess.run(  # noqa: S603
			["git", "-C", str(path_root), "cat-file", "-e", f"{str_ref}:{_ROSTER_FILE}"],  # noqa: S607
			capture_output=True,
			check=False,
			env=dict_env,
		)
		if cls_run.returncode == 0:
			return True
	return False


def posts_of(dict_row: dict) -> str:
	"""Return the ``posts:`` classification declared by one roster row.

	Parameters
	----------
	dict_row : dict
		One entry of the roster's ``reviewers:`` list.

	Returns
	-------
	str
		One of :data:`_POSTS_VALID` — ``"threads"`` or ``"status"``.

	Raises
	------
	RuntimeError
		When ``posts:`` is missing or is not one of :data:`_POSTS_VALID`. Defaulting is not
			available here in either direction: silently reading a forgotten field as ``status``
			makes the gate unsatisfiable (and unsatisfiable gates get bypassed with ``--admin``,
			taking the real blocks with them), while reading it as ``threads`` re-opens the exact
			hole this field exists to close. So the roster must say, and a row that does not is a
			configuration error the message has to name.
	"""
	str_login = str(dict_row.get("login") or "").strip()
	str_posts = str(dict_row.get("posts") or "").strip()
	if str_posts not in _POSTS_VALID:
		raise RuntimeError(
			f"{_ROSTER_FILE}: reviewer {str_login or '<no login>'} declares "
			f"posts: {str_posts or '<missing>'} — expected one of "
			f"{', '.join(sorted(_POSTS_VALID))}. This field decides who can satisfy the "
			f"missing-review gate, and neither default is safe, so it cannot be omitted."
		)
	return str_posts


def load_roster(path_root: pathlib.Path) -> dict[str, str]:
	"""Read the declared review-bot roster.

	Parameters
	----------
	path_root : pathlib.Path
		Repository root holding ``.review-bots.yaml``.

	Returns
	-------
	dict of str to str
		Normalised login mapped to its ``posts:`` classification. Every member counts as a
			reviewer rather than as an answer for the THREAD half; only the ``threads`` members
			can satisfy the MISSING-REVIEW half — see :func:`reviewer_logins`. Empty when the
			file was NEVER there, which makes the gate a no-op rather than a source of false
			failures.

	Raises
	------
	RuntimeError
		When the roster is absent HERE but present on the default branch — that is a
			deletion, and since an empty roster makes this gate a no-op, it would switch the
			gate off inside the very PR it is meant to police. Also propagated from
			:func:`posts_of` for a row that does not declare a usable ``posts:``.
	"""
	path_roster = path_root / _ROSTER_FILE
	if yaml is None:
		return {}
	if not path_roster.is_file():
		if _roster_exists_on_default_branch(path_root):
			raise RuntimeError(
				f"{_ROSTER_FILE} exists on the default branch but not here — deleting it "
				f"disables this gate. Restore it, or remove it on the default branch first."
			)
		return {}
	dict_yaml = yaml.safe_load(path_roster.read_text(encoding="utf-8")) or {}
	dict_roster = {
		normalise_login(str(d.get("login", ""))): posts_of(d)
		for d in (dict_yaml.get("reviewers") or [])
		if d.get("login")
	}
	if not dict_roster:
		raise RuntimeError(
			f"{_ROSTER_FILE} exists but declares no reviewers — an empty roster makes this "
			f"gate a no-op, which is the same as deleting it. Declare a reviewer, or delete "
			f"the file to opt out (that path self-skips with a message)."
		)
	return dict_roster


def reviewer_logins(dict_roster: dict[str, str]) -> set[str]:
	"""Return the roster logins that can actually submit a review.

	Parameters
	----------
	dict_roster : dict of str to str
		Roster as returned by :func:`load_roster`.

	Returns
	-------
	set of str
		The ``posts: threads`` members. A ``posts: status`` member is deliberately absent:
			it can neither be expected to review nor accepted as having reviewed.

	Raises
	------
	RuntimeError
		When a non-empty roster declares no member that can review. That roster makes the
			missing-review check unsatisfiable on every PR, and a permanently red required check
			is the fastest way to teach people that red means nothing.
	"""
	set_reviewers = {s for s, p in dict_roster.items() if _POSTS_CAN_REVIEW[p]}
	if dict_roster and not set_reviewers:
		raise RuntimeError(
			f"{_ROSTER_FILE} declares no member with posts: {_POSTS_THREADS}, so no PR can "
			f"ever satisfy the missing-review check. Declare a reviewer, or delete the "
			f"roster to opt out of this gate entirely."
		)
	return set_reviewers


def _fetch_page(
	str_owner: str,
	str_repo: str,
	int_number: int,
	str_review_cursor: str | None,
	str_thread_cursor: str | None,
	str_comment_cursor: str | None = None,
) -> dict:
	"""Run one page of the query.

	Returns
	-------
	dict
		The ``pullRequest`` node for this page.

	Raises
	------
	RuntimeError
		If the API call fails, so an unreachable API is never mistaken for a clean PR.
	"""
	list_cmd = [
		"gh",
		"api",
		"graphql",
		"-f",
		f"query={_QUERY}",
		"-F",
		f"owner={str_owner}",
		"-F",
		f"repo={str_repo}",
		"-F",
		f"number={int_number}",
		"-F",
		f"rc={str_review_cursor}" if str_review_cursor else "rc=",
		"-F",
		f"tc={str_thread_cursor}" if str_thread_cursor else "tc=",
		"-F",
		f"cc={str_comment_cursor}" if str_comment_cursor else "cc=",
	]
	cls_run = subprocess.run(list_cmd, capture_output=True, text=True, check=False)  # noqa: S603
	if cls_run.returncode != 0:
		raise RuntimeError(f"GraphQL query failed: {cls_run.stderr.strip()[:400]}")
	dict_out = json.loads(cls_run.stdout)
	if "errors" in dict_out:
		raise RuntimeError(f"GraphQL returned errors: {dict_out['errors']}")
	return dict_out["data"]["repository"]["pullRequest"]


_TUPLE_PAGED = ("reviews", "reviewThreads", "comments")


def _next_cursor(dict_side: dict | None) -> str | None:
	"""Return the cursor to resume a connection from, or ``None`` when it has no next page."""
	if not dict_side or not dict_side["pageInfo"]["hasNextPage"]:
		return None
	return dict_side["pageInfo"]["endCursor"]


def _borrows_bot_login(dict_node: dict, set_declared: set[str]) -> bool:
	"""Return whether a node's author borrows the login of a roster entry.

	``normalise_login`` strips ``[bot]``, so a human who registers a roster App's bare name
	would otherwise compare equal to it. Roster members are Apps by contract, so only a
	``__typename`` of ``Bot`` proves one and a missing one fails closed. Authors outside the
	roster are never touched, so human reviews still reach every other check.
	"""
	dict_author = dict_node.get("author") or {}
	set_roster = {normalise_login(s) for s in set_declared}
	return (
		normalise_login(dict_author.get("login") or "") in set_roster
		and dict_author.get("__typename") != "Bot"
	)


def _drop_borrowed(dict_pr: dict, set_declared: set[str]) -> None:
	"""Remove the reviews and issue comments whose author borrows a roster login."""
	for str_key in ("reviews", "comments"):
		dict_side = dict_pr.get(str_key)
		if dict_side:
			dict_side["nodes"] = [
				d for d in dict_side["nodes"] if not _borrows_bot_login(d, set_declared)
			]


def fetch_pull_request(
	str_owner: str, str_repo: str, int_number: int, set_declared: frozenset[str] = frozenset()
) -> dict:
	"""Fetch the PR's author, submitted reviews and review threads in one GraphQL call.

	Parameters
	----------
	str_owner : str
		Repository owner.
	str_repo : str
		Repository name.
	int_number : int
		Pull-request number.
	set_declared : frozenset of str, optional
		Roster and marker-poster logins. A review or comment under one of them that is not
		typed ``Bot`` is dropped here, so no caller can read a borrowed identity.

	Returns
	-------
	dict
		The ``pullRequest`` node, carrying ``author``, ``reviews`` and ``reviewThreads``.

	Raises
	------
	RuntimeError
		If the API call fails, so an unreachable API is never mistaken for a clean PR.
	"""
	dict_pr = _fetch_page(str_owner, str_repo, int_number, None, None, None)
	list_sides = [(dict_pr[str_key], str_key) for str_key in _TUPLE_PAGED if str_key in dict_pr]

	while any(dict_side["pageInfo"]["hasNextPage"] for dict_side, _ in list_sides):
		dict_next = _fetch_page(
			str_owner,
			str_repo,
			int_number,
			*(_next_cursor(dict_pr.get(str_key)) for str_key in _TUPLE_PAGED),
		)
		for dict_side, str_key in list_sides:
			if not dict_side["pageInfo"]["hasNextPage"]:
				continue
			dict_side["nodes"].extend(dict_next[str_key]["nodes"])
			dict_side["pageInfo"] = dict_next[str_key]["pageInfo"]
	_drop_borrowed(dict_pr, set_declared)
	return dict_pr


def reviewers_who_reported(
	list_reviews: list[dict],
	set_roster: set[str],
	str_commit_oid: str = "",
) -> set[str]:
	"""Return the roster logins that submitted a review, optionally pinned to one commit.

	Parameters
	----------
	list_reviews : list of dict
		Submitted reviews, each with an ``author`` node and a ``commit`` node.
	set_roster : set of str
		Already-normalised logins that can submit a review.
	str_commit_oid : str, optional
		When given, only a review written against exactly this commit counts. When empty,
			every review counts regardless of commit — used to tell "reviewed OLDER code" apart
			from "never reviewed", which must not print the same sentence.

	Returns
	-------
	set of str
		The subset of ``set_roster`` that reported under the requested pinning.
	"""
	return {
		normalise_login((d.get("author") or {}).get("login") or "")
		for d in list_reviews
		if not str_commit_oid or ((d.get("commit") or {}).get("oid") or "") == str_commit_oid
	} & set_roster


def reviewed_commits(list_reviews: list[dict], set_roster: set[str]) -> list[str]:
	"""Return the distinct commits a roster member reviewed, newest review first.

	Newest first because, after an ``update-branch``, the most recent reviewed commit is the
	likeliest match, so the caller's cap spends its calls where they pay.

	Parameters
	----------
	list_reviews : list of dict
		Submitted reviews, oldest first, each with an ``author`` node and a ``commit`` node.
	set_roster : set of str
		Already-normalised logins that can submit a review.

	Returns
	-------
	list of str
		Commit oids, deduplicated, empty oids dropped.
	"""
	list_oids = [
		(d.get("commit") or {}).get("oid") or ""
		for d in list_reviews
		if normalise_login((d.get("author") or {}).get("login") or "") in set_roster
		and d.get("state") != "DISMISSED"
	]
	return list(dict.fromkeys(str_oid for str_oid in reversed(list_oids) if str_oid))


_INT_COMPARE_FILES = 300

_INT_COMPARE_TIMEOUT_S = 20

_INT_MAX_REVIEWED_COMMITS = 5

_TUPLE_FINGERPRINT_ERRORS = (
	RuntimeError,
	ValueError,
	OSError,
	subprocess.TimeoutExpired,
)


def _is_pure_rename(dict_file: dict) -> bool:
	"""Return whether a file entry is a rename with no patch text AND a blob ``sha`` to hash.

	The API reports ``changes == 0`` for a binary file too, so the blob ``sha`` is what proves
	the content; without it the entry is not trusted.
	"""
	return (
		dict_file.get("status") == "renamed"
		and dict_file.get("changes") == 0
		and bool(dict_file.get("sha"))
	)


_TUPLE_PATCH_PREFIXES = ("+", "-")


def patch_fingerprint(list_files: list[dict]) -> str:
	"""Hash the PR's own patch as the compare API reports it.

	Parameters
	----------
	list_files : list of dict
		The ``files`` array of ``compare/<base>...<oid>`` (merge-base to oid).

	Returns
	-------
	str
		A digest of the file names and the ordered ``+``/``-`` lines. Hunk headers (line
			numbers and function context) and unchanged context lines are ignored: they
			describe the base, and main's edits split and re-head hunks. An identical edit
			moved to another function therefore matches.

	Raises
	------
	ValueError
		If the list is malformed, empty, possibly truncated, or a file carries no patch text
			(a pure rename has none and is hashed by its names).
	"""
	if not isinstance(list_files, list) or not all(isinstance(d, dict) for d in list_files):
		raise ValueError("patch unavailable: the file list is malformed")
	if not list_files or len(list_files) >= _INT_COMPARE_FILES:
		raise ValueError(f"patch unavailable: {len(list_files)} file(s) in the comparison")
	if any(d.get("patch") is None and not _is_pure_rename(d) for d in list_files):
		raise ValueError("patch unavailable: a file has no patch text (binary or too large)")
	try:
		list_parts = [
			[
				d["filename"],
				d.get("status", ""),
				d.get("previous_filename", ""),
				d.get("sha", "") if d.get("patch") is None else "",
				[s for s in (d.get("patch") or "").splitlines() if s[:1] in _TUPLE_PATCH_PREFIXES],
			]
			for d in sorted(list_files, key=lambda d: d["filename"])
		]
	except (KeyError, TypeError, AttributeError) as cls_error:
		raise ValueError(f"patch unavailable: malformed file entry ({cls_error!r})") from cls_error
	return hashlib.sha256(json.dumps(list_parts).encode()).hexdigest()


def fetch_patch_fingerprint(str_owner: str, str_repo: str, str_base: str, str_oid: str) -> str:
	"""Return the PR's own patch fingerprint at ``str_oid`` via the compare API.

	The CI checkout is shallow (``actions/checkout`` defaults to ``fetch-depth: 1``), so
	``git merge-base`` has no history to read. The three-dot compare computes the merge base
	server side, which is the same diff ``git diff $(git merge-base base oid) oid`` yields.

	Parameters
	----------
	str_owner : str
		Repository owner.
	str_repo : str
		Repository name.
	str_base : str
		The base commit SHA, read once with the PR. ⚠️ Never the branch name: two compares
			would resolve it at two moments, and a retarget or push in between would measure
			both patches against different bases.
	str_oid : str
		The commit whose patch is wanted.

	Returns
	-------
	str
		See :func:`patch_fingerprint`.

	Raises
	------
	RuntimeError
		If the API call fails.
	ValueError
		If the base SHA is empty, or the response is unusable, see
			:func:`patch_fingerprint`.
	"""
	if not str_base:
		raise ValueError("patch unavailable: the PR's base commit is unknown")
	list_cmd = [
		"gh",
		"api",
		f"repos/{str_owner}/{str_repo}/compare/{str_base}...{str_oid}?per_page=1",
	]
	cls_run = subprocess.run(  # noqa: S603
		list_cmd,
		capture_output=True,
		text=True,
		check=False,
		timeout=_INT_COMPARE_TIMEOUT_S,
	)
	if cls_run.returncode != 0:
		raise RuntimeError(f"compare failed: {cls_run.stderr.strip()[:400]}")
	dict_compare = json.loads(cls_run.stdout)
	if not isinstance(dict_compare, dict):
		raise ValueError("patch unavailable: the compare response is not an object")
	return patch_fingerprint(dict_compare.get("files"))


def review_covers_head(
	fn_fingerprint: Callable[[str], str],
	str_review_oid: str,
	str_head_oid: str,
	str_head_digest: str,
) -> bool:
	"""Return whether a review at an earlier commit still covers the head.

	It does when the PR's own patch is unchanged, so the head only merged the base in. A
	conflict resolution, a new commit or a force-push changes the patch and stays superseded.
	⚠️ Fails CLOSED: any error computing the review's patch (API failure, a malformed file
	entry) means "not covered", never "covered".

	Parameters
	----------
	fn_fingerprint : Callable[[str], str]
		Maps a commit oid to its patch fingerprint; raises on an unavailable patch.
	str_review_oid : str
		The commit the review was written against.
	str_head_oid : str
		The PR's head commit, for the diagnostic only.
	str_head_digest : str
		The head's fingerprint, computed once by the caller and passed in, so the
			at-most-once guarantee never depends on the callable caching.

	Returns
	-------
	bool
		``True`` only when both fingerprints were computed and are equal.
	"""
	try:
		bool_same = fn_fingerprint(str_review_oid) == str_head_digest
	except _TUPLE_FINGERPRINT_ERRORS as cls_error:
		_note(f"carry-forward from {str_review_oid[:7]} unavailable: {cls_error}")
		return False
	if bool_same:
		_note(
			f"review at {str_review_oid[:7]} still covers {str_head_oid[:7]}: the head only "
			"merges the base, the PR's own patch is unchanged"
		)
	return bool_same


def _note(str_message: str) -> None:
	"""Print a diagnostic on stderr, so ``--json`` keeps stdout to the one verdict document.

	Parameters
	----------
	str_message : str
		The line to print.
	"""
	print(str_message, file=sys.stderr)


def review_carried_forward(
	fn_fingerprint: Callable[[str], str] | None,
	list_reviews: list[dict],
	set_roster: set[str],
	str_head_oid: str,
) -> str:
	"""Return the commit of an earlier roster review that still covers the head, or ``""``.

	The head is fingerprinted once, up front: if that fails, every comparison would fail the
	same way, so the loop is skipped instead of repeating the failing call per reviewed commit.
	Only the newest ``_INT_MAX_REVIEWED_COMMITS`` reviewed commits are tried.

	Parameters
	----------
	fn_fingerprint : Callable[[str], str] or None
		Maps a commit oid to its patch fingerprint; ``None`` disables carry-forward.
	list_reviews : list of dict
		Submitted reviews.
	set_roster : set of str
		Already-normalised logins that can submit a review.
	str_head_oid : str
		The PR's head commit.

	Returns
	-------
	str
		The covering review's commit, or ``""`` when none has an equal fingerprint.
	"""
	list_oids = reviewed_commits(list_reviews, set_roster) if fn_fingerprint else []
	if not list_oids:
		return ""
	try:
		str_head_digest = fn_fingerprint(str_head_oid)
	except _TUPLE_FINGERPRINT_ERRORS as cls_error:
		_note(f"carry-forward unavailable, the head patch cannot be read: {cls_error}")
		return ""
	for str_oid in list_oids[:_INT_MAX_REVIEWED_COMMITS]:
		if review_covers_head(fn_fingerprint, str_oid, str_head_oid, str_head_digest):
			return str_oid
	return ""


_INT_NOTICE_DISPLAY_CHARS = 200


def newest_roster_notice(list_notices: list[dict], set_roster: set[str]) -> str:
	"""Return the roster's most recent notice, flattened and COMPLETE.

	Parameters
	----------
	list_notices : list of dict
		The PR's issue comments, oldest first — the stream a declining reviewer posts to.
	set_roster : set of str
		Already-normalised logins that can submit a review.

	Returns
	-------
	str
		The newest roster comment with markup stripped, untruncated, or ``""`` when the roster
			has said nothing.

	Notes
	-----
	Every matcher reads THIS, never the truncated display form. A phrase the reviewer buries
	past the display budget is still a phrase it said, and a cut string turns "found" into
	"absent" — silent in both directions. Measured over 112 real notices in this repo
	(blueprintx#372). Four classified ``UNKNOWN`` on the full body and ``OK`` on the first
	200 chars, with the phrase at offsets 394, 583, 583 and 2700 — an unrecognised rate
	limit reported as no rate limit, the third state collapsing into the wrong one. Four
	carried a completion phrase past the budget, so the gate would claim no review completed
	on a PR whose reviewer had written "Review finished".
	"""
	for dict_comment in reversed(list_notices):
		if (
			normalise_login((dict_comment.get("author") or {}).get("login") or "")
			not in set_roster
		):
			continue
		return " ".join(_RE_MARKUP.sub(" ", dict_comment.get("body") or "").split())
	return ""


def summarise_reviewer_notice(list_notices: list[dict], set_roster: set[str]) -> str:
	"""Return the roster's most recent notice, truncated, to quote in a failure message.

	Parameters
	----------
	list_notices : list of dict
		The PR's issue comments, oldest first — the stream a declining reviewer posts to.
	set_roster : set of str
		Already-normalised logins that can submit a review.

	Returns
	-------
	str
		:func:`newest_roster_notice` cut to :data:`_INT_NOTICE_DISPLAY_CHARS`, or ``""`` when
			the roster has said nothing. ⚠️ DISPLAY ONLY, never a verdict — see the notice block
			above: every outcome carries the same "already reviewed" footnote, so the text cannot
			discriminate between them. Match on :func:`newest_roster_notice` instead.
	"""
	return newest_roster_notice(list_notices, set_roster)[:_INT_NOTICE_DISPLAY_CHARS]


def newest_roster_notice_date(list_notices: list[dict], set_roster: set[str]) -> str:
	"""Return the ``createdAt`` of the newest roster-authored notice.

	Parameters
	----------
	list_notices : list of dict
		The PR's issue comments, oldest first.
	set_roster : set of str
		Already-normalised logins that can submit a review.

	Returns
	-------
	str
		ISO-8601 timestamp, or ``""`` when the roster has said nothing. Pairs with
			:func:`summarise_reviewer_notice`, which walks the same stream for the same comment.
	"""
	for dict_comment in reversed(list_notices):
		if normalise_login((dict_comment.get("author") or {}).get("login") or "") in set_roster:
			return dict_comment.get("createdAt") or ""
	return ""


_RE_CHAT_LIMIT = re.compile(
	r"exceeded\s+the\s+limit\s+for\s+the\s+number\s+of\s+chat\s+messages", re.IGNORECASE
)
_RE_REVIEW_LIMIT = re.compile(r"review\s+rate\s+limited", re.IGNORECASE)
_RE_ANY_RATE_LIMIT = re.compile(r"rate[\s-]?limit", re.IGNORECASE)

_RE_FILE_CAP = re.compile(
	r"review\s+skipped:\s*\d+\s+files?\s+exceed\s+the\s+limit\s+of\s+\d+(?:\.|$)",
	re.IGNORECASE,
)

NOTICE_REVIEW_LIMITED = "REVIEW_LIMITED"
NOTICE_CHAT_LIMITED = "CHAT_LIMITED"
NOTICE_FILE_CAP_EXCEEDED = "FILE_CAP_EXCEEDED"
NOTICE_OK = "OK"
NOTICE_UNKNOWN = "UNKNOWN"


def classify_reviewer_notice(str_notice: str) -> str:
	"""Classify a reviewer's notice by which quota or refusal (if any) it reports.

	Parameters
	----------
	str_notice : str
		A reviewer comment body, or ``""`` when the roster has said nothing.

	Returns
	-------
	str
		One of :data:`NOTICE_FILE_CAP_EXCEEDED` (a stated file-count refusal — see the block
		above), :data:`NOTICE_CHAT_LIMITED`, :data:`NOTICE_REVIEW_LIMITED`, :data:`NOTICE_OK`
		(no rate-limit or cap wording at all — including an empty notice), or
		:data:`NOTICE_UNKNOWN` (mentions a rate limit in neither recognised shape).
	"""
	if _RE_FILE_CAP.search(str_notice):
		return NOTICE_FILE_CAP_EXCEEDED
	if _RE_CHAT_LIMIT.search(str_notice):
		return NOTICE_CHAT_LIMITED
	if _RE_REVIEW_LIMIT.search(str_notice):
		return NOTICE_REVIEW_LIMITED
	if _RE_ANY_RATE_LIMIT.search(str_notice):
		return NOTICE_UNKNOWN
	return NOTICE_OK


_RE_CHAT_WAIT = re.compile(
	r"wait\s+\*{0,2}(\d+)\s+minutes?(?:\s+and\s+(\d+)\s+seconds?)?\*{0,2}",
	re.IGNORECASE,
)
_RE_REVIEW_WAIT = re.compile(
	r"next\s+included\s+review\s+will\s+be\s+available\s+in\s+(\d+)\s+minutes?",
	re.IGNORECASE,
)


def parse_declared_wait(str_notice: str) -> int | None:
	"""Return the wait in SECONDS the reviewer declared, or ``None`` when it declared none.

	Parameters
	----------
	str_notice : str
		The reviewer's refusal body.

	Returns
	-------
	int or None
		Seconds to wait, or ``None`` when the notice states no parseable wait.
	"""
	cls_chat = _RE_CHAT_WAIT.search(str_notice)
	if cls_chat is not None:
		try:
			return int(cls_chat.group(1)) * 60 + int(cls_chat.group(2) or 0)
		except ValueError:
			return None
	cls_review = _RE_REVIEW_WAIT.search(str_notice)
	if cls_review is not None:
		try:
			return int(cls_review.group(1)) * 60
		except ValueError:
			return None
	return None


_TUPLE_COMPLETION_PHRASES = (
	"review finished",
	"no actionable comments were generated",
)


def reviewer_declared_completion(
	list_notices: list[dict],
	set_roster: set[str],
	str_head_date: str = "",
) -> bool:
	"""Return whether a roster member's own notice says it reviewed THIS PR's head.

	Parameters
	----------
	list_notices : list of dict
		The PR's issue comments, oldest first — the stream the reviewer reports completion to.
	set_roster : set of str
		Already-normalised logins that can submit a review.
	str_head_date : str, optional
		ISO-8601 time the head reached GitHub. A notice created BEFORE it describes
			superseded code and is not evidence. Empty means unknown, and unknown fails closed.

	Returns
	-------
	bool
		``True`` when a roster-authored comment carries a completion phrase AND postdates the
			head commit. ⚠️ Evidence that a review HAPPENED and never that a thread was answered —
			see the COMPLETION block above.
	"""
	if not str_head_date:
		return False
	str_newest = newest_roster_notice(list_notices, set_roster).casefold()
	if not any(str_phrase in str_newest for str_phrase in _TUPLE_COMPLETION_PHRASES):
		return False
	str_when = newest_roster_notice_date(list_notices, set_roster)
	return bool(str_when) and str_when >= str_head_date


_KIND_COMMENT_MARKER = "comment-marker"
_SET_TRUSTED_ASSOCIATIONS = frozenset({"OWNER", "MEMBER", "COLLABORATOR"})


def load_comment_markers(path_root: pathlib.Path) -> tuple[str, ...]:
	"""Return the ``kind: comment-marker`` strings declared by the roster.

	Parameters
	----------
	path_root : pathlib.Path
		Repository root holding ``.review-bots.yaml``.

	Returns
	-------
	tuple of str
		Lower-cased marker strings; empty when the file, the key or the row is absent, so a
			roster without the row behaves exactly as before.
	"""
	path_roster = path_root / _ROSTER_FILE
	if yaml is None or not path_roster.is_file():
		return ()
	dict_yaml = yaml.safe_load(path_roster.read_text(encoding="utf-8")) or {}
	return tuple(
		str(d["marker"]).strip().casefold()
		for d in (dict_yaml.get("reviewers") or [])
		if isinstance(d, dict)
		and d.get("kind") == _KIND_COMMENT_MARKER
		and str(d.get("marker") or "").strip()
	)


def _row_posters(posters: object) -> frozenset[str]:
	"""Return one row's normalised ``posters:`` logins, or none when the value is malformed.

	Only a list of non-empty strings is valid. A scalar (``posters: foo``) would otherwise be
	iterated into single characters, so anything else is reported on stderr and trusts nobody.
	"""
	if posters is None:
		return frozenset()
	if not isinstance(posters, list) or not all(isinstance(x, str) and x.strip() for x in posters):
		print(
			"check_review_threads: ignoring a comment-marker `posters:` that is not a list of "
			"non-empty strings; no marker will be accepted from that row",
			file=sys.stderr,
		)
		return frozenset()
	return frozenset(normalise_login(x) for x in posters)


def load_marker_posters(path_root: pathlib.Path) -> frozenset[str]:
	"""Return the normalised logins the roster's ``comment-marker`` rows allow to post a marker.

	Parameters
	----------
	path_root : pathlib.Path
		Repository root holding ``.review-bots.yaml``.

	Returns
	-------
	frozenset of str
		Logins from every ``posters:`` list, normalised like the roster logins. Empty when
		absent, which makes every marker unacceptable: authority is an explicit allowlist,
		never an author-association guess (blueprintx#761).
	"""
	path_roster = path_root / _ROSTER_FILE
	if yaml is None or not path_roster.is_file():
		return frozenset()
	dict_yaml = yaml.safe_load(path_roster.read_text(encoding="utf-8")) or {}
	return frozenset(
		str_login
		for d in (dict_yaml.get("reviewers") or [])
		if isinstance(d, dict) and d.get("kind") == _KIND_COMMENT_MARKER
		for str_login in _row_posters(d.get("posters"))
	)


_RE_FINDINGS_LINE = re.compile(r"(\d+) finding\(s\) across (\d+) reviewed file\(s\)\.")


def ladder_reports_zero_findings(list_lines: list[str]) -> bool:
	"""Return whether a ladder comment's findings line reads zero, failing closed.

	Parameters
	----------
	list_lines : list of str
		The comment body split into lines.

	Returns
	-------
	bool
		``True`` only when exactly one line is ``0 finding(s) across N reviewed file(s).``
			and no line reports a non-zero count. A missing or unparsable line is "has
			findings", so a prose review never satisfies the gate (blueprintx#630).
	"""
	list_stripped = [str_line.strip() for str_line in list_lines]
	list_counts = [m.group(1) for m in map(_RE_FINDINGS_LINE.search, list_stripped) if m]
	list_zero = [m for m in map(_RE_FINDINGS_LINE.fullmatch, list_stripped) if m]
	return list_counts == ["0"] and len(list_zero) == 1 and int(list_zero[0].group(2)) > 0


def _is_allowlisted_bot(dict_notice: dict, set_posters: frozenset[str]) -> bool:
	"""Return whether a comment's author is a GitHub ``Bot`` actor whose login is allowlisted.

	The login alone is not identity: normalising strips ``[bot]``, so a human who registers the
	bare App name would match. GraphQL ``__typename`` separates the two, and a missing one
	fails closed.
	"""
	dict_author = dict_notice.get("author") or {}
	return (
		dict_author.get("__typename") == "Bot"
		and normalise_login(dict_author.get("login") or "") in set_posters
	)


def ladder_marker_declared(
	list_notices: list[dict],
	tuple_markers: tuple[str, ...],
	str_head_date: str = "",
	str_head_oid: str = "",
	set_posters: frozenset[str] = frozenset(),
) -> bool:
	"""Return whether an allowlisted poster declared a roster marker after the head commit.

	Parameters
	----------
	list_notices : list of dict
		The PR's issue comments, each with ``authorAssociation``, ``body``, ``createdAt``.
	tuple_markers : tuple of str
		Lower-cased markers from :func:`load_comment_markers`; matched at the start of the body
			only, so a quotation on a later line is not a review.
	str_head_date : str, optional
		ISO-8601 time the head reached GitHub; empty fails closed.
	str_head_oid : str, optional
		The head commit SHA. The ladder writes ``Reviewed head: <sha>`` on the second line
			of its comment, which must name this SHA; empty fails closed.
	set_posters : frozenset of str, optional
		Normalised logins from :func:`load_marker_posters`; the author must also be a ``Bot``
		actor (``__typename``), so a user with the bare name does not match. The association is NOT
		consulted: the PR author is usually the repo OWNER, so trusting it would let the
		author self-approve by typing the marker (blueprintx#761). Empty fails closed.

	Returns
	-------
	bool
		``True`` only for a comment by an allowlisted poster carrying a marker and
			postdating the head, whose LATEST such comment names the head SHA on its second
			line and reports zero findings (a later ladder run, even a malformed one,
			supersedes an earlier clean one), so an outside commenter cannot forge it and a
			review of an older head cannot be reused.
	"""
	if not str_head_date or not str_head_oid:
		return False
	str_reviewed = f"reviewed head: {str_head_oid}".casefold()
	list_trusted = [
		d
		for d in list_notices
		if _is_allowlisted_bot(d, set_posters)
		and (d.get("createdAt") or "") >= str_head_date
		and (d.get("body") or "").lstrip().casefold().startswith(tuple_markers)
	]
	if not list_trusted:
		return False
	dict_latest = max(list_trusted, key=lambda d: d.get("createdAt") or "")
	str_body = (dict_latest.get("body") or "").strip()
	list_lines = str_body.splitlines()
	if [s.strip().casefold() for s in list_lines[1:2]] != [str_reviewed]:
		return False
	return ladder_reports_zero_findings(list_lines)


def _zero_review_message(str_quote: str, set_roster: set[str], list_notices: list[dict]) -> str:
	"""Return the message for a PR with zero reviews submitted by the roster.

	Parameters
	----------
	str_quote : str
		The "reviewer's most recent notice" suffix the caller already built, or ``""``.
	set_roster : set of str
		Already-normalised logins that can submit a review, named in the generic message.
	list_notices : list of dict
		The PR's issue comments, oldest first — read again to classify the SAME notice
			``str_quote`` already quotes, so the sentence and the quote never disagree.

	Returns
	-------
	str
		The file-cap sentence when the reviewer's newest notice states that structural reason;
			the generic "never ran" sentence otherwise. Both are failures — never a pass.
	"""
	str_notice = newest_roster_notice(list_notices, set_roster)
	if classify_reviewer_notice(str_notice) == NOTICE_FILE_CAP_EXCEEDED:
		return (
			"a declared reviewer DECLINED this PR for a STRUCTURAL reason it stated: the diff "
			"exceeds the reviewer's file-count cap. This is NOT 'no reviewer ever ran' — "
			"retrying or waiting will not change the file count.\n"
			"Split this PR into smaller PRs, each under the cap, so each part can actually be "
			"reviewed and merged." + str_quote
		)
	return (
		f"no declared reviewer ever reported on this PR — expected one of "
		f"{', '.join(sorted(set_roster))} to submit a review, and none did. "
		"This is NOT 'the reviewer found nothing': a reviewer that ran and found nothing "
		"still submits a review, so zero threads would be fine. Zero REVIEWS means the "
		"reviewer never ran, and nothing on this PR has been looked at.\n"
		"Trigger it with '@coderabbitai full review' from a user account. ⚠️ Prefer FULL over "
		"a plain 'review': an incremental reviewer answers 'already reviewed' on commits it has "
		"seen on another PR (a reopen, a rebase, a re-PR), and a full review does not." + str_quote
	)


def _notice_quote(list_notices: list[dict], set_roster: set[str]) -> str:
	"""Return the reviewer's newest notice as a message suffix, or ``""`` when there is none."""
	str_seen = summarise_reviewer_notice(list_notices, set_roster)
	return f"\nThe reviewer's most recent notice on this PR reads: {str_seen}" if str_seen else ""


def _notice_declares_review(
	list_notices: list[dict],
	set_roster: set[str],
	tuple_marker_rule: tuple[tuple[str, ...], frozenset[str]],
	str_head_date: str,
	str_head_oid: str,
) -> bool:
	"""Return whether an issue comment declares the head reviewed: a completion or a marker.

	A CLEAN review is not a missing one — see the COMPLETION block above this function.
	``tuple_marker_rule`` is ``(markers, posters)`` as :func:`ladder_marker_declared` takes them.
	"""
	tuple_markers, set_posters = tuple_marker_rule
	return reviewer_declared_completion(
		list_notices, set_roster, str_head_date
	) or ladder_marker_declared(
		list_notices, tuple_markers, str_head_date, str_head_oid, set_posters
	)


def check_missing_review(  # noqa: PLR0913
	list_reviews: list[dict],
	set_reviewers: set[str],
	str_pr_author: str = "",
	*,
	str_head_oid: str,
	list_notices: list[dict] | None = None,
	str_head_date: str = "",
	tuple_markers: tuple[str, ...] = (),
	fn_fingerprint: Callable[[str], str] | None = None,
	set_posters: frozenset[str] = frozenset(),
) -> tuple[str | None, str]:
	"""Return ``(problem, carried_from)`` for a PR no declared reviewer reported on at HEAD.

	Parameters
	----------
	list_reviews : list of dict
		Submitted reviews, each with an ``author`` node and a ``commit`` node.
	set_reviewers : set of str
		Logins that can actually submit a review — :func:`reviewer_logins`, NOT the whole
			roster. ⚠️ Handing this the full roster is the defect it was fixed for: a
			``posts: status`` member both gets NAMED as expected and SATISFIES the check, and
			``github-actions[bot]`` can submit a review with the ambient token.
	str_pr_author : str, optional
		Login of the PR author; a roster member's own PR is exempt.
	str_head_date : str, optional
		ISO-8601 time the head reached GitHub, so a completion notice can be pinned to
			the code it described. ⚠️ Empty fails CLOSED: unknown is not evidence.
	str_head_oid : str, keyword-only
		The PR's ``headRefOid``. ⚠️ Deliberately has NO default, like ``posts:`` on a roster
			row: an empty value silently counts every review whatever code it was written
			against, which is the vacuous pass this parameter exists to remove.
	list_notices : list of dict, optional
		The PR's issue comments, oldest first. Consulted only when nothing reviewed HEAD.
	tuple_markers : tuple of str, optional
		Roster ``comment-marker`` strings; see :func:`ladder_marker_declared`.
	set_posters : frozenset of str, optional
		Roster ``posters:`` logins allowed to post a marker; see :func:`load_marker_posters`.
	fn_fingerprint : Callable[[str], str], optional
		Maps a commit oid to its patch fingerprint. When given, a review at an earlier
			commit covers HEAD if the PR's own patch is unchanged (see
			:func:`review_covers_head`). ``None`` keeps the strict pin to HEAD.

	Returns
	-------
	tuple of (str or None, str)
		A human-readable problem, or ``None`` when a reviewer reported on the head commit
			(or declared those commits already reviewed); and the commit of the carried-forward
			review that satisfied the check, ``""`` when none did, so the caller can show it.
	"""
	set_roster = {normalise_login(s) for s in set_reviewers}
	if normalise_login(str_pr_author) in set_roster:
		return None, ""

	if reviewers_who_reported(list_reviews, set_roster, str_head_oid):
		return None, ""

	if _notice_declares_review(
		list_notices or [], set_roster, (tuple_markers, set_posters), str_head_date, str_head_oid
	):
		return None, ""

	str_carried = review_carried_forward(fn_fingerprint, list_reviews, set_roster, str_head_oid)
	if str_carried:
		return None, str_carried

	str_quote = _notice_quote(list_notices or [], set_roster)

	if reviewers_who_reported(list_reviews, set_roster):
		str_problem = (
			f"a declared reviewer DID review this PR, but only on SUPERSEDED code — no review "
			f"is attributed to the head commit {str_head_oid[:7] or '?'}. A review is pinned to "
			"the commit it was written against and nothing re-pins it when the branch moves, so "
			"the code that would merge has not been looked at. This is NOT 'no review "
			"happened'.\n"
			"Push-triggered re-review is automatic; if it did not fire, ask for a FULL re-review "
			"(a comment such as '@coderabbitai full review' from a user account, which unlike a "
			"plain 'review' disregards what was already reviewed) and re-run this check."
			+ str_quote
		)
		return str_problem, ""

	return _zero_review_message(str_quote, set_roster, list_notices or []), ""


def find_missing_review_problem(  # noqa: PLR0913
	list_reviews: list[dict],
	set_reviewers: set[str],
	str_pr_author: str = "",
	*,
	str_head_oid: str,
	list_notices: list[dict] | None = None,
	str_head_date: str = "",
	tuple_markers: tuple[str, ...] = (),
	fn_fingerprint: Callable[[str], str] | None = None,
	set_posters: frozenset[str] = frozenset(),
) -> str | None:
	"""Return only the problem half of :func:`check_missing_review` (same parameters)."""
	return check_missing_review(
		list_reviews,
		set_reviewers,
		str_pr_author,
		str_head_oid=str_head_oid,
		list_notices=list_notices,
		str_head_date=str_head_date,
		tuple_markers=tuple_markers,
		fn_fingerprint=fn_fingerprint,
		set_posters=set_posters,
	)[0]


def find_thread_problems(
	list_threads: list[dict],
	set_roster: set[str],
	int_min_chars: int = _MIN_REPLY_CHARS,
	*,
	bool_require_resolved: bool = True,
) -> list[str]:
	"""Return one problem per thread that nobody outside the roster answered.

	Parameters
	----------
	list_threads : list of dict
		Review threads as returned by :func:`fetch_pull_request` (its ``reviewThreads``).
	set_roster : set of str
		Logins that count as reviewers rather than as answers.
	int_min_chars : int, optional
		Minimum length for a reply to count as substantive.
	bool_require_resolved : bool, keyword-only, optional
		Whether an answered-but-open thread is a problem. ⚠️ CI passes ``True`` — it used to
			pass ``False`` on the reasoning that a job must not assert what it cannot re-evaluate,
			which delegated the resolve half to a native setting that DROPS an outdated thread.
			See the SUPERSEDED block above ``main`` for the measurement and the accepted cost.

	Returns
	-------
	list of str
		Human-readable problems; empty when every thread carries an answer — and, when
			``bool_require_resolved`` is set, is resolved as well. Both halves are the contract:
			the reply records the reasoning, the resolution records that the exchange is over.
	"""
	set_roster = {normalise_login(s) for s in set_roster}

	list_problems: list[str] = []
	for dict_thread in list_threads:
		list_comments = dict_thread["comments"]["nodes"]
		if not list_comments:
			continue
		list_answers = [
			c
			for c in list_comments
			if normalise_login((c.get("author") or {}).get("login") or "") not in set_roster
			and len((c.get("body") or "").strip()) >= int_min_chars
		]
		str_first = (list_comments[0].get("body") or "").strip().splitlines()
		str_title = next(
			(s for s in str_first if s.startswith("**")),
			str_first[0] if str_first else "",
		).strip("* ")[:90]
		str_path = dict_thread.get("path", "?")

		if not list_answers:
			str_state = "resolved" if dict_thread.get("isResolved") else "open"
			list_problems.append(
				f"{str_path}: thread is {str_state} but nobody outside the "
				f"reviewer roster answered it — {str_title}"
			)
			continue

		if bool_require_resolved and not dict_thread.get("isResolved"):
			str_why = (
				" — this thread is OUTDATED, so the merge button will NOT block on it and "
				"this check is the only thing asserting it"
				if dict_thread.get("isOutdated")
				else ""
			)
			list_problems.append(
				f"{str_path}: thread is answered but NOT resolved — resolve the conversation "
				f"once the reply is posted{str_why} — {str_title}"
			)
	return list_problems


_STR_SEVERITY = r"critical|major|minor|blocker"
_RE_BODY_SEVERITY = re.compile(
	rf"🔴|🟠|🟡|\bseverity\s*:\s*\w"
	rf"|^[^\w\n]*(?:\d+[.)]\s*)?(?:\*\*|\[)\s*(?:{_STR_SEVERITY})\b"
	rf"|^\W*(?:{_STR_SEVERITY})\b\s*[:—-]",
	re.IGNORECASE | re.MULTILINE,
)
_RE_BODY_COUNT = re.compile(
	r"^[^\w\n]*(?:(?:found|posted|reported|with|has|have)\s+)?[1-9]\d*\s+findings?\b",
	re.IGNORECASE | re.MULTILINE,
)
_RE_BODY_HEADING = re.compile(r"^#{1,6}\s*(?:findings|issues|problems)\b", re.I | re.M)
_RE_BODY_REVIEW_LINE = re.compile(
	r"^[^\w\n]*(?:\d+[.)]\s*)?[*_]{0,2}\s*(?:review|findings?)\b"
	r"(?!\s+(?:ladder|skipped|profile|details|status|in progress|completed))",
	re.IGNORECASE | re.MULTILINE,
)
_RE_BODY_SECTION = re.compile(
	r"\b(?:outside diff range|duplicate) comments(?:\s*\((\d+)\))?", re.IGNORECASE
)
_RE_ACTIONABLE = re.compile(
	r"^[ \t*_#-]*actionable comments posted:?[\s*]*\d+", re.IGNORECASE | re.MULTILINE
)
_RE_LADDER_COUNT = re.compile(
	r"^[ \t*_#-]*(\d+)\s+finding\(?s?\)?\s+across\b", re.IGNORECASE | re.MULTILINE
)
_RE_LADDER_HEAD = re.compile(r"^\s*fallback review\s*[—–-]\s*runtime\s*:", re.I | re.M)
_RE_LADDER_META = re.compile(r"^\s*(?:fallback review\b|reviewed head\s*:).*$", re.I | re.M)
_STR_CLEAN_LINE = (
	r"^[^\w\n]*(?:(?:review|findings?|summary|result)\s*[:—–-]\s*)?"
	r"(?:no\s+(?:[\w*-]+\s+){0,2}(?:findings?|issues?|bugs?|problems?)(?:\s+found)?"
	rf"|none(?:\s+found)?"
	rf"|(?:{_STR_SEVERITY}|nitpick|severity)[^\w\n]*(?:none|n/?a|no)"
	r"(?:\s+(?:found|issues?|findings?))?)[^\w\n]*$"
)
_RE_BODY_CLEAN_LINE = re.compile(_STR_CLEAN_LINE, re.I | re.M)
_RE_BODY_CLEAN_SECTION = re.compile(
	r"^#{1,6}\s*(?:findings|issues|problems|review)\b[^\n]*\n(?:[^\S\n]*\n)*" + _STR_CLEAN_LINE,
	re.I | re.M,
)
_RES_BODY_FINDING = (
	_RE_BODY_SEVERITY,
	_RE_BODY_COUNT,
	_RE_BODY_HEADING,
	_RE_BODY_REVIEW_LINE,
)


_RE_QUOTED = re.compile(r"^[ \t]*(?:```|~~~).*?^[ \t]*(?:```|~~~)|^[ \t]*>[^\n]*", re.M | re.S)


_SET_HEADER_AUTHORS = frozenset({"coderabbitai"})
_SET_LADDER_AUTHORS = frozenset({"guilhermegor-review-ladder"})


def _declared_findings(str_body: str, str_login: str = "") -> list[str] | None:
	"""Return the findings a body's own printed counts declare, or ``None`` if it prints none.

	A non-zero body section (outside the diff, duplicates) always counts: it can only add a
	finding. The counts that can CLEAR a body speak only for their author: the ``Actionable``
	header for CodeRabbit (its N findings are inline threads, which the thread check holds), the
	``N finding(s) across`` count for the ladder app and only with the attribution line. Both are
	read with quoted lines and fenced blocks removed. Any other author gets no count authority.
	"""
	list_sections = [
		cls_section.group(0)
		for cls_section in _RE_BODY_SECTION.finditer(str_body)
		if cls_section.group(1) != "0"
	]
	if list_sections:
		return list_sections
	str_author = normalise_login(str_login)
	str_own = _RE_QUOTED.sub("", str_body)
	if str_author in _SET_HEADER_AUTHORS and _RE_ACTIONABLE.search(str_own):
		return []
	cls_count = _RE_LADDER_COUNT.search(str_own)
	is_ladder = str_author in _SET_LADDER_AUTHORS and _RE_LADDER_HEAD.search(str_body)
	if cls_count is None or not is_ladder:
		return None
	return [cls_count.group(0).strip("* \t")] if int(cls_count.group(1)) else []


def _ladder_prose_line(str_text: str) -> list[str]:
	"""Return the first prose line of an uncounted ladder review, which counts as a review."""
	list_prose = [
		str_line.strip()
		for str_line in _RE_LADDER_META.sub("", str_text).splitlines()
		if str_line.strip()
	]
	return list_prose[:1]


def _ladder_empty_findings(str_body: str) -> list[str]:
	"""Return a finding for a ladder review with no prose, unless it says it is clean.

	An attribution line with nothing after it is a truncated or failed review, not a clean one,
	so it fails closed; only an explicit clean line ("No findings.") clears it.
	"""
	if _RE_BODY_CLEAN_LINE.search(str_body):
		return []
	return ["ladder review with no findings count and no clean statement"]


def review_body_finding_lines(str_body: str | None, str_login: str = "") -> list[str]:
	"""Return the lines of a review body that list findings; empty means a clean body.

	Parameters
	----------
	str_body : str or None
		The submitted review's body.
	str_login : str, optional
		The author's login. Printed counts clear a body only for the author they speak
			for (CodeRabbit's header, the ladder app's count); any other author is read by
			structure alone.

	Returns
	-------
	list of str
		Each line carrying a severity marker, a non-zero finding count or a findings
			heading. A line that only reports there are none ("No findings.", "Minor: none")
			and a findings heading directly followed by one are dropped first.
	"""
	list_declared = _declared_findings(str_body or "", str_login)
	if list_declared is not None:
		return list_declared
	str_text = _RE_BODY_CLEAN_LINE.sub("", _RE_BODY_CLEAN_SECTION.sub("", str_body or ""))
	list_lines = [
		str_line.strip()
		for str_line in str_text.splitlines()
		if any(re_.search(str_line) for re_ in _RES_BODY_FINDING)
	]
	if _RE_LADDER_HEAD.search(str_body or ""):
		return list_lines or _ladder_prose_line(str_text) or _ladder_empty_findings(str_body or "")
	return list_lines


def review_body_has_findings(str_body: str | None) -> bool:
	"""Return whether a review body lists findings rather than reporting none.

	Parameters
	----------
	str_body : str or None
		The submitted review's body.

	Returns
	-------
	bool
		``True`` when :func:`review_body_finding_lines` finds at least one line.
	"""
	return bool(review_body_finding_lines(str_body))


def _is_marker_comment(dict_notice: dict, tuple_markers: tuple[str, ...]) -> bool:
	"""Return whether a comment opens with a roster ``comment-marker`` string."""
	return bool(tuple_markers) and (
		(dict_notice.get("body") or "").lstrip().casefold().startswith(tuple_markers)
	)


def _answered_after(
	list_notices: list[dict],
	set_roster: set[str],
	str_when: str,
	int_min_chars: int,
	tuple_markers: tuple[str, ...] = (),
) -> bool:
	"""Return whether a human comment of at least ``int_min_chars`` postdates ``str_when``.

	Bots never answer: GraphQL reports ``__typename`` ``Bot`` (and REST a ``[bot]`` suffix) for
	GitGuardian, ``github-actions`` and the like, and one of those clearing findings unread is
	the #630 failure again. A null author (a deleted "ghost" account) is not a known human
	either, so it fails closed like a missing ``submittedAt``.
	"""
	return bool(str_when) and any(
		_is_human_answer(dict_notice, set_roster, int_min_chars)
		and not _is_marker_comment(dict_notice, tuple_markers)
		and (dict_notice.get("createdAt") or "") > str_when
		for dict_notice in list_notices
	)


_STR_REVIEW_NOUN = (
	r"(?:the\s+|our\s+|my\s+)?(?:(?:ladder|fallback|claude|coderabbit|cli|rung)\s+)*review\b"
)
_RE_ANSWER_SHAPE = re.compile(
	r"^[\s*_#-]*(?:re\s*:|(?:repl(?:y|ies)|answers?|responses?|verdicts?|judg(?:e)?ments?)"
	rf"(?:\s+(?:to|on))?\s*:?)\s*{_STR_REVIEW_NOUN}"
	r"|\b(?:addressed|fixed|resolved)\s+in\s+`?[0-9a-f]{7,40}\b"
	r"|^[^\w\n]*finding\s+\d+\b"
	r"|\breview\s+\d{6,}\b"
	r"|^>[^\n]*\n(?:[^\S\n]*\n)*[^>\s]",
	re.IGNORECASE | re.MULTILINE,
)


def _is_human_answer(dict_notice: dict, set_roster: set[str], int_min_chars: int) -> bool:
	"""Return whether one comment is by a known human outside the roster and reads as an answer."""
	dict_author = dict_notice.get("author") or {}
	str_login = dict_author.get("login") or ""
	str_body = (dict_notice.get("body") or "").strip()
	return (
		bool(str_login)
		and normalise_login(str_login) not in set_roster
		and dict_author.get("__typename", "User") == "User"
		and not str_login.endswith(_BOT_SUFFIX)
		and (len(str_body) >= int_min_chars or bool(_RE_ANSWER_SHAPE.search(str_body)))
	)


def _notices_as_reviews(list_notices: list[dict], set_roster: set[str]) -> list[dict]:
	"""Return the roster's own issue comments in review shape.

	Some ladder rungs post their review as an issue comment, not a PR review. Only a comment that
	declares itself one counts (the ladder attribution line or a CodeRabbit header): status and
	failure notices ("Review ladder: all rungs failed"), walkthroughs and command replies are
	not reviews, whatever their first word is.
	"""
	return [
		{
			"author": dict_notice.get("author"),
			"state": "COMMENTED",
			"body": dict_notice.get("body"),
			"submittedAt": dict_notice.get("createdAt"),
		}
		for dict_notice in list_notices
		if normalise_login((dict_notice.get("author") or {}).get("login") or "") in set_roster
		and any(
			re_.search(dict_notice.get("body") or "")
			for re_ in (_RE_LADDER_HEAD, _RE_ACTIONABLE, _RE_BODY_SECTION)
		)
	]


def _marker_notices_as_reviews(
	list_notices: list[dict], tuple_markers: tuple[str, ...], set_roster: set[str]
) -> list[dict]:
	"""Return trusted ladder-marker comments in review shape, authored by their poster.

	A roster author's marker comment is already returned by :func:`_notices_as_reviews`, so it is
	left out here; counting it twice would report one body as two problems.
	"""
	return [
		{
			"author": dict_notice.get("author"),
			"state": "COMMENTED",
			"body": dict_notice.get("body"),
			"submittedAt": dict_notice.get("createdAt"),
		}
		for dict_notice in list_notices
		if dict_notice.get("authorAssociation") in _SET_TRUSTED_ASSOCIATIONS
		and _is_marker_comment(dict_notice, tuple_markers)
		and normalise_login((dict_notice.get("author") or {}).get("login") or "") not in set_roster
	]


def _count_authority(dict_review: dict, tuple_markers: tuple[str, ...]) -> str:
	"""Return the login whose printed findings count speaks for this review body.

	A trusted marker comment is posted by a person on the ladder's behalf, so its count is read
	with the ladder app's authority; every other review speaks as its own author.
	"""
	if _is_marker_comment(dict_review, tuple_markers):
		return next(iter(_SET_LADDER_AUTHORS))
	return (dict_review.get("author") or {}).get("login") or ""


def find_review_body_problems(
	list_reviews: list[dict],
	list_notices: list[dict],
	set_roster: set[str],
	int_min_chars: int = _MIN_REPLY_CHARS,
	tuple_markers: tuple[str, ...] = (),
) -> list[str]:
	"""Return one problem per roster review whose body lists findings nobody answered.

	Every submitted review counts, not only the head's: inline threads persist across pushes,
	so a body must too, or a trivial push plus a clean re-review would clear it. One reply
	posted after the latest findings body therefore answers all earlier ones; a reply must
	postdate the review it answers. A ``DISMISSED`` review is skipped, the dismissal being the
	maintainer's explicit answer. A roster issue comment that is shaped like a review counts as
	one, since some ladder rungs post that way.

	Parameters
	----------
	list_reviews : list of dict
		Submitted reviews with ``author``, ``state``, ``body`` and ``submittedAt``.
	list_notices : list of dict
		The PR's issue comments, where the author's reply to a review body lands.
	set_roster : set of str
		Logins that count as reviewers rather than as answers.
	int_min_chars : int, optional
		Minimum length for a reply to count, the same bar a thread reply meets.
	tuple_markers : tuple of str, optional
		Roster ``comment-marker`` strings. A trusted comment opening with one is read as a
			review (its findings need an answer) and never counts as an answer itself.

	Returns
	-------
	list of str
		Human-readable problems; empty when every findings body was answered after it was
			submitted. A missing ``submittedAt`` fails closed.
	"""
	set_roster = {normalise_login(str_login) for str_login in set_roster}
	list_hits = [
		(
			dict_review,
			review_body_finding_lines(
				dict_review.get("body"),
				_count_authority(dict_review, tuple_markers),
			),
		)
		for dict_review in list_reviews
		+ _notices_as_reviews(list_notices, set_roster)
		+ _marker_notices_as_reviews(list_notices, tuple_markers, set_roster)
		if dict_review.get("state") != "DISMISSED"
		and (
			normalise_login((dict_review.get("author") or {}).get("login") or "") in set_roster
			or _is_marker_comment(dict_review, tuple_markers)
		)
	]
	return [
		f"{(dict_review.get('author') or {}).get('login')}'s review lists findings in its body "
		f"and nobody outside the reviewer roster (and no bot) replied after it — "
		f"{list_lines[0][:90]}"
		for dict_review, list_lines in list_hits
		if list_lines
		and not _answered_after(
			list_notices,
			set_roster,
			dict_review.get("submittedAt") or "",
			int_min_chars,
			tuple_markers,
		)
	]


def report_verdict(
	list_problems: list[str],
	int_threads: int,
	bool_require_resolved: bool,
) -> int:
	"""Print the verdict and return the exit code.

	Parameters
	----------
	list_problems : list of str
		Problems from :func:`find_thread_problems`.
	int_threads : int
		How many review threads were examined.
	bool_require_resolved : bool
		Whether the resolve half was asserted, so the wording matches what was checked.

	Returns
	-------
	int
		``1`` when there are problems, ``0`` otherwise.
	"""
	for str_problem in list_problems:
		print(f"❌ {str_problem}")
	if list_problems:
		print(
			f"\n{len(list_problems)} of {int_threads} review thread(s) are not finished.\n"
			"A finding takes BOTH halves: REPLY with what changed and why, then RESOLVE the "
			"conversation.\n"
			"- Resolving without replying is not answering: a reviewer bot closes its own threads "
			"when it sees the fix, so the resolved flag records ITS satisfaction, never your "
			"reasoning — and that reasoning is what the next session reads.\n"
			"- Replying without resolving leaves the thread live, so nothing distinguishes a "
			"finished exchange from one still in progress, and the PR can merge with it open."
		)
		return 1
	if not int_threads:
		print("A declared reviewer reported and raised no findings (0 review threads).")
		return 0
	str_scope = "answered and resolved" if bool_require_resolved else "answered"
	print(f"All {int_threads} review thread(s) {str_scope}.")
	return 0


def parse_args(list_argv: list[str] | None = None) -> argparse.Namespace:
	"""Parse this gate's CLI arguments.

	Parameters
	----------
	list_argv : list of str, optional
		Arguments to parse; ``None`` (the default) makes argparse read ``sys.argv[1:]``, so
			``sys.exit(main())`` at the bottom of this file is unaffected.

	Returns
	-------
	argparse.Namespace
		A ``json`` boolean. Every other input stays environment-only (``GITHUB_REPOSITORY``,
			``PR_NUMBER``, ``REVIEW_THREADS_REQUIRE_RESOLVED``) — unchanged by this addition.
	"""
	cls_parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
	cls_parser.add_argument(
		"--json",
		action="store_true",
		help="Emit a machine-readable JSON verdict on stdout instead of prose (default: prose).",
	)
	return cls_parser.parse_args(list_argv)


def _print_skip(bool_json: bool, str_reason: str) -> int:
	"""Print a self-skip in the requested representation and return ``0``."""
	print(json.dumps({"status": "skipped", "reason": str_reason}) if bool_json else str_reason)
	return 0


def _print_missing_review(
	bool_json: bool, str_missing: str, list_notices: list[dict], set_reviewers: set[str]
) -> int:
	"""Print the missing-review failure in the requested representation and return ``1``."""
	if bool_json:
		str_notice = newest_roster_notice(list_notices, set_reviewers)
		print(
			json.dumps(
				{
					"status": "fail",
					"reason": "missing_review",
					"detail": str_missing,
					"notice_classification": classify_reviewer_notice(str_notice),
				}
			)
		)
	else:
		print(f"❌ {str_missing}")
	return 1


def _print_review_body_problems(
	bool_json: bool,
	list_problems: list[str],
	list_thread_problems: list[str] | None = None,
) -> int:
	"""Print the unanswered-review-body failure, with any thread failures too; return ``1``."""
	list_thread_problems = list_thread_problems or []
	if bool_json:
		print(
			json.dumps(
				{
					"status": "fail",
					"reason": "unanswered_review_body",
					"problems": list_problems,
					"thread_problems": list_thread_problems,
				}
			)
		)
		return 1
	for str_problem in list_problems + list_thread_problems:
		print(f"❌ {str_problem}")
	print(
		f"\nReply (at least {_MIN_REPLY_CHARS} characters) on the PR after the review, saying "
		"what changed and why, then re-run this check. A review body has no thread to resolve, "
		"so the reply is the whole answer (blueprintx#630)."
	)
	return 1


def _print_thread_verdict(
	bool_json: bool,
	list_problems: list[str],
	int_threads: int,
	bool_require_resolved: bool,
	str_carried: str = "",
) -> int:
	"""Print the thread verdict in the requested representation and return the exit code.

	A carried-forward review is shown in the verdict itself: a ``carried_forward_from`` field
	under ``--json`` (stdout stays one document), one extra line otherwise.
	"""
	if bool_json:
		dict_verdict = {
			"status": "fail" if list_problems else "pass",
			"threads_examined": int_threads,
			"require_resolved": bool_require_resolved,
			"problems": list_problems,
		}
		if str_carried:
			dict_verdict["carried_forward_from"] = str_carried
		print(json.dumps(dict_verdict))
		return 1 if list_problems else 0
	if str_carried:
		print(f"Review carried forward from {str_carried[:7]} (the PR's own patch is unchanged).")
	return report_verdict(list_problems, int_threads, bool_require_resolved)


def _head_committed_date(dict_pr: dict) -> str:
	"""Return when the head reached GitHub, or ``""`` (fail closed) when that is unknown.

	``committedDate`` is client-set: a commit made before a reviewer's notice and pushed after it
	would let that notice vouch for code it never saw. The EARLIEST check suite on the head is
	created server-side at push (measured on #312: commit 18:06:44, suites from 18:09:49); the
	newest is not, since review events add suites later. The later of the two is returned.
	"""
	dict_commit = ((dict_pr.get("commits", {}).get("nodes") or [{}])[0].get("commit")) or {}
	str_committed = dict_commit.get("committedDate") or ""
	list_suites = [
		d.get("createdAt") or "" for d in (dict_commit.get("checkSuites") or {}).get("nodes") or []
	]
	if not str_committed or not list_suites or not all(list_suites):
		return ""
	return max(str_committed, min(list_suites))


def _unanswered_bodies(dict_pr: dict, list_notices: list[dict], set_roster: set[str]) -> list[str]:
	"""Return :func:`find_review_body_problems` for one fetched ``pullRequest`` node."""
	return find_review_body_problems(
		dict_pr.get("reviews", {}).get("nodes", []),
		list_notices,
		set_roster,
		tuple_markers=load_comment_markers(pathlib.Path.cwd()),
	)


def _parse_time(str_time: str) -> datetime.datetime:
	"""Parse a GitHub ISO-8601 timestamp; raise ``ValueError`` when it is missing or malformed."""
	return datetime.datetime.fromisoformat(str_time.replace("Z", "+00:00"))


def _review_times(
	dict_pr: dict, str_oid: str, set_roster: set[str] | None
) -> list[datetime.datetime]:
	"""Return the submission times of the live roster reviews written against ``str_oid``.

	Dismissed reviews are skipped, as :func:`reviewed_commits` skips them; ``None`` for the
	roster keeps every author.
	"""
	return [
		_parse_time(dict_review.get("submittedAt") or "")
		for dict_review in dict_pr.get("reviews", {}).get("nodes", [])
		if (dict_review.get("commit") or {}).get("oid") == str_oid
		and dict_review.get("state") != "DISMISSED"
		and (
			set_roster is None
			or normalise_login((dict_review.get("author") or {}).get("login") or "") in set_roster
		)
	]


def _reviewed_before_base_change(
	dict_pr: dict, list_changes: list[dict], str_oid: str, set_roster: set[str] | None = None
) -> bool:
	"""Return whether the newest review at ``str_oid`` predates the PR's latest base change.

	Fails closed: an unreadable event time or review time counts as "before". A commit with no
	live roster review (the head, fingerprinted as the comparison target) is not refused. A
	later review on the same commit supersedes an earlier one, so only the newest decides.

	Parameters
	----------
	dict_pr : dict
		The ``pullRequest`` node, read for ``reviews.nodes``.
	list_changes : list of dict
		The base-change timeline events, each carrying ``createdAt``.
	str_oid : str
		The commit being fingerprinted.
	set_roster : set of str, optional
		Already-normalised logins that can submit a review; ``None`` keeps every author.

	Returns
	-------
	bool
		``True`` when the carry-forward must be refused.
	"""
	try:
		dt_change = max(_parse_time(dict_ev.get("createdAt") or "") for dict_ev in list_changes)
		list_times = _review_times(dict_pr, str_oid, set_roster)
	except (ValueError, AttributeError, TypeError):
		return True
	return bool(list_times) and max(list_times) <= dt_change


def _compare_fingerprint(
	dict_pr: dict, str_repo_full: str, set_roster: set[str] | None = None
) -> Callable[[str], str]:
	"""Bind the compare-API fingerprint to this PR's repository and base branch.

	A review written before the latest base change gets no fingerprint: the compare is measured
	against today's base, which is not the base that review was written against. A review
	submitted after that change was, so it carries.

	Parameters
	----------
	dict_pr : dict
		The ``pullRequest`` node, read for ``baseRefOid`` (pinned in the same query as
			``headRefOid``) and ``timelineItems.nodes``, the base-change events.
	str_repo_full : str
		``owner/name``.
	set_roster : set of str, optional
		Already-normalised logins whose reviews count for the base-change comparison.

	Returns
	-------
	Callable[[str], str]
		Maps a commit oid to its patch fingerprint; raises ``ValueError`` when a review at that
			commit predates the latest base change, the event time is unreadable, or the events
			are missing (unknown is not "never retargeted").
	"""
	str_owner, _, str_repo = str_repo_full.partition("/")
	str_base = dict_pr.get("baseRefOid") or ""
	list_changes = (dict_pr.get("timelineItems") or {}).get("nodes")

	def fn_fingerprint(str_oid: str) -> str:
		if not isinstance(list_changes, list):
			raise ValueError("the PR's retarget state is unknown: a review is not carried across")
		if list_changes and _reviewed_before_base_change(
			dict_pr, list_changes, str_oid, set_roster
		):
			raise ValueError("the PR's base branch was changed: a review is not carried across")
		return fetch_patch_fingerprint(str_owner, str_repo, str_base, str_oid)

	return fn_fingerprint


_RE_UPDATE_TYPE = re.compile(r"^\s*update-type:\s*version-update:semver-(\w+)\s*$", re.M)
_RE_DEPENDENCY_NAME = re.compile(r"^\s*-?\s*dependency-name:", re.M)
_SET_EXEMPT_UPDATES = frozenset({"patch", "minor"})
_STR_DEPENDABOT_EMAIL = "+dependabot[bot]@users.noreply.github.com"


def _is_dependabot_commit(dict_node: dict) -> bool:
	"""Return whether one commit is Dependabot's: its email AND a valid GitHub web-flow signature.

	The author email alone is forgeable by any pusher; only GitHub's own signature is not.
	"""
	dict_commit = dict_node.get("commit") or {}
	str_email = (dict_commit.get("author") or {}).get("email") or ""
	dict_sig = dict_commit.get("signature") or {}
	return (
		str_email.endswith(_STR_DEPENDABOT_EMAIL)
		and dict_sig.get("isValid") is True
		and dict_sig.get("wasSignedByGitHub") is True
	)


def _is_dependabot_bot(dict_author: dict) -> bool:
	"""Return whether a PR author node is the ``dependabot`` ``Bot`` actor."""
	return (
		dict_author.get("__typename") == "Bot"
		and normalise_login(dict_author.get("login") or "") == "dependabot"
	)


def dependabot_pushed_head(str_repo_full: str, str_head_oid: str) -> bool:
	"""Return whether every ``pull_request`` run on the head commit was started by Dependabot.

	Commit metadata can be forged by anyone with write access; the actor of the run is who
	pushed. Unreadable, empty or truncated results fail closed.
	"""
	if not str_head_oid:
		return False
	list_cmd = [
		"gh",
		"api",
		f"repos/{str_repo_full}/actions/runs?head_sha={str_head_oid}&event=pull_request&per_page=100",
	]
	try:
		cls_run = subprocess.run(  # noqa: S603
			list_cmd, capture_output=True, text=True, check=False, timeout=_INT_COMPARE_TIMEOUT_S
		)
		dict_out = json.loads(cls_run.stdout)
	except (OSError, ValueError, subprocess.TimeoutExpired):
		return False
	if not isinstance(dict_out, dict):
		return False
	list_runs = dict_out.get("workflow_runs") or []
	if cls_run.returncode != 0 or not list_runs or dict_out.get("total_count") != len(list_runs):
		return False
	return all(((d.get("actor") or {}).get("login") or "") == "dependabot[bot]" for d in list_runs)


def dependabot_review_exempt(
	dict_pr: dict, fn_pusher: Callable[[str], bool] | None = None
) -> bool:
	"""Return whether a PR needs no review: a pure Dependabot patch/minor bump (fail-closed).

	Parameters
	----------
	dict_pr : dict
		The fetched ``pullRequest`` node.
	fn_pusher : Callable[[str], bool], optional
		Maps the head oid to whether Dependabot itself pushed it; ``None`` fails closed.

	Returns
	-------
	bool
		``True`` only for a ``Bot`` author ``dependabot``, pushed by Dependabot, with every
		commit authored and signed by GitHub as Dependabot's and every ``update-type`` in the
		commit metadata a patch or minor.
	"""
	if not _is_dependabot_bot(dict_pr.get("author") or {}):
		return False
	if fn_pusher is None or not fn_pusher(dict_pr.get("headRefOid") or ""):
		return False
	dict_all = dict_pr.get("allCommits") or {}
	list_nodes = dict_all.get("nodes") or []
	if not list_nodes or (dict_all.get("pageInfo") or {}).get("hasNextPage") is not False:
		return False
	if not all(_is_dependabot_commit(dict_node) for dict_node in list_nodes):
		return False
	str_messages = "\n".join(d["commit"].get("message") or "" for d in list_nodes)
	list_types = _RE_UPDATE_TYPE.findall(str_messages)
	if len(list_types) != len(_RE_DEPENDENCY_NAME.findall(str_messages)):
		return False
	return bool(list_types) and set(list_types) <= _SET_EXEMPT_UPDATES


def _missing_review(
	dict_pr: dict,
	str_repo_full: str,
	set_reviewers: set[str],
) -> tuple[str | None, str]:
	"""Return :func:`check_missing_review` for one fetched ``pullRequest`` node."""
	if dependabot_review_exempt(dict_pr, functools.partial(dependabot_pushed_head, str_repo_full)):
		return None, ""
	str_author = (dict_pr.get("author") or {}).get("login") or ""
	return check_missing_review(
		dict_pr.get("reviews", {}).get("nodes", []),
		set_reviewers,
		"" if _borrows_bot_login(dict_pr, set_reviewers) else str_author,
		str_head_oid=dict_pr.get("headRefOid") or "",
		list_notices=dict_pr.get("comments", {}).get("nodes", []),
		str_head_date=_head_committed_date(dict_pr),
		tuple_markers=load_comment_markers(pathlib.Path.cwd()),
		set_posters=load_marker_posters(pathlib.Path.cwd()),
		fn_fingerprint=_compare_fingerprint(
			dict_pr, str_repo_full, {normalise_login(str_login) for str_login in set_reviewers}
		),
	)


def main(list_argv: list[str] | None = None) -> int:
	"""Check the current PR's review threads.

	Parameters
	----------
	list_argv : list of str, optional
		CLI arguments; ``None`` defaults to ``sys.argv[1:]`` — see :func:`parse_args`.

	Returns
	-------
	int
		``0`` when every thread is answered (or the repo declares no roster), ``1`` otherwise.
	"""
	bool_json = parse_args(list_argv).json

	str_repo_full = os.environ.get("GITHUB_REPOSITORY", "")
	str_number = os.environ.get("PR_NUMBER", "")
	if not str_repo_full or not str_number.isdigit():
		return _print_skip(bool_json, "PR_NUMBER / GITHUB_REPOSITORY not set — nothing to check")

	dict_roster = load_roster(pathlib.Path.cwd())
	if not dict_roster:
		return _print_skip(
			bool_json, f"No {_ROSTER_FILE} — the review-thread gate is not adopted here"
		)

	set_roster = set(dict_roster)
	set_reviewers = reviewer_logins(dict_roster)

	str_owner, _, str_repo = str_repo_full.partition("/")
	dict_pr = fetch_pull_request(
		str_owner,
		str_repo,
		int(str_number),
		frozenset(dict_roster) | load_marker_posters(pathlib.Path.cwd()),
	)
	list_threads = dict_pr["reviewThreads"]["nodes"]
	list_notices = dict_pr.get("comments", {}).get("nodes", [])

	str_missing, str_carried = _missing_review(dict_pr, str_repo_full, set_reviewers)
	if str_missing:
		return _print_missing_review(bool_json, str_missing, list_notices, set_reviewers)

	list_body_problems = _unanswered_bodies(dict_pr, list_notices, set_roster)

	bool_require_resolved = os.environ.get("REVIEW_THREADS_REQUIRE_RESOLVED", "1") == "1"
	list_problems = find_thread_problems(
		list_threads, set_roster, bool_require_resolved=bool_require_resolved
	)
	if list_body_problems:
		return _print_review_body_problems(bool_json, list_body_problems, list_problems)

	return _print_thread_verdict(
		bool_json,
		list_problems,
		len(list_threads),
		bool_require_resolved,
		str_carried,
	)


if __name__ == "__main__":
	for cls_stream in (sys.stdout, sys.stderr):
		if hasattr(cls_stream, "reconfigure"):
			cls_stream.reconfigure(encoding="utf-8", errors="replace")

	sys.exit(main())
