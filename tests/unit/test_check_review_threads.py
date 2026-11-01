"""Unit tests for the review-thread answer gate (``bin/check_review_threads.py``).

The should-PASS cases carry the design. Two rules people reach for first — *"only a human may
resolve"* and *"the last comment must be human"* — **fail the best case**, because a good
reviewer bot acknowledges the author's reply and then resolves the thread itself, so its
comment is always last. A gate exercised only on what it rejects has been shown to reject, not
to discriminate.

Every shape here was measured on a real PR (blueprintx#170), including the one that motivated
the gate: 14 threads all reading ``isResolved: true`` while 11 held no author reply at all.
"""

import functools
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
from types import ModuleType
from unittest.mock import Mock, call

import pytest


def _find_gate_path() -> Path:
	"""Locate ``check_review_threads.py``, whether run from the template tree or a scaffold.

	The gate's single source is ``templates/common/bin/`` (blueprintx#175 follow-up), a
	SIBLING of ``templates/python-common/`` — but every scaffold copies it into the
	generated project's own flat ``bin/``, alongside this test file's own copy at
	``tests/unit/``. Both layouts have to resolve from the same test source.

	Returns
	-------
	Path
		Whichever candidate exists. ⚠️ No branch here on purpose — ``tests/`` is capped at
		cyclomatic complexity 1 (`` bin/check_complexity.sh``); an ``if``/``raise`` pair
		would violate that ceiling for a path lookup that is not itself a test. Defaulting
		to the template-tree candidate when neither exists lets a genuinely missing gate
		fail naturally in the loader below, which already reports an absent file clearly.
	"""
	path_here = Path(__file__).resolve()
	tuple_candidates = (
		path_here.parents[2] / "bin" / "check_review_threads.py",
		path_here.parents[3] / "common" / "bin" / "check_review_threads.py",
	)
	return next(
		(path_candidate for path_candidate in tuple_candidates if path_candidate.is_file()),
		tuple_candidates[-1],
	)


def _load_gate() -> ModuleType:
	"""Import ``check_review_threads.py`` as a module.

	Returns
	-------
	ModuleType
		The loaded gate module.
	"""
	path_gate = _find_gate_path()
	cls_spec = importlib.util.spec_from_file_location("_check_review_threads", path_gate)
	assert cls_spec is not None
	assert cls_spec.loader is not None
	cls_module = importlib.util.module_from_spec(cls_spec)
	cls_spec.loader.exec_module(cls_module)
	return cls_module


_ROSTER = {"coderabbitai[bot]", "github-actions[bot]"}

_ROSTER_WITH_POSTS = {"coderabbitai": "threads", "github-actions": "status"}
_LONG = "x" * 150

_HEAD = "9ae76ab0000000000000000000000000000000000"
_SUPERSEDED = "9e7d1fe0000000000000000000000000000000000"

_HEAD_DATE = "2026-01-01T00:00:00Z"


def _thread(list_comments: list[tuple[str, str]], *, bool_resolved: bool = True) -> dict:
	"""Build a review thread from ``(login, body)`` pairs.

	Parameters
	----------
	list_comments : list of tuple of (str, str)
		Author login and comment body, in order.
	bool_resolved : bool, optional
		Whether the thread is marked resolved, by default ``True``.

	Returns
	-------
	dict
		A thread shaped like the GraphQL response.
	"""
	return {
		"isResolved": bool_resolved,
		"isOutdated": False,
		"path": "src/thing.py",
		"comments": {"nodes": [{"author": {"login": a}, "body": b} for a, b in list_comments]},
	}


def _sole(list_problems: list[str]) -> str:
	"""Return the one problem reported, asserting there is exactly one.

	"It fired exactly once" and "it said the right thing" are two claims (blueprintx#544).
	The count is the precondition — indexing ``[0]`` of an empty list raises an
	``IndexError`` naming neither the gate nor the fixture — so it is checked here and each
	test keeps the single assertion that names the behaviour.

	Parameters
	----------
	list_problems : list of str
		Whatever the gate reported.

	Returns
	-------
	str
		The single problem.
	"""
	assert len(list_problems) == 1, list_problems
	return list_problems[0]


def _reported(str_problem: str | None) -> str:
	"""Return a problem string, asserting the gate reported one at all.

	Parameters
	----------
	str_problem : str or None
		The gate's single-problem return, where ``None`` means "no finding".

	Returns
	-------
	str
		The finding.
	"""
	assert str_problem is not None, "the gate reported no problem at all"
	return str_problem


def test_a_thread_the_bot_resolved_alone_is_reported() -> None:
	"""The shape that motivated the gate: resolved by the reviewer, answered by nobody.

	Measured on blueprintx#170 — every thread read ``isResolved: true`` while 11 of 14 held no
	author reply. The resolved flag records the BOT's satisfaction on seeing the commit, never
	the author's reasoning, so keying on it would have passed all 14.
	"""
	cls_gate = _load_gate()
	list_threads = [
		_thread(
			[
				("coderabbitai[bot]", "**Correct the issue count.** " + _LONG),
				("coderabbitai[bot]", "✅ Addressed in commit 65ec2e9"),
			]
		)
	]
	assert "nobody outside the reviewer roster answered it" in _sole(
		cls_gate.find_thread_problems(list_threads, _ROSTER)
	)


def test_a_terse_acknowledgement_is_not_an_answer() -> None:
	"""A one-word acknowledgement records no decision, so it cannot stand in for one.

	The floor is measured rather than invented: real replies ran 100-667 characters (median
	439) on the PR that motivated this, and 356-1126 on an earlier sample.
	"""
	cls_gate = _load_gate()
	list_threads = [
		_thread([("coderabbitai[bot]", "**Finding.** " + _LONG), ("guilhermegor", "done")])
	]
	assert len(cls_gate.find_thread_problems(list_threads, _ROSTER)) == 1


def test_the_bot_may_acknowledge_and_resolve_after_a_real_answer() -> None:
	"""The BEST case must pass: author explains, bot confirms, bot resolves.

	This is why the gate keys on content rather than on resolver identity. "Only a human may
	resolve" fails here, and so does "the last comment must be human" — the bot's
	acknowledgement is always last.
	"""
	cls_gate = _load_gate()
	list_threads = [
		_thread(
			[
				("coderabbitai[bot]", "**Finding.** " + _LONG),
				("guilhermegor", "Corrigido em `65ec2e9`. " + _LONG),
				("coderabbitai[bot]", "Confirmed, the behaviour already covered both cases."),
			]
		)
	]
	assert cls_gate.find_thread_problems(list_threads, _ROSTER) == []


def test_an_answered_but_open_thread_is_now_reported() -> None:
	"""CONTRACT CHANGE: both halves are required — reply AND resolve.

	This test previously asserted the opposite, reasoning that resolving was covered by
	GitHub's ``required_conversation_resolution``. That reasoning holds only where the setting
	is actually enabled, and it was **off on this repo** — which is exactly how a PR merged
	with two live, unanswered threads. Delegating half a rule to a server-side toggle nobody
	verified is how the rule stops existing.

	Both layers now run: this gate fails fast in CI and on pre-push, and the ruleset
	provisioned by ``bin/enable_repo_rules.sh`` blocks the merge button. A thread whose
	discussion genuinely continues is a PR that is not ready to merge, so blocking is correct.
	"""
	cls_gate = _load_gate()
	list_threads = [
		_thread(
			[
				("coderabbitai[bot]", "**Finding.** " + _LONG),
				("guilhermegor", "Discordo, e aqui está o porquê: " + _LONG),
			],
			bool_resolved=False,
		)
	]

	assert "NOT resolved" in _sole(cls_gate.find_thread_problems(list_threads, _ROSTER))


def test_no_threads_is_not_a_THREAD_problem() -> None:
	"""A reviewer posting only a status check leaves no thread — not a THREAD failure.

	Measured: one tool posted five inline threads on a PR while another posted none at all. A
	roster that assumes every reviewer speaks in threads is born broken.

	⚠️ This function's silence on the empty set is correct but is NOT the whole verdict — see
	``find_missing_review_problem``, which owns "there were never any threads because nobody
	reviewed". Keeping the two apart is what lets each say something true.
	"""
	cls_gate = _load_gate()
	assert cls_gate.find_thread_problems([], _ROSTER) == []


def _review(str_login: str, str_oid: str = _HEAD) -> dict:
	"""Build a submitted review authored by ``str_login`` against ``str_oid``.

	Parameters
	----------
	str_login : str
		Review author's login, in either API's spelling.
	str_oid : str
		Commit the review is attributed to; defaults to the PR head.

	Returns
	-------
	dict
		A review shaped like the GraphQL response.
	"""
	return {
		"author": {"login": str_login, "__typename": "Bot"},
		"commit": {"oid": str_oid},
	}


def _notice(str_login: str, str_body: str, str_created: str = "2026-01-02T00:00:00Z") -> dict:
	"""Build one of the PR's issue comments.

	Parameters
	----------
	str_login : str
		Comment author's login.
	str_body : str
		Comment body.
	str_created : str
		ISO-8601 ``createdAt``. Defaults to a date AFTER ``_HEAD_DATE`` so the ordinary case
		reads as "the reviewer spoke about the current head".

	Returns
	-------
	dict
		An issue comment shaped like the GraphQL response.
	"""
	return {"author": {"login": str_login}, "body": str_body, "createdAt": str_created}


def test_a_pr_nobody_reviewed_fails() -> None:
	"""Zero reviews from the roster must FAIL — the case the gate most needs to catch.

	Measured on PR #204: the reviewer was star-gated, posted only its refusal notice, and the
	PR merged with 29 of 30 checks green. Reading threads alone, "found nothing" and "never
	ran" are both zero, and the gate reported the second as ``All 0 review thread(s)
	answered.``
	"""
	cls_gate = _load_gate()
	str_problem = _reported(
		cls_gate.find_missing_review_problem([], _ROSTER, "some-human", str_head_oid=_HEAD)
	)

	assert "never ran" in str_problem, "the message must not read like 'found nothing'"


def test_a_reviewer_that_found_nothing_passes() -> None:
	"""A submitted review with zero threads is a clean PR, not an absent reviewer.

	This is the half that makes the check above safe to require: without it the gate would be
	unsatisfiable on any PR a reviewer genuinely had no findings for.
	"""
	cls_gate = _load_gate()
	assert (
		cls_gate.find_missing_review_problem(
			[_review("coderabbitai")], _ROSTER, "h", str_head_oid=_HEAD
		)
		is None
	)


@pytest.mark.parametrize("str_login", ["coderabbitai", "coderabbitai[bot]"])
def test_the_review_author_spelling_does_not_matter(str_login: str) -> None:
	"""REST and GraphQL disagree on a bot login, and this predicate must survive both.

	The same mismatch made the thread half of this gate permanently green once already.
	"""
	cls_gate = _load_gate()
	assert (
		cls_gate.find_missing_review_problem(
			[_review(str_login)], _ROSTER, "h", str_head_oid=_HEAD
		)
		is None
	)


def test_a_review_from_outside_the_roster_is_not_the_declared_review() -> None:
	"""A passing human comment is not the reviewer this gate was told to expect."""
	cls_gate = _load_gate()
	assert (
		cls_gate.find_missing_review_problem(
			[_review("some-human")], _ROSTER, "h", str_head_oid=_HEAD
		)
		is not None
	)


@pytest.mark.parametrize(
	("str_fragment", "bool_present"),
	[
		("states:[APPROVED, CHANGES_REQUESTED, COMMENTED, DISMISSED]", True),
		("PENDING", False),
	],
	ids=["the-filter-is-present", "and-pending-is-not-in-it"],
)
def test_the_query_excludes_unsubmitted_reviews(str_fragment: str, bool_present: bool) -> None:
	"""A PENDING review must not count as "a reviewer reported".

	Measured on blueprintx#216: opening a draft review and re-querying showed it in the
	``reviews`` connection, so without the ``states:`` filter the gate would read a reporting
	reviewer off something nobody can see — the vacuous pass it exists to remove.

	The filter lives in a GraphQL string that no unit test can execute, so this pins its
	presence instead: cheap, and it fails the moment someone "simplifies" the query.
	"""
	assert (str_fragment in _load_gate()._QUERY) is bool_present


_DICT_PAGE_ONE = {
	"author": {"login": "someone"},
	"reviews": {
		"pageInfo": {"hasNextPage": True, "endCursor": "R1"},
		"nodes": [_review("human")],
	},
	"reviewThreads": {
		"pageInfo": {"hasNextPage": True, "endCursor": "T1"},
		"nodes": [_thread([("coderabbitai", "**A.** " + _LONG)])],
	},
}
_DICT_PAGE_TWO = {
	"author": {"login": "someone"},
	"reviews": {
		"pageInfo": {"hasNextPage": False, "endCursor": None},
		"nodes": [_review("coderabbitai")],
	},
	"reviewThreads": {
		"pageInfo": {"hasNextPage": False, "endCursor": None},
		"nodes": [_thread([("coderabbitai", "**B.** " + _LONG)])],
	},
}


@pytest.fixture(scope="module")  # fixture-scope-ok: immutable fetch result, read-only in 5 tests
def tuple_paged_fetch() -> tuple[ModuleType, dict, Mock]:
	"""Fetch a two-page pull request ONCE and share the gate, the result and the call record.

	Module-scoped because the artifact is immutable and five tests inspect different facets
	of it. ``pytest.MonkeyPatch.context()`` rather than the ``monkeypatch`` fixture, which is
	function-scoped and cannot be requested from here.

	Returns
	-------
	tuple of (ModuleType, dict, unittest.mock.Mock)
		The loaded gate, the merged pull request, and the page-fetch mock.
	"""
	cls_gate = _load_gate()
	cls_page = Mock(side_effect=[_DICT_PAGE_ONE, _DICT_PAGE_TWO])
	with pytest.MonkeyPatch.context() as cls_patch:
		cls_patch.setattr(cls_gate, "_fetch_page", cls_page)
		dict_pr = cls_gate.fetch_pull_request("o", "r", 1)
	return cls_gate, dict_pr, cls_page


def test_the_second_page_is_requested_with_both_cursors(
	tuple_paged_fetch: tuple[ModuleType, dict, Mock],
) -> None:
	"""``first:100`` is a CAP, not "all" — page two must actually be asked for.

	Parameters
	----------
	tuple_paged_fetch : tuple of (ModuleType, dict, unittest.mock.Mock)
		The shared two-page fetch.
	"""
	_, _, cls_page = tuple_paged_fetch

	assert [tuple_args[3:5] for tuple_args, _ in cls_page.call_args_list] == [
		(None, None),
		("R1", "T1"),
	]


def test_page_two_reviews_are_merged_in(
	tuple_paged_fetch: tuple[ModuleType, dict, Mock],
) -> None:
	"""Truncated REVIEWS cause a false failure — the merge is what prevents it.

	Parameters
	----------
	tuple_paged_fetch : tuple of (ModuleType, dict, unittest.mock.Mock)
		The shared two-page fetch.
	"""
	_, dict_pr, _ = tuple_paged_fetch

	assert len(dict_pr["reviews"]["nodes"]) == 2


def test_page_two_threads_are_merged_in(
	tuple_paged_fetch: tuple[ModuleType, dict, Mock],
) -> None:
	"""⚠️ Truncated THREADS are the worse half, and not what the review flagged.

	Thread 101 is simply never examined and the gate prints "All 100 ... answered" over
	unfinished conversations — the false pass this whole file exists to eliminate.

	Parameters
	----------
	tuple_paged_fetch : tuple of (ModuleType, dict, unittest.mock.Mock)
		The shared two-page fetch.
	"""
	_, dict_pr, _ = tuple_paged_fetch

	assert len(dict_pr["reviewThreads"]["nodes"]) == 2


def test_the_merged_reviews_reach_the_missing_review_verdict(
	tuple_paged_fetch: tuple[ModuleType, dict, Mock],
) -> None:
	"""The roster review is served ONLY on page two — unpaginated, this PR reads as unreviewed.

	Parameters
	----------
	tuple_paged_fetch : tuple of (ModuleType, dict, unittest.mock.Mock)
		The shared two-page fetch.
	"""
	cls_gate, dict_pr, _ = tuple_paged_fetch

	assert (
		cls_gate.find_missing_review_problem(
			dict_pr["reviews"]["nodes"], _ROSTER, "someone", str_head_oid=_HEAD
		)
		is None
	)


def test_the_merged_threads_reach_the_thread_verdict(
	tuple_paged_fetch: tuple[ModuleType, dict, Mock],
) -> None:
	"""Both pages' threads must be judged, not only the first page's.

	Parameters
	----------
	tuple_paged_fetch : tuple of (ModuleType, dict, unittest.mock.Mock)
		The shared two-page fetch.
	"""
	cls_gate, dict_pr, _ = tuple_paged_fetch

	assert len(cls_gate.find_thread_problems(dict_pr["reviewThreads"]["nodes"], _ROSTER)) == 2


def test_a_roster_members_own_pr_is_exempt() -> None:
	"""A reviewer's own PR cannot require itself to review it.

	A gate nobody can satisfy is one people learn to bypass with ``--admin``, and the bypass
	habit swallows the real blocks too.
	"""
	cls_gate = _load_gate()
	assert (
		cls_gate.find_missing_review_problem([], _ROSTER, "coderabbitai[bot]", str_head_oid=_HEAD)
		is None
	)


def test_an_absent_roster_makes_the_gate_a_no_op(tmp_path: Path) -> None:
	"""Without a declared roster the gate cannot tell a finding from an answer, so it skips.

	Guessing at logins would produce false failures on the repos that never adopted it.
	"""
	cls_gate = _load_gate()
	assert cls_gate.load_roster(tmp_path) == {}


def test_an_absent_roster_is_absent_even_when_a_hook_exports_git_dir(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Inside a git hook ``GIT_DIR`` outranks ``-C``; the lookup must not follow it.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest throwaway dir: a repo holding the roster on ``origin/main``, and an unrelated dir.
	monkeypatch : pytest.MonkeyPatch
		Sets the ``GIT_DIR`` a pre-commit hook would export.
	"""
	path_repo = tmp_path / "repo"
	path_repo.mkdir()
	_git(path_repo, "init", "-q")
	_commit(path_repo, ".review-bots.yaml", _STR_OTHER_ROSTER)
	_git(path_repo, "update-ref", "refs/remotes/origin/main", "HEAD")
	path_other = tmp_path / "other"
	path_other.mkdir()
	monkeypatch.setenv("GIT_DIR", str(path_repo / ".git"))

	assert _load_gate().load_roster(path_other) == {}


_STR_OTHER_ROSTER = "reviewers:\n  - login: some-other-reviewer[bot]\n    posts: threads\n"


def test_the_roster_is_read_from_the_declared_file(tmp_path: Path) -> None:
	"""The roster is data. No reviewer is named in the gate's logic, so swapping tools is a row.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest throwaway dir holding the roster file.
	"""
	cls_gate = _load_gate()
	(tmp_path / ".review-bots.yaml").write_text(_STR_OTHER_ROSTER, encoding="utf-8")

	assert cls_gate.load_roster(tmp_path) == {"some-other-reviewer": "threads"}, (
		"logins are normalised on load: GraphQL omits the bot-login suffix a declared "
		"reviewer carries, and comparing those spellings literally made this gate vacuous"
	)


def test_a_swapped_in_reviewer_is_policed_like_any_other(tmp_path: Path) -> None:
	"""Reading the roster is half the claim; behaving the same for its members is the other.

	Split from its sibling rather than folded in (blueprintx#544): a gate that PARSES a
	swapped-in reviewer but never applies the rule to it would pass the first claim alone.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest throwaway dir holding the roster file.
	"""
	cls_gate = _load_gate()
	(tmp_path / ".review-bots.yaml").write_text(_STR_OTHER_ROSTER, encoding="utf-8")
	list_threads = [_thread([("some-other-reviewer[bot]", "**Finding.** " + _LONG)])]

	set_roster = set(cls_gate.load_roster(tmp_path))
	assert len(cls_gate.find_thread_problems(list_threads, set_roster)) == 1


def test_an_unreachable_api_is_not_mistaken_for_a_clean_pr(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""A failed query raises instead of returning an empty list.

	Returning ``[]`` on error would make an outage indistinguishable from "no threads" — the
	job reporting its own blindness as all-clear.

	``_fetch_page`` is the subprocess boundary — it shells out to the real ``gh`` binary and
	the live network (blueprintx#201). Mocking it here, the way ``test_both_connections_are_
	paginated`` already mocks it above, keeps this a UNIT test: no ``gh`` on PATH and no
	network required. It still proves the real property — ``fetch_pull_request`` PROPAGATES a
	page failure rather than swallowing it, which is exactly what ``gh`` returning a non-zero
	exit would trigger in ``_fetch_page`` (see its own ``RuntimeError`` there).

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Used to replace ``_fetch_page`` with a mock that raises, standing in for a real
		``gh`` failure without touching a binary or the wire.
	"""
	cls_gate = _load_gate()
	cls_page = Mock(
		spec=cls_gate._fetch_page,
		side_effect=RuntimeError("GraphQL query failed: simulated non-zero gh exit"),
	)
	monkeypatch.setattr(cls_gate, "_fetch_page", cls_page)
	with pytest.raises(RuntimeError):
		cls_gate.fetch_pull_request("no-such-owner-xyz", "no-such-repo-xyz", 1)


@pytest.mark.parametrize(
	("str_login", "str_normalised"),
	[
		("coderabbitai[bot]", "coderabbitai"),
		("coderabbitai", "coderabbitai"),
		("guilhermegor", "guilhermegor"),
	],
	ids=["rest-spelling", "graphql-spelling", "a-human-is-untouched"],
)
def test_graphql_drops_the_bot_suffix_that_the_roster_carries(
	str_login: str, str_normalised: str
) -> None:
	"""REST says ``coderabbitai[bot]``; GraphQL's ``author.login`` says ``coderabbitai``.

	The roster is written in the REST spelling because that is what GitHub shows everywhere
	else, but this gate reads GraphQL. A literal comparison therefore NEVER matched, so every
	reviewer comment counted as an "answer" and the gate reported "all threads answered" on a
	PR where nobody had replied to anything — permanently, silently green.

	⚠️ The existing fixtures could not catch it: they spell the login ``coderabbitai[bot]``,
	i.e. the test and the code shared the same wrong assumption about the data, and only
	production disagreed. These fixtures use the spelling GraphQL actually returns.
	"""
	assert _load_gate().normalise_login(str_login) == str_normalised


def test_a_reviewer_comment_in_graphql_spelling_is_not_an_answer(tmp_path: Path) -> None:
	"""The production shape: roster in REST spelling, thread authors in GraphQL spelling.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest throwaway dir holding the roster file.
	"""
	cls_gate = _load_gate()
	(tmp_path / ".review-bots.yaml").write_text(
		"reviewers:\n  - login: coderabbitai[bot]\n    posts: threads\n",
		encoding="utf-8",
	)
	set_roster = cls_gate.load_roster(tmp_path)

	list_threads = [_thread([("coderabbitai", "**Finding.** " + _LONG)])]
	assert len(cls_gate.find_thread_problems(list_threads, set_roster)) == 1


def test_a_human_reply_in_the_same_thread_still_answers_it(tmp_path: Path) -> None:
	"""The positive half: normalisation must not make every thread unanswerable.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest throwaway dir holding the roster file.
	"""
	cls_gate = _load_gate()
	(tmp_path / ".review-bots.yaml").write_text(
		"reviewers:\n  - login: coderabbitai[bot]\n    posts: threads\n",
		encoding="utf-8",
	)
	set_roster = cls_gate.load_roster(tmp_path)

	list_threads = [_thread([("coderabbitai", "**Finding.** " + _LONG), ("guilhermegor", _LONG)])]
	assert cls_gate.find_thread_problems(list_threads, set_roster) == []


def test_an_answered_but_unresolved_thread_is_reported(tmp_path: Path) -> None:
	"""Replying is half the job — an open thread lets a PR merge mid-conversation.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest throwaway dir holding the roster file.
	"""
	cls_gate = _load_gate()
	(tmp_path / ".review-bots.yaml").write_text(
		"reviewers:\n  - login: coderabbitai[bot]\n    posts: threads\n",
		encoding="utf-8",
	)
	set_roster = cls_gate.load_roster(tmp_path)

	list_threads = [
		_thread(
			[("coderabbitai", "**Finding.** " + _LONG), ("guilhermegor", _LONG)],
			bool_resolved=False,
		)
	]

	assert "NOT resolved" in _sole(cls_gate.find_thread_problems(list_threads, set_roster))


def test_deleting_the_roster_is_not_a_silent_opt_out(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""An absent roster means "never adopted" — unless the default branch still carries it.

	An empty roster makes the gate a no-op, so `rm .review-bots.yaml` is a one-line way to
	switch the gate off from inside the very PR it is meant to police. When git can prove the
	file exists on the default branch, its absence here is a DELETION and must be loud.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest throwaway dir standing in for a checkout with no roster.
	monkeypatch : pytest.MonkeyPatch
		Used to stub the default-branch probe, so the test needs no real remote.
	"""
	cls_gate = _load_gate()
	monkeypatch.setattr(cls_gate, "_roster_exists_on_default_branch", lambda _p: True)

	with pytest.raises(RuntimeError, match="disables this gate"):
		cls_gate.load_roster(tmp_path)


def test_a_roster_never_adopted_is_still_a_silent_no_op(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""The positive control for the test above — and the reason it needs one.

	"Absent" means two different things depending on the default branch, and a gate that
	failed on BOTH would stop being opt-in for every other repo. Split out rather than left
	as a second assert (blueprintx#544): these are opposite verdicts over the same input,
	which is the clearest case there is for two tests.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest throwaway dir standing in for a checkout with no roster.
	monkeypatch : pytest.MonkeyPatch
		Used to stub the default-branch probe, so the test needs no real remote.
	"""
	cls_gate = _load_gate()
	monkeypatch.setattr(cls_gate, "_roster_exists_on_default_branch", lambda _p: False)

	assert cls_gate.load_roster(tmp_path) == {}


_LIST_OPEN_BUT_ANSWERED = [
	_thread(
		[("coderabbitai", "**Finding.** " + _LONG), ("guilhermegor", _LONG)],
		bool_resolved=False,
	)
]
_LIST_UNANSWERED = [_thread([("coderabbitai", "**Finding.** " + _LONG)])]


def test_the_resolve_half_can_still_be_switched_off_by_flag() -> None:
	"""CI mode tolerates an open-but-answered thread — it could not tell you when it was fixed."""
	assert (
		_load_gate().find_thread_problems(
			_LIST_OPEN_BUT_ANSWERED, _ROSTER, bool_require_resolved=False
		)
		== []
	)


def test_local_mode_still_catches_an_unresolved_thread() -> None:
	"""A local run is always current, so it keeps the half CI gave up."""
	assert len(_load_gate().find_thread_problems(_LIST_OPEN_BUT_ANSWERED, _ROSTER)) == 1


def test_switching_off_the_resolve_half_does_not_disable_the_reply_half() -> None:
	"""⚠️ The half CI DOES own must still fire, or the flag silently turns the job off.

	This is the claim a three-assert test hides: the first two say the flag changes
	something, and only this one says it did not change everything.
	"""
	assert (
		len(
			_load_gate().find_thread_problems(
				_LIST_UNANSWERED, _ROSTER, bool_require_resolved=False
			)
		)
		== 1
	)


def test_a_status_only_member_cannot_satisfy_the_missing_review_gate() -> None:
	"""The negative control: a review by a ``posts: status`` member is not a review.

	``github-actions[bot]`` can submit a review with the ambient ``GITHUB_TOKEN``, so before
	this split any workflow that posted one satisfied a gate whose entire purpose is "a real
	reviewer looked at this" — the same class of hole as #208, reached from the other side.
	"""
	cls_gate = _load_gate()
	set_reviewers = cls_gate.reviewer_logins(_ROSTER_WITH_POSTS)
	assert cls_gate.find_missing_review_problem(
		[_review("github-actions")], set_reviewers, "h", str_head_oid=_HEAD
	)


def test_the_missing_review_message_names_only_members_that_can_review() -> None:
	"""The gate must not tell people to wait for a member that never submits a review."""
	cls_gate = _load_gate()
	set_reviewers = cls_gate.reviewer_logins(_ROSTER_WITH_POSTS)
	assert "github-actions" not in cls_gate.find_missing_review_problem(
		[], set_reviewers, "h", str_head_oid=_HEAD
	)


def test_a_thread_answer_from_a_status_member_is_still_not_an_answer() -> None:
	"""The THREAD half keeps the whole roster — a status member's comment is not the author's.

	The two halves take different sets on purpose, and this pins the half that must NOT narrow.
	"""
	cls_gate = _load_gate()
	list_threads = [
		_thread([("coderabbitai", "**Finding.** " + _LONG), ("github-actions", _LONG)])
	]
	assert len(cls_gate.find_thread_problems(list_threads, set(_ROSTER_WITH_POSTS))) == 1


def test_reviewer_logins_keeps_only_the_threads_members() -> None:
	"""The split itself, asserted directly rather than only through its two consumers."""
	cls_gate = _load_gate()
	assert cls_gate.reviewer_logins(_ROSTER_WITH_POSTS) == {"coderabbitai"}


def test_a_roster_where_nobody_can_review_fails_loudly() -> None:
	"""A roster of only status members makes the gate unsatisfiable, so it must not load.

	A required check that can never go green is the fastest way to teach people that red
	means nothing — and the bypass habit that follows swallows the real blocks too.
	"""
	cls_gate = _load_gate()
	with pytest.raises(RuntimeError, match="no member with posts"):
		cls_gate.reviewer_logins({"github-actions": "status"})


def test_a_row_without_posts_is_rejected_rather_than_defaulted(tmp_path: Path) -> None:
	"""Neither default is safe, so the roster must say. See ``posts_of``.

	Reading a forgotten field as ``status`` makes the gate unsatisfiable; reading it as
	``threads`` re-opens the exact hole the field exists to close.
	"""
	cls_gate = _load_gate()
	(tmp_path / ".review-bots.yaml").write_text(
		"reviewers:\n  - login: some-reviewer[bot]\n", encoding="utf-8"
	)
	with pytest.raises(RuntimeError, match="some-reviewer"):
		cls_gate.load_roster(tmp_path)


def test_an_unrecognised_posts_value_is_rejected(tmp_path: Path) -> None:
	"""A typo'd classification must name itself, not fall through to a silent behaviour."""
	cls_gate = _load_gate()
	(tmp_path / ".review-bots.yaml").write_text(
		"reviewers:\n  - login: some-reviewer[bot]\n    posts: reviews\n", encoding="utf-8"
	)
	with pytest.raises(RuntimeError, match="reviews"):
		cls_gate.load_roster(tmp_path)


def test_a_status_member_opening_a_pr_is_not_exempt() -> None:
	"""The exemption is "do not ask X to review X", never "bots are exempt".

	``github-actions[bot]`` opens workflow PRs and cannot review, so a real reviewer can look
	at its PR and there is nothing unsatisfiable about asking.
	"""
	cls_gate = _load_gate()
	set_reviewers = cls_gate.reviewer_logins(_ROSTER_WITH_POSTS)
	assert cls_gate.find_missing_review_problem(
		[], set_reviewers, "github-actions[bot]", str_head_oid=_HEAD
	)


def test_an_emptied_roster_is_rejected_like_a_deleted_one(tmp_path: Path) -> None:
	"""``reviewers: []`` is the deletion guard's hole, reached with different keystrokes.

	The file is present, so the default-branch deletion check never fires, and an empty result
	reads to ``main`` as "not adopted here" — a gate switched off inside the very PR it polices.
	Opting out is deleting the file, which self-skips with a message. Raised by review on #262.
	"""
	cls_gate = _load_gate()
	(tmp_path / ".review-bots.yaml").write_text("reviewers: []\n", encoding="utf-8")
	with pytest.raises(RuntimeError, match="declares no reviewers"):
		cls_gate.load_roster(tmp_path)


def test_a_review_of_a_superseded_commit_does_not_satisfy_the_gate() -> None:
	"""The negative control: this input PASSED before the head check existed.

	Measured on blueprintx#219 while the gate was first being exercised: ``head=9ae76ab`` and the
	PR's only review attributed to ``9e7d1fe``, a commit superseded five minutes earlier. Both
	trigger runs had fired and both succeeded — triggering a review is necessary and NOT
	sufficient, because nothing checked what came back was about the current code.
	"""
	cls_gate = _load_gate()
	assert (
		cls_gate.find_missing_review_problem(
			[_review("coderabbitai", _SUPERSEDED)], _ROSTER, "h", str_head_oid=_HEAD
		)
		is not None
	)


def test_a_review_of_the_head_commit_satisfies_the_gate() -> None:
	"""The should-PASS half: the check must discriminate, not merely reject.

	Without this, tightening the predicate to "no review ever counts" would also go green.
	"""
	cls_gate = _load_gate()
	assert (
		cls_gate.find_missing_review_problem(
			[_review("coderabbitai", _HEAD)], _ROSTER, "h", str_head_oid=_HEAD
		)
		is None
	)


def test_reviewed_older_code_and_never_reviewed_print_different_sentences() -> None:
	"""Two facts with different remedies must not print identically.

	This is the defect #208 rewrote this message for once already, one level up: "the reviewer
	ran, on older code" tells you to wait for the push-triggered re-review, while "no reviewer
	ever ran" tells you to trigger one. A reader given the wrong sentence wastes the trigger.
	"""
	cls_gate = _load_gate()
	str_stale = cls_gate.find_missing_review_problem(
		[_review("coderabbitai", _SUPERSEDED)], _ROSTER, "h", str_head_oid=_HEAD
	)
	assert "SUPERSEDED" in str_stale, "the stale-review message must not read like 'no review'"


def test_the_stale_review_message_names_the_head_commit() -> None:
	"""A message that cannot be acted on is a message nobody reads.

	Naming the head oid is what lets a reader compare it against the review's own attribution
	on the PR page, rather than taking the gate's word for it.
	"""
	cls_gate = _load_gate()
	str_stale = cls_gate.find_missing_review_problem(
		[_review("coderabbitai", _SUPERSEDED)], _ROSTER, "h", str_head_oid=_HEAD
	)
	assert _HEAD[:7] in str_stale


def test_the_query_asks_for_the_commit_each_review_was_written_against() -> None:
	"""The head check is worthless if the field stops being fetched.

	The query is a GraphQL string no unit test can execute, so its content is pinned here —
	the same technique that guards the ``states:`` filter against a well-meant simplification.
	"""
	cls_gate = _load_gate()
	assert "commit { oid }" in cls_gate._QUERY


def test_the_query_asks_for_the_head_commit() -> None:
	"""Without ``headRefOid`` there is nothing to compare a review's commit against."""
	cls_gate = _load_gate()
	assert "headRefOid" in cls_gate._QUERY


_FOOTNOTE = (
	"> Note: CodeRabbit is an incremental review system and does not re-review already "
	"reviewed commits. This command is applicable only when automatic reviews are paused."
)
_NOTICE_PERFORMED = (
	f"<summary>\u2705 Action performed</summary>\n\nReview finished.\n\n{_FOOTNOTE}"
)
_NOTICE_LIMITED = (
	f"<summary>\u26a0\ufe0f Action not completed</summary>\n\nReview rate limited.\n\n{_FOOTNOTE}"
)
_NOTICE_FAILED = f"<summary>\u274c Action failed</summary>\n\nReview failed.\n\n{_FOOTNOTE}"


def test_a_declared_completion_is_evidence_the_reviewer_ran() -> None:
	"""A reviewer that ran and found nothing produces no review object — only a notice.

	CodeRabbit emits a formal review ONLY when it has line comments to attach, so a clean
	review leaves ``reviews == 0`` and ``threads == 0`` — byte for byte identical to "never
	ran", which the gate must keep failing. The completion LINE is the discriminator, measured
	2026-08-29 against the counter-examples that killed the broad version::

			#204 merged unreviewed  reviews=0  phrase=0  -> still fails
			#213 merged unreviewed  reviews=0  phrase=0  -> still fails
			#328 reviewed, clean    reviews=0  phrase=1  -> now passes

	⚠️ Evidence the review HAPPENED, never that a thread was answered — thread strictness is
	untouched. See blueprintx#336.
	"""
	cls_gate = _load_gate()
	assert (
		cls_gate.find_missing_review_problem(
			[],
			_ROSTER,
			"h",
			str_head_oid=_HEAD,
			str_head_date=_HEAD_DATE,
			list_notices=[_notice("coderabbitai", _NOTICE_PERFORMED)],
		)
		is None
	)


def test_a_completion_predating_the_head_commit_is_not_evidence() -> None:
	"""H1/H2: a completion notice must POSTDATE the head commit it is offered as evidence for.

	A notice carries no commit oid, unlike a review object. So a reviewer that finished on H1,
	followed by a push to H2, leaves the newest roster notice reading "Review finished" while
	nothing has looked at H2. Raised by review on blueprintx#339, which is where this had been
	written down as a known limitation instead of being closed.
	"""
	cls_gate = _load_gate()
	assert (
		cls_gate.find_missing_review_problem(
			[],
			_ROSTER,
			"h",
			str_head_oid=_HEAD,
			str_head_date="2026-06-01T00:00:00Z",
			list_notices=[
				_notice("coderabbitai", _NOTICE_PERFORMED, "2026-05-01T00:00:00Z"),
			],
		)
		is not None
	)


def test_an_unknown_head_date_is_not_evidence() -> None:
	"""Fails CLOSED: without the head commit's date, a completion notice cannot be pinned.

	An absent ``committedDate`` means the query changed or the payload is partial. Treating
	unknown as "recent enough" is the vacuous pass this whole file exists to remove.
	"""
	cls_gate = _load_gate()
	assert (
		cls_gate.find_missing_review_problem(
			[],
			_ROSTER,
			"h",
			str_head_oid=_HEAD,
			str_head_date="",
			list_notices=[_notice("coderabbitai", _NOTICE_PERFORMED)],
		)
		is not None
	)


def _pr_head(str_committed: str, *list_suites: str) -> dict:
	"""Return a ``pullRequest`` node whose head carries a commit date and check suites."""
	list_nodes = [{"createdAt": s} for s in list_suites]
	dict_commit = {"committedDate": str_committed, "checkSuites": {"nodes": list_nodes}}
	return {"commits": {"nodes": [{"commit": dict_commit}]}}


@pytest.mark.parametrize(
	("dict_pr", "str_expected"),
	[
		# committed 18:06, pushed 18:09, a review-event suite at 18:23 (#312): push time wins
		(
			_pr_head("2026-10-31T18:06:44Z", "2026-10-31T18:23:17Z", "2026-10-31T18:09:49Z"),
			"2026-10-31T18:09:49Z",
		),
		# a forward-dated committedDate is stricter than the push, so it is kept
		(_pr_head("2026-11-01T00:00:00Z", "2026-10-31T18:09:49Z"), "2026-11-01T00:00:00Z"),
		# without any server-side timestamp the date is unknown and the gate fails closed
		(_pr_head("2026-10-31T18:06:44Z"), ""),
		({"commits": {"nodes": []}}, ""),
	],
)
def test_head_date_is_the_push_not_the_client_set_commit_date(
	dict_pr: dict, str_expected: str
) -> None:
	"""A commit made before a reviewer's notice and pushed after it is not vouched for by it."""
	assert _load_gate()._head_committed_date(dict_pr) == str_expected


def test_a_superseded_completion_does_not_satisfy_the_gate() -> None:
	"""Only the NEWEST roster notice counts — a stale completion outlives what it described.

	The reviewer finishing on an older commit and then being turned away on the current one
	leaves both notices in the stream. Reading "any notice ever" passes that PR while its head
	commit has never been looked at. Caught by this test during blueprintx#336.
	"""
	cls_gate = _load_gate()
	assert (
		cls_gate.find_missing_review_problem(
			[],
			_ROSTER,
			"h",
			str_head_oid=_HEAD,
			str_head_date=_HEAD_DATE,
			list_notices=[
				_notice("coderabbitai", _NOTICE_PERFORMED),
				_notice("coderabbitai", _NOTICE_LIMITED),
			],
		)
		is not None
	)


@pytest.mark.parametrize(
	"str_notice",
	[_FOOTNOTE, _NOTICE_LIMITED, _NOTICE_FAILED],
	ids=["footnote_only", "rate_limited", "failed"],
)
def test_the_already_reviewed_footnote_never_satisfies_the_gate(str_notice: str) -> None:
	"""The negative control for the defect this check shipped with and review caught.

	"does not re-review already reviewed commits" is a STANDING FOOTNOTE about how the product
	works, appended to every outcome — not a statement about this PR. Keying a pass on it made a
	rate-limited and an outright FAILED review read as "declined as redundant". Measured on
	blueprintx#264 by reading its own comment stream: all three notices carry it verbatim.

	⚠️ The ``performed`` case MOVED to
	:func:`test_a_declared_completion_is_evidence_the_reviewer_ran` in blueprintx#336, and the
	distinction is the point: this test protects against keying a pass on the FOOTNOTE, which
	every outcome carries. A completion LINE is carried by exactly one outcome, so it
	discriminates where the footnote cannot. The footnote-only case is parametrised here to
	keep that original protection under test on its own, without a completion line to carry it.

	Parameters
	----------
	str_notice : str
		A notice that must NOT satisfy the gate, copied from the measured stream.
	"""
	cls_gate = _load_gate()
	assert (
		cls_gate.find_missing_review_problem(
			[],
			_ROSTER,
			"h",
			str_head_oid=_HEAD,
			str_head_date=_HEAD_DATE,
			list_notices=[_notice("coderabbitai", str_notice)],
		)
		is not None
	)


def test_the_failure_message_quotes_the_reviewers_latest_notice() -> None:
	"""The notice is worth SHOWING even though it is not worth trusting.

	`reviews == 0` collapses states with different remedies — never ran, refused, rate-limited,
	declined. The reader cannot tell which without the reviewer's own words, so they are quoted;
	the verdict is unaffected.
	"""
	cls_gate = _load_gate()
	str_problem = cls_gate.find_missing_review_problem(
		[],
		_ROSTER,
		"h",
		str_head_oid=_HEAD,
		str_head_date=_HEAD_DATE,
		list_notices=[_notice("coderabbitai", _NOTICE_LIMITED)],
	)
	assert "Review rate limited." in str_problem


def test_the_quoted_notice_is_stripped_of_markup() -> None:
	"""A notice pasted raw drags hidden HTML markers into a CI log nobody can read."""
	cls_gate = _load_gate()
	str_problem = cls_gate.find_missing_review_problem(
		[],
		_ROSTER,
		"h",
		str_head_oid=_HEAD,
		str_head_date=_HEAD_DATE,
		list_notices=[_notice("coderabbitai", _NOTICE_FAILED)],
	)
	assert "<summary>" not in str_problem


def test_only_a_roster_notice_is_quoted() -> None:
	"""A comment from anyone else is not the reviewer's word about its own run."""
	cls_gate = _load_gate()
	str_problem = cls_gate.find_missing_review_problem(
		[],
		_ROSTER,
		"h",
		str_head_oid=_HEAD,
		str_head_date=_HEAD_DATE,
		list_notices=[_notice("some-human", "these commits were already reviewed on the old PR")],
	)
	assert "already reviewed on the old PR" not in str_problem


def test_the_newest_roster_notice_is_the_one_quoted() -> None:
	"""An older notice describes a state the reviewer has since superseded."""
	cls_gate = _load_gate()
	str_problem = cls_gate.find_missing_review_problem(
		[],
		_ROSTER,
		"h",
		str_head_oid=_HEAD,
		str_head_date=_HEAD_DATE,
		list_notices=[
			_notice("coderabbitai", _NOTICE_PERFORMED),
			_notice("coderabbitai", _NOTICE_LIMITED),
		],
	)
	assert "Review rate limited." in str_problem


def test_the_remedy_names_a_full_review_not_an_incremental_one() -> None:
	"""An incremental reviewer answers "already reviewed" on commits seen on another PR.

	#259 argued this gate would be unsatisfiable because the remedy it printed was the command
	that fails. A different documented command does not: `@coderabbitai full review` "disregards
	any comments that CodeRabbit has already made on this pull request, and generates a complete
	review of the entire pull request". Printing the wrong one is what makes a gate look
	unsatisfiable, and unsatisfiable gates get bypassed with --admin.
	"""
	cls_gate = _load_gate()
	str_problem = cls_gate.find_missing_review_problem([], _ROSTER, "h", str_head_oid=_HEAD)
	assert "@coderabbitai full review" in str_problem


def test_the_superseded_message_also_names_a_full_review() -> None:
	"""The remedy is printed by TWO messages, and a test on one proves nothing about the other.

	⚠️ Found by a negative control that PASSED: downgrading `full review` to `review` in the
	superseded-code branch changed nothing red, because the only test asserting the remedy
	exercised the zero-review branch. Both branches carry the same sentence and it can rot
	independently in either — which is the "shrink the mutation until only the target test can
	fail" rule read from the other end: a mutation that fails nothing has found a gap, not a
	clean bill of health.
	"""
	cls_gate = _load_gate()
	str_problem = cls_gate.find_missing_review_problem(
		[_review("coderabbitai", _SUPERSEDED)], _ROSTER, "h", str_head_oid=_HEAD
	)
	assert "@coderabbitai full review" in str_problem


def test_the_query_asks_for_the_prs_issue_comments() -> None:
	"""The notices are ISSUE comments, not review threads — verified on blueprintx#257.

	Reading only ``reviewThreads`` cannot see them, which is why the distinction between
	"nobody looked" and "already looked" was unavailable to the gate at all. The connection is
	paginated (``first`` + cursor) because ``last:100`` silently dropped the older half of a
	140-comment PR (#282, #319); the old assertion pinned that truncating shape.
	"""
	cls_gate = _load_gate()
	assert "comments(first:100, after:$cc)" in cls_gate._QUERY


def test_an_outdated_unresolved_thread_is_reported() -> None:
	"""GitHub drops it from the blocking set, so this gate is the only thing left asserting it.

	Measured on blueprintx#193: ``required_conversation_resolution: enabled``,
	``enforce_admins: True``, 29 of 29 checks green — and "Squash and merge" enabled over a
	thread reading ``resolved=False outdated=True``. Outdating is caused by the author's own
	commit rewriting the commented lines, so it is exactly the state an author can manufacture.
	"""
	cls_gate = _load_gate()
	dict_outdated = _thread(
		[("coderabbitai", "**Finding.** " + _LONG), ("guilhermegor", _LONG)],
		bool_resolved=False,
	)
	dict_outdated["isOutdated"] = True
	assert len(cls_gate.find_thread_problems([dict_outdated], _ROSTER)) == 1


def test_the_outdated_thread_message_says_the_merge_button_will_not_block() -> None:
	"""A reader who believes the native setting covers this will not act on the finding.

	The field was queried and never read in any predicate — the gate could see the state and
	said nothing about it, which is how the guarantee came to be described as stronger than it
	was.
	"""
	cls_gate = _load_gate()
	dict_outdated = _thread(
		[("coderabbitai", "**Finding.** " + _LONG), ("guilhermegor", _LONG)],
		bool_resolved=False,
	)
	dict_outdated["isOutdated"] = True
	assert "OUTDATED" in cls_gate.find_thread_problems([dict_outdated], _ROSTER)[0]


def test_a_current_unresolved_thread_does_not_claim_to_be_outdated() -> None:
	"""The should-PASS half of the message: the warning must discriminate, not always print."""
	cls_gate = _load_gate()
	list_current = [
		_thread(
			[("coderabbitai", "**Finding.** " + _LONG), ("guilhermegor", _LONG)],
			bool_resolved=False,
		)
	]
	assert "OUTDATED" not in cls_gate.find_thread_problems(list_current, _ROSTER)[0]


_CHAT_NOTICE = (
	"<!-- This is an auto-generated reply by CodeRabbit -->\n### Rate Limit Exceeded\n\n"
	"`@guilhermegor` have exceeded the limit for the number of chat messages per hour. Please "
	"wait **4 minutes and 37 seconds** before sending another message."
)
_REVIEW_NOTICE = (
	"<!-- This is an auto-generated reply by CodeRabbit -->\n<!-- CodeRabbit review command "
	"invocation: v2:d76d52b00d2dea173ffbdd1777877b36ea6f3150af9dfa2c0dd7a18cd167e6a1 -->\n"
	"<details>\n<summary>⚠️ Action not completed</summary>\n\nReview rate limited.\n\n---\n\n"
	"Your included review limit is currently reached under our [Fair Usage Limits "
	"Policy](https://docs.coderabbit.ai/management/plans#fair-usage-limits-policy). This "
	"review may still proceed through usage-based billing if eligible. Your next included "
	"review will be available in 21 minutes.\n\n</details>"
)


def test_classify_reviewer_notice_reads_the_real_chat_body_as_chat_limited() -> None:
	"""The should-fail witness this issue exists for: chat must not read as review."""
	cls_gate = _load_gate()
	assert cls_gate.classify_reviewer_notice(_CHAT_NOTICE) == cls_gate.NOTICE_CHAT_LIMITED


def test_classify_reviewer_notice_reads_the_real_review_body_as_review_limited() -> None:
	"""The should-fail witness in the other direction: review must not read as chat."""
	cls_gate = _load_gate()
	assert cls_gate.classify_reviewer_notice(_REVIEW_NOTICE) == cls_gate.NOTICE_REVIEW_LIMITED


def test_classify_reviewer_notice_an_unrecognised_rate_limit_mention_is_unknown_not_ok() -> None:
	"""UNKNOWN must never collapse into OK — an unrecognised notice is not an all-clear."""
	cls_gate = _load_gate()
	str_notice = "we are experiencing a general rate limit issue today"
	assert cls_gate.classify_reviewer_notice(str_notice) == cls_gate.NOTICE_UNKNOWN


def test_classify_reviewer_notice_a_clean_completion_is_ok() -> None:
	"""The should-PASS case: a notice with no rate-limit wording at all."""
	cls_gate = _load_gate()
	str_notice = "Review finished. No actionable comments were generated."
	assert cls_gate.classify_reviewer_notice(str_notice) == cls_gate.NOTICE_OK


_FILE_CAP_NOTICE = "Review skipped: 241 files exceed the limit of 100."


def test_classify_reviewer_notice_reads_the_real_file_cap_body_as_file_cap_exceeded() -> None:
	"""The should-fail witness this issue exists for: a stated file cap is its own state."""
	cls_gate = _load_gate()
	assert cls_gate.classify_reviewer_notice(_FILE_CAP_NOTICE) == cls_gate.NOTICE_FILE_CAP_EXCEEDED


def test_a_reworded_file_cap_notice_does_not_classify_as_file_cap() -> None:
	"""Defensive parsing: prose that only RESEMBLES the vendor's wording must not match.

	The notice is untrusted third-party text — over-matching a paraphrase is as much a defect
	as missing the real one, because it would let an unrelated notice borrow this state.
	"""
	cls_gate = _load_gate()
	str_notice = "This PR has too many files for a comfortable review, please consider splitting."
	assert cls_gate.classify_reviewer_notice(str_notice) == cls_gate.NOTICE_OK


def test_a_file_cap_near_match_with_a_trailing_suffix_does_not_classify_as_file_cap() -> None:
	"""The limit number needs its own sentence boundary, not just the words around it.

	An unterminated digit run matches its own prefix inside a longer token — "100x" reads as
	"100" followed by an unmatched "x", which used to satisfy the pattern anyway.
	"""
	cls_gate = _load_gate()
	str_notice = "Review skipped: 241 files exceed the limit of 100x, contact support."
	assert cls_gate.classify_reviewer_notice(str_notice) == cls_gate.NOTICE_OK


def test_a_file_cap_decline_is_still_a_failure() -> None:
	"""🔴 THE HARD CONSTRAINT: a structural decline must never read as a pass.

	Treating any reviewer refusal as a pass would reopen the #213 hole this gate exists to
	keep closed — a PR merging with nothing looked at, just spelled a different way.
	"""
	cls_gate = _load_gate()
	str_problem = cls_gate.find_missing_review_problem(
		[],
		_ROSTER,
		"h",
		str_head_oid=_HEAD,
		list_notices=[_notice("coderabbitai", _FILE_CAP_NOTICE)],
	)
	assert str_problem is not None


def test_a_file_cap_decline_message_tells_the_author_to_split_the_pr() -> None:
	"""The remedy differs from every other zero-review state: retrying cannot fix a file cap."""
	cls_gate = _load_gate()
	str_problem = cls_gate.find_missing_review_problem(
		[],
		_ROSTER,
		"h",
		str_head_oid=_HEAD,
		list_notices=[_notice("coderabbitai", _FILE_CAP_NOTICE)],
	)
	assert "Split this PR" in str_problem


def test_a_file_cap_decline_message_does_not_read_like_a_missing_reviewer() -> None:
	"""The discrimination this issue exists for: two different sentences, not one collapsed."""
	cls_gate = _load_gate()
	str_problem = cls_gate.find_missing_review_problem(
		[],
		_ROSTER,
		"h",
		str_head_oid=_HEAD,
		list_notices=[_notice("coderabbitai", _FILE_CAP_NOTICE)],
	)
	assert "never ran" not in str_problem


def test_a_reworded_notice_still_fails_rather_than_silently_passing() -> None:
	"""An unrecognised notice must fall back to the generic failure, never to a pass.

	This is the other half of the hard constraint: parsing defensively must not become an
	excuse to skip the check when the vendor's wording drifts.
	"""
	cls_gate = _load_gate()
	str_problem = cls_gate.find_missing_review_problem(
		[],
		_ROSTER,
		"h",
		str_head_oid=_HEAD,
		list_notices=[_notice("coderabbitai", "too many files, sorry")],
	)
	assert str_problem is not None


def test_print_missing_review_json_carries_the_file_cap_classification(
	capsys: pytest.CaptureFixture[str],
) -> None:
	"""The third state must be visible in machine-readable output too, not only in prose."""
	cls_gate = _load_gate()
	list_notices = [{"author": {"login": "coderabbitai[bot]"}, "body": _FILE_CAP_NOTICE}]
	set_roster = {cls_gate.normalise_login(str_login) for str_login in _ROSTER}
	cls_gate._print_missing_review(
		True, "no declared reviewer ever reported", list_notices, set_roster
	)
	dict_out = json.loads(capsys.readouterr().out)
	assert dict_out["notice_classification"] == cls_gate.NOTICE_FILE_CAP_EXCEEDED


_BOT_DETECTED_NOTICE = "Review skipped — Bot user detected."


def test_a_bot_detected_notice_does_not_classify_as_file_cap() -> None:
	"""The shared 'Review skipped' prefix must not make two unrelated reasons collide."""
	cls_gate = _load_gate()
	assert cls_gate.classify_reviewer_notice(_BOT_DETECTED_NOTICE) == cls_gate.NOTICE_OK


def test_a_bot_detected_decline_gets_the_generic_remedy_not_split_advice() -> None:
	"""Splitting a one-file PR is nonsense advice — this reason clears by asking, not splitting."""
	cls_gate = _load_gate()
	str_problem = cls_gate.find_missing_review_problem(
		[],
		_ROSTER,
		"h",
		str_head_oid=_HEAD,
		list_notices=[_notice("coderabbitai", _BOT_DETECTED_NOTICE)],
	)
	assert "Split this PR" not in str_problem


def test_a_bot_detected_decline_still_fails_the_gate() -> None:
	"""Same hard constraint as the file cap: a stated reason is still not a pass."""
	cls_gate = _load_gate()
	assert (
		cls_gate.find_missing_review_problem(
			[],
			_ROSTER,
			"h",
			str_head_oid=_HEAD,
			list_notices=[_notice("coderabbitai", _BOT_DETECTED_NOTICE)],
		)
		is not None
	)


def test_parse_declared_wait_reads_277_seconds_from_the_real_chat_body() -> None:
	"""Pinned exactly on the number blueprintx#364 measured the loop stalling on: 4m37s."""
	cls_gate = _load_gate()
	assert cls_gate.parse_declared_wait(_CHAT_NOTICE) == 277


def test_parse_declared_wait_reads_minutes_from_the_real_review_body() -> None:
	"""The review quota declares whole minutes; 21 minutes is 1260 seconds."""
	cls_gate = _load_gate()
	assert cls_gate.parse_declared_wait(_REVIEW_NOTICE) == 1260


def test_parse_declared_wait_returns_none_when_no_wait_is_declared() -> None:
	"""A notice that names no number must not invent one."""
	cls_gate = _load_gate()
	assert cls_gate.parse_declared_wait("Review rate limited.") is None


def test_parse_args_default_is_prose() -> None:
	"""Without ``--json`` the gate keeps its historical prose-only behaviour."""
	cls_gate = _load_gate()
	assert cls_gate.parse_args([]).json is False


def test_parse_args_json_flag_is_read() -> None:
	"""``--json`` is the one new flag this issue adds."""
	cls_gate = _load_gate()
	assert cls_gate.parse_args(["--json"]).json is True


def test_print_skip_prose_mode_prints_the_reason(capsys: pytest.CaptureFixture[str]) -> None:
	"""Default mode: the self-skip line is unchanged prose."""
	cls_gate = _load_gate()
	cls_gate._print_skip(
		False, "No .review-bots.yaml — the review-thread gate is not adopted here"
	)
	assert "not adopted here" in capsys.readouterr().out


def test_print_skip_json_mode_emits_a_status_field(capsys: pytest.CaptureFixture[str]) -> None:
	"""``--json`` mode: the same self-skip is machine-readable, never grepped prose."""
	cls_gate = _load_gate()
	cls_gate._print_skip(True, "nothing to check")
	assert json.loads(capsys.readouterr().out)["status"] == "skipped"


def test_print_missing_review_json_carries_the_notice_classification(
	capsys: pytest.CaptureFixture[str],
) -> None:
	"""The exact gap #364 names: a caller must not have to grep the quoted notice itself."""
	cls_gate = _load_gate()
	list_notices = [{"author": {"login": "coderabbitai[bot]"}, "body": _CHAT_NOTICE}]
	set_roster = {cls_gate.normalise_login(str_login) for str_login in _ROSTER}
	cls_gate._print_missing_review(
		True, "no declared reviewer ever reported", list_notices, set_roster
	)
	dict_out = json.loads(capsys.readouterr().out)
	assert dict_out["notice_classification"] == cls_gate.NOTICE_CHAT_LIMITED


def test_print_thread_verdict_json_pass_has_no_problems(
	capsys: pytest.CaptureFixture[str],
) -> None:
	"""An empty problem list must report ``pass``, matching the prose "All N answered" case."""
	cls_gate = _load_gate()
	cls_gate._print_thread_verdict(True, [], 3, True)
	assert json.loads(capsys.readouterr().out)["status"] == "pass"


def test_print_thread_verdict_json_fail_reports_fail_status(
	capsys: pytest.CaptureFixture[str],
) -> None:
	"""A non-empty problem list must report ``fail``.

	This is the concrete case #364 names: a caller that must grep prose for "thread" matched
	the phrase "so zero threads would be fine" inside an unrelated message and misreported 27
	PRs. JSON mode gives it a status field instead.
	"""
	cls_gate = _load_gate()
	cls_gate._print_thread_verdict(True, ["src/thing.py: thread is open"], 1, True)
	assert json.loads(capsys.readouterr().out)["status"] == "fail"


def test_print_thread_verdict_json_fail_carries_the_problems(
	capsys: pytest.CaptureFixture[str],
) -> None:
	"""A failing verdict must carry the problems themselves, not only the status.

	Separate from the status assertion above: a verdict that says ``fail`` and drops the
	problem list tells a caller something is wrong without saying what, and the two
	outcomes fail independently.
	"""
	cls_gate = _load_gate()
	cls_gate._print_thread_verdict(True, ["src/thing.py: thread is open"], 1, True)
	assert json.loads(capsys.readouterr().out)["problems"] == ["src/thing.py: thread is open"]


_BODY_ROSTER = {"coderabbitai"}
_BOTH_ROSTER = {"coderabbitai", "guilhermegor-review-ladder", "copilot-pull-request-reviewer"}
_BODY_MAJOR = "**Major** — the retry loop swallows the final error."
_BODY_SUBMITTED = "2026-01-02T00:00:00Z"
_BODY_AFTER = "2026-01-03T00:00:00Z"
_BODY_REPLY = "Fixed in the next commit: the loop now re-raises the last error. " + "x" * 60


def _body_review(str_body: str | None, str_login: str = "coderabbitai[bot]") -> dict:
	"""Build a submitted review on the head carrying a body, as the ladder posts them."""
	return {
		"author": {"login": str_login},
		"commit": {"oid": _HEAD},
		"body": str_body,
		"submittedAt": _BODY_SUBMITTED,
	}


_LADDER_LOGIN = "guilhermegor-review-ladder[bot]"


def _ladder_problems(str_body: str, str_login: str = _LADDER_LOGIN) -> list[str]:
	"""Problems for one review authored by ``str_login`` under a CodeRabbit + ladder roster."""
	list_reviews = [_body_review(str_body, str_login)]
	return _load_gate().find_review_body_problems(list_reviews, [], _BOTH_ROSTER)


def _body_problems(list_reviews: list[dict], list_notices: list[dict]) -> list[str]:
	return _load_gate().find_review_body_problems(list_reviews, list_notices, _BODY_ROSTER)


def test_review_body_with_findings_and_no_reply_is_a_problem() -> None:
	"""A severity marker in a review body with nobody answering it must fail (#630)."""
	assert len(_body_problems([_body_review(_BODY_MAJOR)], [])) == 1


def test_review_body_with_findings_answered_after_it_passes() -> None:
	"""A substantive non-roster reply posted after the review answers it."""
	list_notices = [_notice("someone", _BODY_REPLY, _BODY_AFTER)]
	assert _body_problems([_body_review(_BODY_MAJOR)], list_notices) == []


def test_review_body_reply_shorter_than_the_bar_is_a_problem() -> None:
	"""The thread bar applies: 99 characters is not an answer."""
	list_notices = [_notice("someone", "x" * 99, _BODY_AFTER)]
	assert len(_body_problems([_body_review(_BODY_MAJOR)], list_notices)) == 1


def test_review_body_reply_posted_before_the_review_is_a_problem() -> None:
	"""A reply that predates the review cannot be an answer to it."""
	list_notices = [_notice("someone", _BODY_REPLY, "2026-01-01T12:00:00Z")]
	assert len(_body_problems([_body_review(_BODY_MAJOR)], list_notices)) == 1


def test_review_body_reply_from_the_roster_is_a_problem() -> None:
	"""A reviewer replying to itself is not an answer, same as in a thread."""
	list_notices = [_notice("coderabbitai[bot]", _BODY_REPLY, _BODY_AFTER)]
	assert len(_body_problems([_body_review(_BODY_MAJOR)], list_notices)) == 1


def test_review_body_findings_on_a_superseded_commit_still_need_a_reply() -> None:
	"""A push must not clear body findings the way it never clears an inline thread."""
	dict_stale = {**_body_review(_BODY_MAJOR), "commit": {"oid": _SUPERSEDED}}
	assert len(_body_problems([dict_stale], [])) == 1


def test_review_body_one_reply_after_both_reviews_answers_both() -> None:
	"""Deliberate: one reply posted after the latest findings body covers the earlier ones."""
	dict_late = {**_body_review(_BODY_MAJOR), "submittedAt": "2026-01-02T12:00:00Z"}
	list_notices = [_notice("someone", _BODY_REPLY, _BODY_AFTER)]
	assert _body_problems([_body_review(_BODY_MAJOR), dict_late], list_notices) == []


def test_review_body_reply_from_a_graphql_bot_is_a_problem() -> None:
	"""GraphQL drops the [bot] suffix; ``__typename`` Bot is what marks GitGuardian et al."""
	dict_bot = {
		"author": {"login": "gitguardian", "__typename": "Bot"},
		"body": _BODY_REPLY,
		"createdAt": _BODY_AFTER,
	}
	assert len(_body_problems([_body_review(_BODY_MAJOR)], [dict_bot])) == 1


def test_review_body_reply_from_a_null_author_is_a_problem() -> None:
	"""A deleted (ghost) account is not a known human; it fails closed."""
	dict_ghost = {"author": None, "body": _BODY_REPLY, "createdAt": _BODY_AFTER}
	assert len(_body_problems([_body_review(_BODY_MAJOR)], [dict_ghost])) == 1


def test_review_body_reply_from_a_rest_bot_login_is_a_problem() -> None:
	"""A ``[bot]`` login that is not on the roster is still not an answer."""
	list_notices = [_notice("github-actions[bot]", _BODY_REPLY, _BODY_AFTER)]
	assert len(_body_problems([_body_review(_BODY_MAJOR)], list_notices)) == 1


def test_review_body_dismissed_review_needs_no_reply() -> None:
	"""A dismissal is the maintainer's explicit answer."""
	dict_dismissed = {**_body_review(_BODY_MAJOR), "state": "DISMISSED"}
	assert _body_problems([dict_dismissed], []) == []


def test_review_body_problem_quotes_the_matched_line_not_the_first() -> None:
	"""CodeRabbit bodies open with boilerplate; the failure must show the finding."""
	str_body = "<!-- auto-generated -->\n**Review profile**: CHILL\n" + _BODY_MAJOR
	assert "retry loop" in _body_problems([_body_review(str_body)], [])[0]


def test_print_review_body_problems_json_carries_the_thread_problems(
	capsys: pytest.CaptureFixture[str],
) -> None:
	"""Both failures reach the caller in one run, not one per round trip."""
	_load_gate()._print_review_body_problems(True, ["body"], ["an open thread"])
	assert json.loads(capsys.readouterr().out)["thread_problems"] == ["an open thread"]


def test_review_body_findings_from_a_non_roster_author_are_ignored() -> None:
	"""Only a roster reviewer's body is held to the bar."""
	assert _body_problems([_body_review(_BODY_MAJOR, "someone")], []) == []


@pytest.mark.parametrize(
	"str_body",
	[
		"**Major** — x",
		"🟠 Major: x",
		"[Critical] x",
		"Severity: major",
		"- **Minor**: x",
		"2 finding(s) across 3 reviewed file(s).",
		"## Findings\n\n- the loop swallows the error",
		"## Findings\n- `parse()` has no known bugs on ASCII but crashes on empty input",
		"No findings in a.py.\n**Major** — b.py swallows the error.",
		"- **Major:** no input validation in parse(), RCE via crafted path",
		"**Critical** — None of the callers check the return code, data loss",
	],
)
def test_review_body_carrying_findings_is_flagged(str_body: str) -> None:
	"""Each shape a reviewer writes findings in must demand an answer."""
	assert len(_body_problems([_body_review(str_body)], [])) == 1


@pytest.mark.parametrize(
	"str_body",
	[
		"",
		"LGTM.",
		"No findings.",
		"No blocking bugs found.",
		"No major issues.",
		"0 finding(s) across 3 reviewed file(s).",
		"## Findings\n\nNo findings.",
		"No **Major** issues.",
		"- **Critical:** none",
		"Minor: none found",
		"Major: none",
		"Severity: none",
		"Severity: n/a",
		"## Issues\n\nNone.",
		"## Issues\nNone found.",
		"This is a *minor* cleanup, LGTM.",
		"Approved (minor nits only, all optional).",
		"Addressed 2 findings from the prior round; nothing new.",
		"_🧹 Nitpick_ | _🔵 Trivial_",
		"- **Nitpick:** rename x",
	],
)
def test_review_body_reporting_no_findings_stays_green(str_body: str) -> None:
	"""A clean review is not a finding: it needs no reply."""
	assert _body_problems([_body_review(str_body)], []) == []


def test_review_body_that_is_null_stays_green() -> None:
	"""GitHub returns a null-ish body for an approval with no text."""
	assert _body_problems([_body_review(None)], []) == []


@pytest.mark.parametrize("str_field", ["body", "submittedAt", "state", "__typename"])
def test_review_query_asks_for_each_field_the_body_check_reads(str_field: str) -> None:
	"""Without these fields the check would read an empty review or a bot as a person."""
	assert str_field in _load_gate()._QUERY


def test_print_review_body_problems_json_carries_the_reason(
	capsys: pytest.CaptureFixture[str],
) -> None:
	"""The JSON verdict names the failure so a caller never greps prose."""
	_load_gate()._print_review_body_problems(True, ["a review body is unanswered"])
	assert json.loads(capsys.readouterr().out)["reason"] == "unanswered_review_body"


_LADDER = (
	"Fallback review — runtime: {}, model: default (selected by: {})\nReviewed head: 1a2b3c4\n\n"
)
_LADDER_CLAUDE = _LADDER.format("claude", "last-resort")
_LADDER_CLI = _LADDER.format("coderabbit", "live-probe")
_PROSE = "I couldn't check any of this against the tree. Every tool call failed."
_LOOP = "the retry loop swallows the final error."

_CR_SECTION = "⚠️ Outside diff range comments (1)"
_CR_OUTSIDE_DIFF = (
	"> [!CAUTION]\n> Some comments are outside the diff and can't be posted inline.\n>\n"
	f"> <details>\n> <summary>{_CR_SECTION}</summary><blockquote>\n>\n"
	"> `191-191`: _🎯 Functional Correctness_ | _🟠 Major_ | _⚡ Quick win_\n>\n"
	"> **Resolve the PR head SHA for `issue_comment` runs.**\n>\n"
	"> </blockquote></details>\n\n"
	"<details>\n<summary>ℹ️ Review info</summary>\n\n**Review profile**: CHILL\n"
)
_CR_NITPICK_ONLY = _CR_OUTSIDE_DIFF.replace(_CR_SECTION, "🧹 Nitpick comments (1)")
_CR_INLINE_ONLY = (
	"**Actionable comments posted: 2**\n\n---\n\nInline comments:\n"
	"Review comments at @docs/faq.md:\n- Line 50: reword.\n\n"
	"<details>\n<summary>ℹ️ Review info</summary>\n\n**Review profile**: CHILL\n"
)

_DICT_REVIEW_SHAPES = {
	"coderabbit-outside-diff-section": (
		_CR_OUTSIDE_DIFF,
		_CR_NITPICK_ONLY.replace("🟠 Major", "🧹 Nitpick"),
	),
	"coderabbit-zero-count-with-outside-diff": (
		"**Actionable comments posted: 0**\n\n" + _CR_OUTSIDE_DIFF,
		"**Actionable comments posted: 0**\n\n" + _CR_NITPICK_ONLY,
	),
	"coderabbit-n-count-with-duplicate-section": (
		"**Actionable comments posted: 2**\n\n♻️ Duplicate comments (1)\n\nx",
		"**Actionable comments posted: 2**\n\n🧹 Nitpick comments (1)\n\nx",
	),
	"ladder-claude-rung-prose-without-a-count": (_LADDER_CLAUDE + _PROSE, _PROSE),
	"ladder-coderabbit-cli-count": (
		_LADDER_CLI + "3 finding(s) across 4 reviewed file(s).",
		_LADDER_CLI + "No findings.",
	),
	"heading-review": (f"## Review\n\n{_LOOP}", _LOOP),
	"bullet-review-dash": (f"* Review - {_LOOP}", f"* {_LOOP}"),
	"review-colon": (f"Review: {_LOOP}", _LOOP),
	"bold-findings": (f"**Findings**\n\n- {_LOOP}", f"- {_LOOP}"),
	"numbered-finding": (f"Finding 1: {_LOOP}", _LOOP),
	"heading-findings": (f"## Findings\n\n- {_LOOP}", f"- {_LOOP}"),
	"severity-bullet": (f"- **Major** `a.py`: {_LOOP}", f"- `a.py`: {_LOOP}"),
}


@pytest.mark.parametrize(
	"str_body", [t[0] for t in _DICT_REVIEW_SHAPES.values()], ids=list(_DICT_REVIEW_SHAPES)
)
def test_review_shape_declared_by_structure_demands_an_answer(str_body: str) -> None:
	"""Every recognised review shape must fail when nobody answered."""
	assert len(_body_problems([_body_review(str_body)], [])) == 1


@pytest.mark.parametrize(
	"str_witness", [t[1] for t in _DICT_REVIEW_SHAPES.values()], ids=list(_DICT_REVIEW_SHAPES)
)
def test_review_shape_witness_without_its_marker_is_not_a_review(str_witness: str) -> None:
	"""Should-fail witness: the same text minus the structural marker must stay green."""
	assert _body_problems([_body_review(str_witness)], []) == []


@pytest.mark.parametrize(
	"str_body",
	[
		"**Actionable comments posted: 0**\n\n## Review details\n\nNitpicks only.",
		"Actionable comments posted: 0",
		_LADDER_CLI + "0 finding(s) across 4 reviewed file(s).",
		_LADDER_CLAUDE + "No findings.",
		_LADDER_CLAUDE + "## Review\n\nNo findings.",
		"Review: no findings",
	],
)
def test_review_stating_zero_findings_never_blocks(str_body: str) -> None:
	"""A printed count of 0 (or an explicit clean line) means no findings."""
	assert _ladder_problems(str_body) == []


@pytest.mark.parametrize(
	"str_body",
	[
		_LADDER_CLI + "0 finding(s) across 4 reviewed file(s).\n- **Major** x",
	],
)
def test_review_count_of_zero_beats_prose_markers(str_body: str) -> None:
	"""Structured counts beat prose: a stated 0 is authoritative when no section contradicts."""
	assert _ladder_problems(str_body) == []


def test_coderabbit_header_of_zero_beats_prose_markers() -> None:
	"""The same rule for CodeRabbit's own header, authored by CodeRabbit."""
	str_body = "**Actionable comments posted: 0**\n\n🔴 Major stray marker"
	assert _ladder_problems(str_body, "coderabbitai[bot]") == []


def test_quoted_ladder_count_inside_a_sentence_does_not_declare_zero() -> None:
	"""The count must open a line: a quoted '0 finding(s) across' cannot clean a real finding."""
	str_body = f"- **Major** x: {_LOOP} (earlier run said 0 finding(s) across 4 files)"
	assert len(_body_problems([_body_review(str_body)], [])) == 1


def test_quoted_actionable_header_mid_line_does_not_clear_a_real_finding() -> None:
	"""Should-fail witness: a claude-rung body quoting the header mid-line still needs a reply."""
	str_body = (
		_LADDER_CLAUDE + "- **Major** x: the gate trusts 'Actionable comments posted: 0' anywhere."
	)
	assert len(_body_problems([_body_review(str_body)], [])) == 1


_FINDING = "- **Major** x: the gate trusts a quoted header."


@pytest.mark.parametrize(
	"str_quote",
	[
		"> **Actionable comments posted: 0**",
		">> Actionable comments posted: 0",
		"```\n**Actionable comments posted: 0**\n```",
		"~~~\nActionable comments posted: 0\n~~~",
	],
)
def test_quoted_or_fenced_header_cannot_clear_a_ladder_finding(str_quote: str) -> None:
	"""Should-fail witness: a quoted CodeRabbit '0' header in a ladder body clears nothing."""
	str_body = f"{_LADDER_CLAUDE}{_FINDING}\n\n{str_quote}\n"
	assert len(_body_problems([_body_review(str_body)], [])) == 1


@pytest.mark.parametrize(
	("str_head", "str_login"),
	[
		(_LADDER_CLAUDE, _LADDER_LOGIN),
		("", _LADDER_LOGIN),
		("", "copilot-pull-request-reviewer[bot]"),
		(_LADDER_CLAUDE, "copilot-pull-request-reviewer[bot]"),
	],
	ids=["ladder-attributed", "ladder-attribution-missing", "other-roster", "other-roster-ladder"],
)
def test_unquoted_header_from_a_non_coderabbit_author_cannot_clear_a_finding(
	str_head: str, str_login: str
) -> None:
	"""Count authority binds to the author: only CodeRabbit's header speaks."""
	str_body = f"{str_head}{_FINDING}\n\n**Actionable comments posted: 0**\n"
	assert len(_ladder_problems(str_body, str_login)) == 1


def test_unquoted_header_from_coderabbit_still_clears_inline_findings() -> None:
	"""Should-fail witness: the same body authored by CodeRabbit stays green."""
	str_body = f"{_FINDING}\n\n**Actionable comments posted: 0**\n"
	assert _ladder_problems(str_body, "coderabbitai[bot]") == []


@pytest.mark.parametrize("str_login", ["coderabbitai[bot]", "copilot-pull-request-reviewer[bot]"])
def test_ladder_count_from_a_non_ladder_author_cannot_clear_a_finding(str_login: str) -> None:
	"""The ladder count speaks only for the ladder app, with the attribution line."""
	str_body = f"{_LADDER_CLI}0 finding(s) across 4 reviewed file(s).\n{_FINDING}"
	assert len(_ladder_problems(str_body, str_login)) == 1


def test_ladder_count_without_attribution_cannot_clear_a_finding() -> None:
	"""Even the ladder app's count needs the attribution line."""
	str_body = f"0 finding(s) across 4 reviewed file(s).\n{_FINDING}"
	assert len(_ladder_problems(str_body)) == 1


@pytest.mark.parametrize(
	"str_quote",
	[
		"> 0 finding(s) across 4 reviewed file(s).",
		"```\n0 finding(s) across 4 reviewed file(s).\n```",
	],
)
def test_quoted_ladder_count_cannot_clear_a_finding(str_quote: str) -> None:
	"""A quoted ladder '0 finding(s)' count clears nothing."""
	str_body = f"{_LADDER_CLAUDE}{_FINDING}\n\n{str_quote}\n"
	assert len(_body_problems([_body_review(str_body)], [])) == 1


def test_ladder_count_without_the_ladder_attribution_is_not_authoritative() -> None:
	"""The count speaks only in a body that carries the attribution line."""
	str_body = f"0 finding(s) across 4 reviewed file(s).\n{_FINDING}"
	assert len(_body_problems([_body_review(str_body)], [])) == 1


def test_actionable_header_at_a_line_start_still_clears_inline_findings() -> None:
	"""The real CodeRabbit shape, the bold header opening a line, still wins."""
	str_body = "**Actionable comments posted: 0**\n\n- **Major** x"
	assert _body_problems([_body_review(str_body)], []) == []


def test_coderabbit_inline_findings_need_no_body_reply() -> None:
	"""Its N inline comments are threads `find_thread_problems` already gates (no double-gate).

	An open PR whose inline threads are all answered and resolved must stay green, so the body
	check cannot demand a PR comment for the same findings.
	"""
	assert _body_problems([_body_review(_CR_INLINE_ONLY)], []) == []


def test_coderabbit_review_boilerplate_is_never_the_quoted_finding() -> None:
	"""The message quotes the section, not '**Review profile**: CHILL'."""
	assert "Outside diff range" in _body_problems([_body_review(_CR_OUTSIDE_DIFF)], [])[0]


def test_ladder_review_posted_as_an_issue_comment_counts_as_a_review() -> None:
	"""Some rungs post their review as an issue comment, not a PR review."""
	list_notices = [_notice("guilhermegor-review-ladder[bot]", _LADDER_CLAUDE + _PROSE)]
	assert len(_load_gate().find_review_body_problems([], list_notices, _BOTH_ROSTER)) == 1


def test_ladder_issue_comment_without_its_attribution_is_not_a_review() -> None:
	"""Should-fail witness for the issue-comment path."""
	list_notices = [_notice("guilhermegor-review-ladder[bot]", _PROSE)]
	assert _load_gate().find_review_body_problems([], list_notices, _BOTH_ROSTER) == []


@pytest.mark.parametrize(
	"str_status",
	[
		"Review ladder: all rungs failed, no review was produced.",
		"Review ladder: no rung available for this PR.",
		"Review skipped: draft PR.",
	],
)
def test_ladder_status_notice_is_not_a_review(str_status: str) -> None:
	"""A failure or status notice from the ladder must not demand an answer."""
	list_notices = [_notice("guilhermegor-review-ladder[bot]", str_status)]
	assert _load_gate().find_review_body_problems([], list_notices, _BOTH_ROSTER) == []


_WALKTHROUGH = "> [!IMPORTANT]\n> ## Review skipped\n> - **Review profile**: CHILL"


def test_coderabbit_walkthrough_comment_is_not_a_review() -> None:
	"""A walkthrough is skipped by SHAPE: it has no ladder head, header or body section."""
	str_body = (
		"<!-- This is an auto-generated comment: summarize by coderabbit.ai -->\n" + _WALKTHROUGH
	)
	assert _body_problems([], [_notice("coderabbitai[bot]", str_body)]) == []


def _pr_page(list_reviews: list[dict], bool_next: bool) -> dict:
	"""Build one GraphQL page whose reviews connection may have a next page."""
	return {
		"reviews": {
			"pageInfo": {"hasNextPage": bool_next, "endCursor": "c"},
			"nodes": list_reviews,
		},
		"reviewThreads": {"pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": []},
	}


def test_review_on_the_second_page_reaches_the_body_check(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Pagination extends ``dict_pr`` in place, so a body past the first 100 reviews is seen."""
	cls_gate = _load_gate()
	list_pages = [
		_pr_page([_body_review("LGTM")], True),
		_pr_page([_body_review(_BODY_MAJOR)], False),
	]
	monkeypatch.setattr(cls_gate, "_fetch_page", lambda *list_args: list_pages.pop(0))
	dict_pr = cls_gate.fetch_pull_request("o", "r", 1)
	assert len(cls_gate._unanswered_bodies(dict_pr, [], _BODY_ROSTER)) == 1


_ANSWER_SHAPES = {
	"reply-to-review-id": ("Reply to review 5474743692: done.", "done."),
	"answer-to-review": ("Answer to review: done.", "done."),
	"answers-to-ladder": ("Answers to ladder review, all held.", "all held."),
	"re-colon-review": ("Re: review — done.", "done."),
	"addressed-in-sha": ("Addressed in 2cdb28bf", "Addressed"),
	"fixed-in-sha": ("Fixed in `7273818f`.", "Fixed."),
	"per-finding": ("**Finding 1: verified, fixed.**", "**verified, fixed.**"),
	"quoted": ("> the loop swallows\nFixed it.", "the loop swallows\nFixed it."),
	"verdicts-on-review": ("Verdicts on the ladder review: held.", "held."),
	"judgment-on-review": ("Judgment on the fallback review: ok.", "ok."),
	"review-id-verified": ("Review 5469399568 verified.", "Verified."),
}
_REVIEWED = [_body_review(_BODY_MAJOR)]


@pytest.mark.parametrize(
	"str_reply", [t[0] for t in _ANSWER_SHAPES.values()], ids=list(_ANSWER_SHAPES)
)
def test_answer_shape_declared_by_structure_answers_at_any_length(str_reply: str) -> None:
	"""A recognised answer shape counts even below the length bar."""
	assert _body_problems(_REVIEWED, [_notice("someone", str_reply, _BODY_AFTER)]) == []


@pytest.mark.parametrize(
	"str_witness", [t[1] for t in _ANSWER_SHAPES.values()], ids=list(_ANSWER_SHAPES)
)
def test_answer_shape_witness_without_its_marker_is_not_an_answer(str_witness: str) -> None:
	"""Should-fail witness: the same short text minus the marker is not an answer."""
	assert len(_body_problems(_REVIEWED, [_notice("someone", str_witness, _BODY_AFTER)])) == 1


@pytest.mark.parametrize(
	"str_command",
	[
		"@coderabbitai review",
		"@coderabbitai full review",
		"@coderabbitai re-review",
		"Ready for re-review",
		"We're waiting on the review",
		"Not answered yet, findings pending",
	],
)
def test_a_review_request_or_status_line_is_not_an_answer(str_command: str) -> None:
	"""Asking for another review, or saying nothing is answered, answers nothing."""
	assert len(_body_problems(_REVIEWED, [_notice("someone", str_command, _BODY_AFTER)])) == 1


def test_answer_shape_from_a_bot_is_not_an_answer() -> None:
	"""The shape alone never lets a bot clear findings."""
	list_notices = [_notice("github-actions[bot]", "Reply to review 123456: ok.", _BODY_AFTER)]
	assert len(_body_problems(_REVIEWED, list_notices)) == 1


def test_answer_shape_posted_before_the_review_is_not_an_answer() -> None:
	"""The shape must still be newer than the review it answers."""
	list_notices = [_notice("someone", "Reply to review 123456: ok.", "2026-01-01T00:00:00Z")]
	assert len(_body_problems(_REVIEWED, list_notices)) == 1


def test_answer_shape_from_the_roster_is_not_an_answer() -> None:
	"""A reviewer answering itself is not an answer, shape or not."""
	list_notices = [_notice("coderabbitai[bot]", "Reply to review 123456: ok.", _BODY_AFTER)]
	assert len(_body_problems(_REVIEWED, list_notices)) == 1


def test_body_section_without_a_parsable_count_is_a_finding() -> None:
	"""A section heading whose count is missing or unparsable is a finding, never a clean 0."""
	str_body = "**Actionable comments posted: 0**\n\n⚠️ Outside diff range comments\n\nx"
	assert len(_body_problems([_body_review(str_body)], [])) == 1


def test_body_section_with_a_stated_zero_count_is_clean() -> None:
	"""Should-fail witness: the same body with an explicit (0) stays green."""
	str_body = "**Actionable comments posted: 0**\n\n⚠️ Outside diff range comments (0)\n\nx"
	assert _body_problems([_body_review(str_body)], []) == []


def test_ladder_review_with_an_attribution_and_nothing_else_is_a_finding() -> None:
	"""A truncated or failed ladder review says nothing, so it cannot read as clean."""
	assert len(_body_problems([_body_review(_LADDER_CLAUDE)], [])) == 1


def test_ladder_review_that_says_no_findings_is_clean() -> None:
	"""Should-fail witness: the explicit clean statement is the positive evidence."""
	assert _body_problems([_body_review(_LADDER_CLAUDE + "No findings.")], []) == []


@pytest.mark.parametrize("str_typename", ["Bot", "Mannequin", "Organization"])
def test_answer_from_a_non_user_account_type_is_not_an_answer(str_typename: str) -> None:
	"""Only a ``User`` (or an untyped REST login) answers; any other type fails closed."""
	dict_author = {"login": "someone", "__typename": str_typename}
	dict_reply = {"author": dict_author, "body": _BODY_REPLY, "createdAt": _BODY_AFTER}
	assert len(_body_problems(_REVIEWED, [dict_reply])) == 1


def test_answer_from_a_user_account_type_is_an_answer() -> None:
	"""Should-fail witness: the same reply from a ``User`` answers."""
	dict_author = {"login": "someone", "__typename": "User"}
	dict_reply = {"author": dict_author, "body": _BODY_REPLY, "createdAt": _BODY_AFTER}
	assert _body_problems(_REVIEWED, [dict_reply]) == []


def test_roster_comment_with_an_auto_marker_and_an_attribution_still_counts() -> None:
	"""A marker must not be a skip list: structure decides, so a marked ladder review counts."""
	str_body = "<!-- This is an auto-generated comment: x -->\n" + _LADDER_CLAUDE + _PROSE
	list_notices = [_notice("guilhermegor-review-ladder[bot]", str_body)]
	assert len(_load_gate().find_review_body_problems([], list_notices, _BOTH_ROSTER)) == 1


def test_roster_issue_comment_with_a_body_section_counts_as_a_review() -> None:
	"""An issue comment carrying a non-zero outside-diff section is a review too."""
	list_notices = [_notice("coderabbitai[bot]", _CR_OUTSIDE_DIFF)]
	assert len(_body_problems([], list_notices)) == 1


def test_roster_issue_comment_without_the_body_section_is_not_a_review() -> None:
	"""Should-fail witness: the same comment minus its section marker."""
	list_notices = [_notice("coderabbitai[bot]", _CR_NITPICK_ONLY.replace("🟠 Major", "x"))]
	assert _body_problems([], list_notices) == []


def test_ladder_issue_review_without_a_timestamp_fails_closed() -> None:
	"""No ``createdAt`` means no ordering evidence, so no answer can postdate it."""
	dict_review = {**_notice("guilhermegor-review-ladder[bot]", _LADDER_CLAUDE + _PROSE)}
	dict_review["createdAt"] = None
	list_notices = [dict_review, _notice("someone", _BODY_REPLY, _BODY_AFTER)]
	assert len(_load_gate().find_review_body_problems([], list_notices, _BOTH_ROSTER)) == 1


def _comments_node(list_notices: list[dict], str_cursor: str | None) -> dict:
	"""Build one page of issue comments; ``str_cursor`` set means another page follows."""
	return {
		"reviews": {"pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": []},
		"reviewThreads": {"pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": []},
		"comments": {
			"pageInfo": {"hasNextPage": bool(str_cursor), "endCursor": str_cursor},
			"nodes": list_notices,
		},
	}


def _fetch_comment_pages(monkeypatch: pytest.MonkeyPatch, list_pages: list[dict]) -> dict:
	"""Run ``fetch_pull_request`` over mocked pages and return the merged node."""
	cls_gate = _load_gate()
	monkeypatch.setattr(cls_gate, "_fetch_page", Mock(side_effect=list_pages))
	return cls_gate.fetch_pull_request("o", "r", 1)


def test_review_on_comment_page_one_answered_on_page_three_counts(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""A PR past 200 comments: the answer on the last page must reach the body check."""
	str_review = "**Actionable comments posted: 1**\n\n♻️ Duplicate comments (1)\n\nx"
	list_pages = [
		_comments_node([_notice("coderabbitai[bot]", str_review, "2026-01-02T00:00:00Z")], "c1"),
		_comments_node([_notice("someone", "unrelated chatter", "2026-01-02T06:00:00Z")], "c2"),
		_comments_node([_notice("someone", _BODY_REPLY, _BODY_AFTER)], None),
	]
	dict_pr = _fetch_comment_pages(monkeypatch, list_pages)
	list_notices = dict_pr["comments"]["nodes"]
	assert _load_gate().find_review_body_problems([], list_notices, _BODY_ROSTER) == []


def test_comment_review_without_the_page_three_answer_is_a_problem(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Should-fail witness: the same review without the last-page answer still fails."""
	str_review = "**Actionable comments posted: 1**\n\n♻️ Duplicate comments (1)\n\nx"
	list_pages = [
		_comments_node([_notice("coderabbitai[bot]", str_review, "2026-01-02T00:00:00Z")], "c1"),
		_comments_node([_notice("someone", "unrelated chatter", "2026-01-02T06:00:00Z")], "c2"),
		_comments_node([_notice("someone", "still chatting", _BODY_AFTER)], None),
	]
	dict_pr = _fetch_comment_pages(monkeypatch, list_pages)
	list_notices = dict_pr["comments"]["nodes"]
	assert len(_load_gate().find_review_body_problems([], list_notices, _BODY_ROSTER)) == 1


def test_comment_pages_are_requested_with_the_comment_cursor(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Page two and three are asked for with the previous page's cursor (sixth argument)."""
	cls_gate = _load_gate()
	cls_page = Mock(
		side_effect=[
			_comments_node([], "c1"),
			_comments_node([], "c2"),
			_comments_node([], None),
		]
	)
	monkeypatch.setattr(cls_gate, "_fetch_page", cls_page)
	cls_gate.fetch_pull_request("o", "r", 1)
	assert [tuple_args[5] for tuple_args, _ in cls_page.call_args_list] == [None, "c1", "c2"]


def test_a_failing_comment_page_raises_instead_of_stopping_early(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Fail closed: an error on a later page propagates, never a silently short list."""
	cls_gate = _load_gate()
	cls_page = Mock(side_effect=[_comments_node([], "c1"), RuntimeError("page two failed")])
	monkeypatch.setattr(cls_gate, "_fetch_page", cls_page)
	with pytest.raises(RuntimeError, match="page two failed"):
		cls_gate.fetch_pull_request("o", "r", 1)


_STR_FILLER = "x" * 400

_ROSTER_NORMALISED = set(_ROSTER_WITH_POSTS)


def test_newest_roster_notice_is_not_truncated() -> None:
	"""A matcher needs the whole notice; truncation is a display concern only."""
	cls_gate = _load_gate()
	str_body = f"{_STR_FILLER} Review rate limited."
	assert cls_gate.newest_roster_notice(
		[_notice("coderabbitai[bot]", str_body)], _ROSTER_NORMALISED
	).endswith("Review rate limited.")


def test_summarise_reviewer_notice_still_truncates_for_display() -> None:
	"""The quoted form stays bounded, or a failure message becomes unreadable."""
	cls_gate = _load_gate()
	str_seen = cls_gate.summarise_reviewer_notice(
		[_notice("coderabbitai[bot]", f"{_STR_FILLER} Review rate limited.")], _ROSTER_NORMALISED
	)
	assert len(str_seen) == cls_gate._INT_NOTICE_DISPLAY_CHARS


def test_the_json_verdict_classifies_a_limit_past_the_display_budget(
	capsys: pytest.CaptureFixture[str],
) -> None:
	"""Exercises the CALL SITE, not the helper — a limit the display form cannot show.

	⚠️ The obvious form of this test — ``classify_reviewer_notice(newest_roster_notice(...))``
	— is a TAUTOLOGY: it wires the two helpers together itself, so it passes no matter which
	one the gate actually calls. Measured: with the fix reverted it stayed green, proving the
	helper works and nothing about the gate. The assertion has to run through
	``_print_missing_review``, which is where the wrong argument was passed.
	"""
	cls_gate = _load_gate()
	cls_gate._print_missing_review(
		True,
		"no declared reviewer ever reported",
		[_notice("coderabbitai[bot]", f"{_STR_FILLER} Review rate limited.")],
		_ROSTER_NORMALISED,
	)
	dict_out = json.loads(capsys.readouterr().out)
	assert dict_out["notice_classification"] == cls_gate.NOTICE_REVIEW_LIMITED


def test_classify_on_the_truncated_form_would_have_missed_it() -> None:
	"""Pins the DEFECT itself: the cut string classifies as OK, so a revert cannot be quiet."""
	cls_gate = _load_gate()
	str_cut = cls_gate.summarise_reviewer_notice(
		[_notice("coderabbitai[bot]", f"{_STR_FILLER} Review rate limited.")],
		_ROSTER_NORMALISED,
	)
	assert cls_gate.classify_reviewer_notice(str_cut) == cls_gate.NOTICE_OK


def test_completion_is_seen_past_the_display_budget() -> None:
	"""4 of 112 real notices buried "Review finished" past 200 chars — a false red."""
	cls_gate = _load_gate()
	assert cls_gate.reviewer_declared_completion(
		[_notice("coderabbitai[bot]", f"{_STR_FILLER} Review finished.")],
		_ROSTER_NORMALISED,
		_HEAD_DATE,
	)


_MARKER = "Fallback review — runtime: codex"
_TUPLE_MARKERS = ("fallback review — runtime:",)


_LADDER_APP = "guilhermegor-review-ladder[bot]"
_SET_POSTERS = frozenset({"guilhermegor-review-ladder"})


def _marker_comment(
	str_association: str, str_login: str = _LADDER_APP, str_typename: str = "Bot"
) -> dict:
	return {
		"author": {"login": str_login, "__typename": str_typename},
		"authorAssociation": str_association,
		"body": f"{_MARKER}\nReviewed head: {_HEAD}\n\n0 finding(s) across 3 reviewed file(s).",
		"createdAt": "2099-01-01T00:00:00Z",
	}


def _missing_with(list_notices: list[dict], tuple_markers: tuple[str, ...]) -> str | None:
	return _load_gate().find_missing_review_problem(
		[],
		{"coderabbitai"},
		"someone-else",
		str_head_oid=_HEAD,
		list_notices=list_notices,
		str_head_date=_HEAD_DATE,
		tuple_markers=tuple_markers,
		set_posters=_SET_POSTERS,
	)


def test_ladder_marker_from_the_pr_author_owner_is_rejected() -> None:
	"""The PR author is the repo OWNER: typing the marker must not self-approve (#761)."""
	dict_forged = _marker_comment("OWNER", "someone-else")
	assert _missing_with([dict_forged], _TUPLE_MARKERS) is not None


def test_ladder_marker_from_the_ladder_app_is_accepted() -> None:
	"""The ladder App posts as a Bot with association NONE; its login is what is trusted."""
	assert _missing_with([_marker_comment("NONE")], _TUPLE_MARKERS) is None


def test_ladder_marker_from_a_user_with_the_bare_app_login_is_rejected() -> None:
	"""A human registering `guilhermegor-review-ladder` is a User, not the App's Bot actor."""
	dict_forged = _marker_comment("NONE", "guilhermegor-review-ladder", "User")
	assert _missing_with([dict_forged], _TUPLE_MARKERS) is not None


def test_ladder_marker_without_an_author_type_is_rejected() -> None:
	"""An author with no `__typename` fails closed."""
	dict_untyped = {**_marker_comment("NONE"), "author": {"login": _LADDER_APP}}
	assert _missing_with([dict_untyped], _TUPLE_MARKERS) is not None


def test_ladder_marker_from_a_non_roster_collaborator_is_rejected() -> None:
	"""A COLLABORATOR outside the posters allowlist cannot forge the marker."""
	dict_forged = _marker_comment("COLLABORATOR", "a-collaborator")
	assert _missing_with([dict_forged], _TUPLE_MARKERS) is not None


def test_ladder_marker_without_any_posters_is_rejected() -> None:
	"""An empty allowlist fails closed, even for the ladder App's login."""
	cls_gate = _load_gate()
	assert not cls_gate.ladder_marker_declared(
		[_marker_comment("NONE")], _TUPLE_MARKERS, _HEAD_DATE, _HEAD
	)


def test_later_marker_from_a_non_poster_does_not_supersede_a_clean_one() -> None:
	"""A forged later marker is ignored, so it can neither approve nor block."""
	dict_forged = {**_marker_comment("OWNER", "someone-else"), "createdAt": "2099-02-01T00:00:00Z"}
	assert _missing_with([_marker_comment("NONE"), dict_forged], _TUPLE_MARKERS) is None


def test_ladder_marker_without_the_roster_row_changes_nothing() -> None:
	"""No `comment-marker` row, no behaviour change."""
	assert _missing_with([_marker_comment("OWNER")], ()) is not None


def test_ladder_marker_quoted_on_a_later_line_is_rejected() -> None:
	"""Only the attribution line itself counts, never a quotation of it."""
	dict_quoted = {**_marker_comment("OWNER"), "body": f"see below\n> {_MARKER}"}
	assert _missing_with([dict_quoted], _TUPLE_MARKERS) is not None


def test_ladder_marker_older_than_the_head_is_rejected() -> None:
	"""A marker posted before the head commit describes superseded code."""
	dict_old = {**_marker_comment("OWNER"), "createdAt": "2000-01-01T00:00:00Z"}
	assert _missing_with([dict_old], _TUPLE_MARKERS) is not None


def test_ladder_marker_for_another_head_is_rejected() -> None:
	"""A marker whose `Reviewed head:` line names a different SHA is not this head's review."""
	dict_other = {
		**_marker_comment("OWNER"),
		"body": f"{_MARKER}\nReviewed head: {'0' * 40}\n\n0 finding(s) across 3 reviewed file(s).",
	}
	assert _missing_with([dict_other], _TUPLE_MARKERS) is not None


def test_ladder_marker_with_findings_is_rejected() -> None:
	"""A ladder review that lists findings must be judged, not auto-accepted (#630)."""
	dict_found = {
		**_marker_comment("OWNER"),
		"body": f"{_MARKER}\nReviewed head: {_HEAD}\n\n2 finding(s) across 3 reviewed file(s).",
	}
	assert _missing_with([dict_found], _TUPLE_MARKERS) is not None


@pytest.mark.parametrize(
	"str_head_line",
	[f"Reviewed head: {_HEAD}  ", f"Reviewed head: {_HEAD}\r", f"  Reviewed head: {_HEAD}"],
)
def test_ladder_marker_tolerates_whitespace_around_the_head_line(str_head_line: str) -> None:
	"""Cosmetic whitespace on the SHA line must not silently block every PR."""
	dict_ws = {
		**_marker_comment("MEMBER"),
		"body": f"{_MARKER}\n{str_head_line}\n\n0 finding(s) across 3 reviewed file(s).",
	}
	assert _missing_with([dict_ws], _TUPLE_MARKERS) is None


def test_ladder_marker_without_a_findings_line_is_rejected() -> None:
	"""Unparsable means "has findings": a prose review never passes."""
	dict_prose = {
		**_marker_comment("OWNER"),
		"body": f"{_MARKER}\nReviewed head: {_HEAD}\n\n- a bug",
	}
	assert _missing_with([dict_prose], _TUPLE_MARKERS) is not None


def test_later_ladder_comment_with_findings_supersedes_an_earlier_clean_one() -> None:
	"""The latest qualifying marker decides: a re-run that found something blocks."""
	dict_later = {
		**_marker_comment("OWNER"),
		"body": f"{_MARKER}\nReviewed head: {_HEAD}\n\n2 finding(s) across 3 reviewed file(s).",
		"createdAt": "2099-02-01T00:00:00Z",
	}
	assert _missing_with([_marker_comment("OWNER"), dict_later], _TUPLE_MARKERS) is not None
	assert _missing_with([dict_later, _marker_comment("OWNER")], _TUPLE_MARKERS) is not None


@pytest.mark.parametrize("str_head_line", ["Reviewed head: " + "0" * 40, "no head line here"])
def test_later_marker_naming_no_valid_head_supersedes_an_earlier_clean_one(
	str_head_line: str,
) -> None:
	"""A later malformed or other-head marker fails closed instead of exposing the clean one."""
	dict_later = {
		**_marker_comment("OWNER"),
		"body": f"{_MARKER}\n{str_head_line}\n\n0 finding(s) across 3 reviewed file(s).",
		"createdAt": "2099-02-01T00:00:00Z",
	}
	assert _missing_with([_marker_comment("OWNER"), dict_later], _TUPLE_MARKERS) is not None


def test_padded_nonzero_findings_line_beside_a_zero_line_is_rejected() -> None:
	"""Trailing or leading whitespace must not hide a non-zero findings line."""
	dict_padded = {
		**_marker_comment("OWNER"),
		"body": f"{_MARKER}\nReviewed head: {_HEAD}\n\n0 finding(s) across 3 reviewed file(s).\n"
		"  3 finding(s) across 3 reviewed file(s). \r",
	}
	assert _missing_with([dict_padded], _TUPLE_MARKERS) is not None


def test_zero_findings_over_zero_files_does_not_clear_the_check() -> None:
	"""A review of no files reviewed nothing, so it proves no review ran."""
	dict_empty = {
		**_marker_comment("OWNER"),
		"body": f"{_MARKER}\nReviewed head: {_HEAD}\n\n0 finding(s) across 0 reviewed file(s).",
	}
	assert _missing_with([dict_empty], _TUPLE_MARKERS) is not None


def _marker_findings_comment() -> dict:
	return {
		**_marker_comment("OWNER"),
		"body": f"{_MARKER}\nReviewed head: {_HEAD}\n\n2 finding(s) across 3 reviewed file(s).",
	}


def test_marker_comment_with_findings_needs_an_answer() -> None:
	"""A trusted marker comment listing findings is read as a review body."""
	list_problems = _load_gate().find_review_body_problems(
		[], [_marker_findings_comment()], _BOTH_ROSTER, tuple_markers=_TUPLE_MARKERS
	)
	assert len(list_problems) == 1


def test_roster_authored_marker_comment_is_one_problem_not_two() -> None:
	"""A marker comment from a roster login is read once, not as a notice AND as a marker."""
	dict_roster_marker = {**_marker_findings_comment(), "author": {"login": "coderabbitai"}}
	list_problems = _load_gate().find_review_body_problems(
		[], [dict_roster_marker], _BOTH_ROSTER, tuple_markers=_TUPLE_MARKERS
	)
	assert len(list_problems) == 1


def test_clean_marker_comment_needs_no_answer() -> None:
	"""A trusted marker comment reporting zero findings is not a review body with findings."""
	list_problems = _load_gate().find_review_body_problems(
		[], [_marker_comment("OWNER")], _BOTH_ROSTER, tuple_markers=_TUPLE_MARKERS
	)
	assert list_problems == []


def test_marker_comment_never_answers_another_reviews_findings() -> None:
	"""A long marker comment by a human must not clear a roster review body unread."""
	dict_review = {
		"author": {"login": "coderabbitai", "__typename": "Bot"},
		"state": "COMMENTED",
		"body": "- **Major** a bug\n",
		"submittedAt": "2000-01-01T00:00:00Z",
	}
	dict_marker = {**_marker_findings_comment(), "createdAt": "2099-01-01T00:00:00Z"}
	dict_marker["author"] = {"login": "owner", "__typename": "User"}
	list_problems = _load_gate().find_review_body_problems(
		[dict_review], [dict_marker], _BOTH_ROSTER, tuple_markers=_TUPLE_MARKERS
	)
	assert any("coderabbitai" in str_problem for str_problem in list_problems)


@pytest.fixture
def path_marker_root(tmp_path: Path) -> Path:
	"""Write a roster holding one reviewer and one marker row."""
	(tmp_path / ".review-bots.yaml").write_text(
		"reviewers:\n"
		"  - login: coderabbitai[bot]\n    posts: threads\n"
		'  - kind: comment-marker\n    marker: "Fallback review — runtime:"\n',
		encoding="utf-8",
	)
	return tmp_path


def test_load_comment_markers_reads_the_marker_row(path_marker_root: Path) -> None:
	"""The marker row is returned lower-cased."""
	assert _load_gate().load_comment_markers(path_marker_root) == _TUPLE_MARKERS


@pytest.mark.parametrize("str_row", ["    marker:\n", '    marker: ""\n', ""])
def test_load_comment_markers_skips_a_row_without_a_marker(tmp_path: Path, str_row: str) -> None:
	"""A comment-marker row with no usable marker is dropped, never a KeyError."""
	(tmp_path / ".review-bots.yaml").write_text(
		"reviewers:\n  - kind: comment-marker\n" + str_row, encoding="utf-8"
	)
	assert _load_gate().load_comment_markers(tmp_path) == ()


def test_load_comment_markers_ignores_a_scalar_reviewer_row(tmp_path: Path) -> None:
	"""A bare-string reviewers entry is skipped, never an AttributeError."""
	(tmp_path / ".review-bots.yaml").write_text(
		"reviewers:\n  - coderabbitai[bot]\n  - kind: comment-marker\n    marker: m\n",
		encoding="utf-8",
	)
	assert _load_gate().load_comment_markers(tmp_path) == ("m",)


def test_load_marker_posters_normalises_the_bot_suffix(tmp_path: Path) -> None:
	"""`posters:` is read in the REST spelling and compared in the GraphQL one."""
	(tmp_path / ".review-bots.yaml").write_text(
		"reviewers:\n  - kind: comment-marker\n    marker: m\n"
		"    posters:\n      - x[bot]\n      - y\n",
		encoding="utf-8",
	)
	assert _load_gate().load_marker_posters(tmp_path) == frozenset({"x", "y"})


@pytest.mark.parametrize(
	"str_posters",
	["    posters: foo\n", "    posters:\n      - 7\n", '    posters:\n      - ""\n'],
)
def test_load_marker_posters_rejects_a_malformed_value(tmp_path: Path, str_posters: str) -> None:
	"""A scalar or non-string entry trusts nobody instead of becoming single characters."""
	(tmp_path / ".review-bots.yaml").write_text(
		"reviewers:\n  - kind: comment-marker\n    marker: m\n" + str_posters,
		encoding="utf-8",
	)
	assert _load_gate().load_marker_posters(tmp_path) == frozenset()


def test_load_marker_posters_is_empty_without_the_field(path_marker_root: Path) -> None:
	"""A marker row with no `posters:` allows nobody."""
	assert _load_gate().load_marker_posters(path_marker_root) == frozenset()


def test_load_roster_ignores_the_marker_row(path_marker_root: Path) -> None:
	"""A marker row has no login, so the login roster is untouched."""
	assert _load_gate().load_roster(path_marker_root) == {"coderabbitai": "threads"}


def _git_env() -> dict[str, str]:
	"""Return the environment without inherited ``GIT_*`` variables.

	Returns
	-------
	dict[str, str]
		``os.environ`` minus every ``GIT_*`` key.
	"""
	return {
		str_key: str_value
		for str_key, str_value in os.environ.items()
		if not str_key.startswith("GIT_")
	}


def _git(path_repo: Path, *list_args: str, bool_check: bool = True) -> str:
	"""Run git in ``path_repo`` and return stdout, raising on a non-zero exit.

	Raising matters: a silent setup failure would yield empty commit ids, and the negative
	witnesses would then pass because two broken fingerprints differ. The ``GIT_*`` variables a
	pre-commit hook exports (``GIT_INDEX_FILE``) are dropped, or ``git add`` in the scratch repo
	writes into the index of the repository being committed.

	Parameters
	----------
	path_repo : Path
		Repository directory.
	*list_args : str
		Arguments after ``git``.
	bool_check : bool
		``False`` only for the one command expected to exit non-zero (a conflicting merge).

	Returns
	-------
	str
		Stripped stdout.
	"""
	list_cmd = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
	cls_run = subprocess.run(  # noqa: S603
		[*list_cmd, "-C", str(path_repo), *list_args],
		capture_output=True,
		text=True,
		check=bool_check,
		env=_git_env(),
	)
	return cls_run.stdout.strip()


def _commit(path_repo: Path, str_file: str, str_text: str) -> str:
	"""Write ``str_text`` to ``str_file``, commit it and return the new commit.

	Parameters
	----------
	path_repo : Path
		Repository directory.
	str_file : str
		File to write, relative to the repo.
	str_text : str
		File content.

	Returns
	-------
	str
		The new commit oid.
	"""
	(path_repo / str_file).write_text(str_text)
	_git(path_repo, "add", str_file)
	_git(path_repo, "commit", "-m", f"edit {str_file}")
	return _git(path_repo, "rev-parse", "HEAD")


def _patch_id(path_repo: Path, str_oid: str) -> str:
	"""Return ``git patch-id --stable`` of the PR's own patch at ``str_oid``.

	Parameters
	----------
	path_repo : Path
		Repository directory, where ``main`` is the base.
	str_oid : str
		Commit to measure.

	Returns
	-------
	str
		The patch id, an independent oracle for the compare-API fingerprint.

	Raises
	------
	ValueError
		If ``git patch-id`` prints nothing, which is an empty diff or a failed run.
	"""
	str_base = _git(path_repo, "merge-base", "main", str_oid)
	str_diff = _git(path_repo, "diff", str_base, str_oid)
	cls_run = subprocess.run(  # noqa: S603
		["git", "patch-id", "--stable"],  # noqa: S607
		input=str_diff + "\n",
		capture_output=True,
		text=True,
		check=True,
		env=_git_env(),
	)
	str_patch_id, _ = cls_run.stdout.split()
	return str_patch_id


_DICT_STATUS = {"A": "added", "M": "modified", "D": "removed", "R": "renamed"}


def _file_entry(path_repo: Path, str_base: str, str_oid: str, str_line: str) -> dict:
	"""Build one ``files`` entry of the compare API from a real ``git diff``.

	Parameters
	----------
	path_repo : Path
		Repository directory.
	str_base : str
		Merge base of ``main`` and the commit.
	str_oid : str
		Commit being compared.
	str_line : str
		One ``git diff --name-status`` line: a status code, then one tab-separated path
		(two for a rename: the old one, then the new one).

	Returns
	-------
	dict
		``filename``, ``status`` and ``patch`` (starting at the first hunk, as the API does),
		plus ``previous_filename`` for a rename.
	"""
	str_code, *list_names = str_line.split("\t")
	str_diff = _git(path_repo, "diff", "-M", str_base, str_oid, "--", *list_names)
	dict_rename = {"R": {"previous_filename": list_names[0]}}.get(str_code[0], {})
	return {
		"filename": list_names[-1],
		"status": _DICT_STATUS[str_code[0]],
		"patch": str_diff[str_diff.index("@@") :],
		**dict_rename,
	}


def _compare_files(path_repo: Path, str_oid: str) -> list[dict]:
	"""Return the compare-shaped ``files`` list of the PR's own patch at ``str_oid``.

	Parameters
	----------
	path_repo : Path
		Repository directory, where ``main`` is the base.
	str_oid : str
		Commit to measure.

	Returns
	-------
	list of dict
		What ``compare/main...<oid>`` would list, built from real ``git diff`` output.
	"""
	str_base = _git(path_repo, "merge-base", "main", str_oid)
	list_lines = _git(path_repo, "diff", "-M", "--name-status", str_base, str_oid).splitlines()
	return list(map(functools.partial(_file_entry, path_repo, str_base, str_oid), list_lines))


def _real_fingerprint(path_repo: Path, str_oid: str) -> str:
	"""Run the PRODUCTION ``patch_fingerprint`` on compare-shaped files from real diffs.

	Parameters
	----------
	path_repo : Path
		Repository directory, where ``main`` is the base.
	str_oid : str
		Commit to measure.

	Returns
	-------
	str
		The gate's own digest.
	"""
	return _load_gate().patch_fingerprint(_compare_files(path_repo, str_oid))


def _overlap_repo(path_repo: Path, str_old: str, str_new: str) -> tuple[str, str]:
	"""Build a PR that edits line 10, then merge a ``main`` that rewrites ``str_old``.

	Parameters
	----------
	path_repo : Path
		Empty repository directory.
	str_old : str
		Text of the 20-line file that ``main`` replaces. Line 12 is inside the PR hunk's
		3-line context; line 20 and the top of the file are outside it.
	str_new : str
		Its replacement.

	Returns
	-------
	tuple of str
		The reviewed commit and the head after the conflict-free merge of ``main``.
	"""
	str_text = "\n".join(map(str, range(1, 21))) + "\n"
	_git(path_repo, "init", "-b", "main")
	_commit(path_repo, "a.txt", str_text)
	_git(path_repo, "checkout", "-b", "feat")
	str_review = _commit(path_repo, "a.txt", str_text.replace("\n10\n", "\nfeat\n"))
	_git(path_repo, "checkout", "main")
	_commit(path_repo, "a.txt", str_text.replace(str_old, str_new, 1))
	_git(path_repo, "checkout", "feat")
	_git(path_repo, "merge", "--no-edit", "main")
	return str_review, _git(path_repo, "rev-parse", "HEAD")


@pytest.fixture
def dict_repo(tmp_path: Path) -> dict:
	"""Build a PR branch with a review commit ``R`` and four candidate heads.

	Parameters
	----------
	tmp_path : Path
		Pytest temp dir.

	Returns
	-------
	dict
		``path``, ``review`` (R) and the heads ``clean_merge``, ``conflict_merge``,
		``new_commit`` and ``rewritten``.
	"""
	str_text = "1\n{}\n3\n4\n5\n6\n7\n8\n9\n"
	_git(tmp_path, "init", "-b", "main")
	_commit(tmp_path, "a.txt", str_text.format("2"))
	_commit(tmp_path, "b.txt", "b\n")
	_git(tmp_path, "checkout", "-b", "feat")
	str_review = _commit(tmp_path, "a.txt", str_text.format("feat"))
	_git(tmp_path, "checkout", "main")
	_commit(tmp_path, "b.txt", "b main\n")
	_commit(tmp_path, "a.txt", str_text.format("main"))
	_git(tmp_path, "checkout", "-b", "clean", str_review)
	_git(tmp_path, "merge", "--no-edit", "main~1")
	str_clean = _git(tmp_path, "rev-parse", "HEAD")
	_git(tmp_path, "checkout", "-b", "conflict", str_review)
	_git(tmp_path, "merge", "--no-edit", "main", bool_check=False)
	str_conflict = _commit(tmp_path, "a.txt", str_text.format("resolved"))
	_git(tmp_path, "checkout", "-b", "more", str_review)
	str_new = _commit(tmp_path, "c.txt", "new\n")
	_git(tmp_path, "checkout", "-b", "rewrite", "main")
	str_rewritten = _commit(tmp_path, "a.txt", str_text.format("rewritten"))
	list_oids = [str_review, str_clean, str_conflict, str_new, str_rewritten]
	assert set(map(len, list_oids)) == {40}, "fixture built an empty or malformed commit id"
	assert len(set(list_oids)) == len(list_oids), "fixture built duplicate commits"
	return {
		"path": tmp_path,
		"review": str_review,
		"clean_merge": str_clean,
		"conflict_merge": str_conflict,
		"new_commit": str_new,
		"rewritten": str_rewritten,
	}


def _covers(dict_repo: dict, str_head_key: str) -> bool:
	"""Ask the gate whether the review at ``R`` covers the head named by ``str_head_key``.

	Parameters
	----------
	dict_repo : dict
		The :func:`dict_repo` fixture value.
	str_head_key : str
		Key of the head commit in that dict.

	Returns
	-------
	bool
		The gate's verdict, using a real ``git patch-id`` as the fingerprint.
	"""
	fn_fingerprint = functools.partial(_patch_id, dict_repo["path"])
	str_head = dict_repo[str_head_key]
	return _load_gate().review_covers_head(
		fn_fingerprint, dict_repo["review"], str_head, fn_fingerprint(str_head)
	)


def test_review_covers_head_carry_forward_notice_leaves_stdout_empty(
	capsys: pytest.CaptureFixture[str],
) -> None:
	"""``--json`` prints the verdict on stdout, so the notice must not share that stream."""
	_load_gate().review_covers_head(lambda str_oid: "same", "a" * 40, "b" * 40, "same")
	assert capsys.readouterr().out == ""


def test_review_covers_head_carry_forward_notice_goes_to_stderr(
	capsys: pytest.CaptureFixture[str],
) -> None:
	"""The one line saying a review was carried forward is still printed, on stderr."""
	_load_gate().review_covers_head(lambda str_oid: "same", "a" * 40, "b" * 40, "same")
	assert "still covers" in capsys.readouterr().err


def test_review_covers_head_merge_of_base_without_conflict_carries_forward(
	dict_repo: dict,
) -> None:
	"""An update-branch that only merges the base leaves the PR's patch alone."""
	assert _covers(dict_repo, "clean_merge") is True


def test_review_covers_head_conflict_resolving_merge_stays_superseded(dict_repo: dict) -> None:
	"""Resolving a conflict changes what the PR contributes, so the review is stale."""
	assert _covers(dict_repo, "conflict_merge") is False


def test_review_covers_head_new_commit_stays_superseded(dict_repo: dict) -> None:
	"""A new commit adds code nobody reviewed."""
	assert _covers(dict_repo, "new_commit") is False


def test_review_covers_head_rewritten_code_stays_superseded(dict_repo: dict) -> None:
	"""A force-push that rewrites the PR's code is new code under an old review."""
	assert _covers(dict_repo, "rewritten") is False


def test_review_covers_head_patch_unavailable_fails_closed() -> None:
	"""A missing commit or an API error is never read as 'covered'."""
	cls_gate = _load_gate()
	fn_broken = Mock(side_effect=RuntimeError("compare failed"))
	assert cls_gate.review_covers_head(fn_broken, "a" * 40, _HEAD, "digest") is False


def test_find_missing_review_problem_carried_review_passes(dict_repo: dict) -> None:
	"""End to end: a roster review at R, head H only a base merge, no problem."""
	cls_gate = _load_gate()
	assert (
		cls_gate.find_missing_review_problem(
			[_review("coderabbitai[bot]", dict_repo["review"])],
			{"coderabbitai"},
			str_head_oid=dict_repo["clean_merge"],
			fn_fingerprint=lambda str_oid: _patch_id(dict_repo["path"], str_oid),
		)
		is None
	)


def test_patch_fingerprint_ignores_hunk_line_numbers() -> None:
	"""Main moving lines above the PR's hunk shifts ``@@`` offsets and nothing else."""
	cls_gate = _load_gate()
	dict_at_review = {"filename": "a", "status": "modified", "patch": "@@ -2,1 +2,1 @@ fn\n-x\n+y"}
	dict_at_head = {"filename": "a", "status": "modified", "patch": "@@ -9,1 +9,1 @@ fn\n-x\n+y"}
	assert cls_gate.patch_fingerprint([dict_at_review]) == cls_gate.patch_fingerprint(
		[dict_at_head]
	)


def test_patch_fingerprint_ignores_unchanged_context_lines() -> None:
	"""Main editing lines next to the PR's hunk changes context only, never the PR's patch."""
	cls_gate = _load_gate()
	dict_at_review = {
		"filename": "a",
		"status": "modified",
		"patch": "@@ -2,3 +2,3 @@ fn\n old_above\n-x\n+y\n old_below",
	}
	dict_at_head = {
		"filename": "a",
		"status": "modified",
		"patch": "@@ -2,3 +2,3 @@ fn\n new_above\n-x\n+y\n new_below",
	}
	assert cls_gate.patch_fingerprint([dict_at_review]) == cls_gate.patch_fingerprint(
		[dict_at_head]
	)


def test_patch_fingerprint_changed_added_line_differs() -> None:
	"""A different ``+`` line is different code, whatever the context says."""
	cls_gate = _load_gate()
	str_head = "@@ -2 +2 @@ fn\n ctx\n-x\n+"
	dict_reviewed = {"filename": "a", "status": "modified", "patch": str_head + "y"}
	dict_edited = {"filename": "a", "status": "modified", "patch": str_head + "z"}
	assert cls_gate.patch_fingerprint([dict_reviewed]) != cls_gate.patch_fingerprint([dict_edited])


def test_patch_fingerprint_file_without_patch_text_raises() -> None:
	"""The API omits ``patch`` for binary or oversized files, which cannot be compared."""
	cls_gate = _load_gate()
	with pytest.raises(ValueError, match="no patch text"):
		cls_gate.patch_fingerprint([{"filename": "big.bin", "status": "added"}])


def test_patch_fingerprint_same_edit_in_another_function_matches() -> None:
	"""Hunk headers are not hashed, so the same edit in another function matches.

	Deliberate (blueprintx#848): main's edits split and re-head hunks, so any hash of
	``@@`` lines breaks the carry-forward on a PR whose own lines did not change.
	"""
	cls_gate = _load_gate()
	dict_reviewed = {"filename": "a", "status": "modified", "patch": "@@ -2 +2 @@ def one\n-x\n+y"}
	dict_moved = {"filename": "a", "status": "modified", "patch": "@@ -2 +2 @@ def two\n-x\n+y"}
	assert cls_gate.patch_fingerprint([dict_reviewed]) == cls_gate.patch_fingerprint([dict_moved])


def test_patch_fingerprint_hunk_split_by_a_base_edit_matches() -> None:
	"""One hunk and the same ``+`` lines split into two re-headed hunks digest equally."""
	cls_gate = _load_gate()
	str_one = "@@ -5,0 +6,2 @@ test_a() {\n+one\n+two"
	str_two = "@@ -5,0 +6,1 @@ test_a() {\n+one\n@@ -20,0 +30,1 @@ main() {\n ctx\n+two"
	dict_one = {"filename": "a", "status": "modified", "patch": str_one}
	dict_two = {"filename": "a", "status": "modified", "patch": str_two}
	assert cls_gate.patch_fingerprint([dict_one]) == cls_gate.patch_fingerprint([dict_two])


def test_patch_fingerprint_field_boundaries_are_unambiguous() -> None:
	"""A filename carrying the old separator must not collide with a different file."""
	cls_gate = _load_gate()
	dict_plain = {"filename": "a", "status": "modified", "patch": "p"}
	dict_crafted = {"filename": "a\nmodified", "status": "", "previous_filename": "p", "patch": ""}
	assert cls_gate.patch_fingerprint([dict_plain]) != cls_gate.patch_fingerprint([dict_crafted])


def test_fetch_patch_fingerprint_compares_against_the_pinned_base_sha(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Both compares name the base by the SHA read once, never by a movable branch name."""
	cls_gate = _load_gate()
	json_body = '{"files": [{"filename": "a", "status": "modified", "patch": "x"}]}'
	fn_run = Mock(return_value=Mock(returncode=0, stdout=json_body))
	monkeypatch.setattr(cls_gate.subprocess, "run", fn_run)
	cls_gate.fetch_patch_fingerprint("o", "r", "basesha", "headsha")
	assert fn_run.call_args[0][0][2].startswith("repos/o/r/compare/basesha...headsha")


def test_fetch_patch_fingerprint_unknown_base_sha_fails_closed() -> None:
	"""No pinned base means no comparison: the gate cannot say which base was measured."""
	cls_gate = _load_gate()
	with pytest.raises(ValueError, match="base commit is unknown"):
		cls_gate.fetch_patch_fingerprint("o", "r", "", "headsha")


@pytest.mark.parametrize(
	("str_head_key", "bool_expected"),
	[
		("clean_merge", True),
		("conflict_merge", False),
		("new_commit", False),
		("rewritten", False),
	],
)
def test_review_covers_head_production_fingerprint_on_real_diffs(
	dict_repo: dict, str_head_key: str, bool_expected: bool
) -> None:
	"""The production digest, fed compare-shaped files from real ``git diff``, decides it."""
	fn_fingerprint = functools.partial(_real_fingerprint, dict_repo["path"])
	str_head = dict_repo[str_head_key]
	bool_covered = _load_gate().review_covers_head(
		fn_fingerprint, dict_repo["review"], str_head, fn_fingerprint(str_head)
	)
	assert bool_covered is bool_expected


@pytest.mark.parametrize(
	("str_old", "str_new", "bool_expected"),
	[
		("\n20\n", "\nmain\n", True),
		("1\n2\n", "0\n1\n2\n", True),
		("\n12\n", "\nmain\n", True),
	],
)
def test_review_covers_head_main_edit_relative_to_the_hunk(
	tmp_path: Path, str_old: str, str_new: str, bool_expected: bool
) -> None:
	"""A clean merge carries a review forward even when main edits the hunk's context lines.

	The digest hashes the PR's ``+``/``-`` lines only, so no conflict-free base edit,
	inside the 3-line window or outside it, changes it (blueprintx#848).
	"""
	str_review, str_head = _overlap_repo(tmp_path, str_old, str_new)
	fn_fingerprint = functools.partial(_real_fingerprint, tmp_path)
	bool_covered = _load_gate().review_covers_head(
		fn_fingerprint, str_review, str_head, fn_fingerprint(str_head)
	)
	assert bool_covered is bool_expected


def _rename_repo(path_repo: Path) -> tuple[str, str]:
	"""Build two PRs that rename DIFFERENT identical files to the same name, same edit.

	Parameters
	----------
	path_repo : Path
		Empty repository directory.

	Returns
	-------
	tuple of str
		The commit that renamed ``a.txt`` and the one that renamed ``b.txt``; both give
		``c.txt`` the same content, so their hunks are identical.
	"""
	str_text = "\n".join(map(str, range(1, 21))) + "\n"
	_git(path_repo, "init", "-b", "main")
	_commit(path_repo, "a.txt", str_text)
	_commit(path_repo, "b.txt", str_text)
	_git(path_repo, "checkout", "-b", "from-a")
	_git(path_repo, "mv", "a.txt", "c.txt")
	str_from_a = _commit(path_repo, "c.txt", str_text.replace("\n10\n", "\nfeat\n"))
	_git(path_repo, "checkout", "-b", "from-b", "main")
	_git(path_repo, "mv", "b.txt", "c.txt")
	return str_from_a, _commit(path_repo, "c.txt", str_text.replace("\n10\n", "\nfeat\n"))


def test_patch_fingerprint_rename_from_another_file_differs_on_a_real_diff(
	tmp_path: Path,
) -> None:
	"""Only ``previous_filename`` tells the two renames apart, so it must be hashed."""
	str_from_a, str_from_b = _rename_repo(tmp_path)
	assert _real_fingerprint(tmp_path, str_from_a) != _real_fingerprint(tmp_path, str_from_b)


def test_patch_fingerprint_whole_file_page_raises() -> None:
	"""A full 300-file list may be cut off by the API, so it is not trusted."""
	cls_gate = _load_gate()
	dict_file = {"filename": "a", "status": "modified", "patch": "p"}
	with pytest.raises(ValueError, match="300 file"):
		cls_gate.patch_fingerprint([dict_file] * 300)


def test_review_covers_head_malformed_file_entry_fails_closed(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""A compare response whose file entry lacks ``filename`` is "not covered", not a crash."""
	cls_gate = _load_gate()
	json_body = '{"files": [{"patch": "x"}]}'
	monkeypatch.setattr(
		cls_gate.subprocess, "run", Mock(return_value=Mock(returncode=0, stdout=json_body))
	)
	fn_fingerprint = functools.partial(cls_gate.fetch_patch_fingerprint, "o", "r", "base")
	assert cls_gate.review_covers_head(fn_fingerprint, "a" * 40, "b" * 40, "digest") is False


def _failing_compare(cls_gate: ModuleType, monkeypatch: pytest.MonkeyPatch) -> Mock:
	"""Make every compare call fail, and return the mock that counts them.

	Parameters
	----------
	cls_gate : ModuleType
		The loaded gate.
	monkeypatch : pytest.MonkeyPatch
		Pytest's patcher.

	Returns
	-------
	Mock
		The stand-in for ``fetch_patch_fingerprint``.
	"""
	fn_fetch = Mock(side_effect=RuntimeError("compare failed: 502"))
	monkeypatch.setattr(cls_gate, "fetch_patch_fingerprint", fn_fetch)
	return fn_fetch


_PR_PLAIN = {"baseRefOid": "base", "timelineItems": {"nodes": []}}
_PR_RETARGETED = {
	"baseRefOid": "base",
	"timelineItems": {"nodes": [{"__typename": "BaseRefChangedEvent"}]},
}


def _three_reviews() -> list[dict]:
	"""Return roster reviews at three distinct commits, none at ``_HEAD``.

	Returns
	-------
	list of dict
		Three reviews by the roster's CodeRabbit.
	"""
	return [_review("coderabbitai[bot]", str_oid * 40) for str_oid in "abc"]


def test_find_missing_review_problem_failing_head_compare_is_called_once(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""A head whose patch cannot be read stops the loop; it is not refetched per review."""
	cls_gate = _load_gate()
	fn_fetch = _failing_compare(cls_gate, monkeypatch)
	cls_gate.find_missing_review_problem(
		_three_reviews(),
		{"coderabbitai"},
		str_head_oid=_HEAD,
		fn_fingerprint=cls_gate._compare_fingerprint(_PR_PLAIN, "o/r"),
	)
	assert fn_fetch.call_count == 1


def test_find_missing_review_problem_failing_head_compare_reports_the_reason(
	capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""A broken carry-forward is diagnosable: the reason reaches stderr."""
	cls_gate = _load_gate()
	_failing_compare(cls_gate, monkeypatch)
	cls_gate.find_missing_review_problem(
		_three_reviews(),
		{"coderabbitai"},
		str_head_oid=_HEAD,
		fn_fingerprint=cls_gate._compare_fingerprint(_PR_PLAIN, "o/r"),
	)
	assert "compare failed: 502" in capsys.readouterr().err


def test_find_missing_review_problem_failing_head_compare_leaves_stdout_empty(
	capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""The failure line is a diagnostic: stdout stays clean for ``--json``."""
	cls_gate = _load_gate()
	_failing_compare(cls_gate, monkeypatch)
	cls_gate.find_missing_review_problem(
		_three_reviews(),
		{"coderabbitai"},
		str_head_oid=_HEAD,
		fn_fingerprint=cls_gate._compare_fingerprint(_PR_PLAIN, "o/r"),
	)
	assert capsys.readouterr().out == ""


def test_find_missing_review_problem_passing_pr_makes_no_compare_call(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""A completion notice already passes the PR, so carry-forward costs no API call."""
	cls_gate = _load_gate()
	fn_fingerprint = Mock(return_value="digest")
	monkeypatch.setattr(cls_gate, "reviewer_declared_completion", lambda *_, **__: True)
	cls_gate.find_missing_review_problem(
		_three_reviews(),
		{"coderabbitai"},
		str_head_oid=_HEAD,
		fn_fingerprint=fn_fingerprint,
	)
	assert fn_fingerprint.call_count == 0


@pytest.mark.parametrize(
	"cls_error", [subprocess.TimeoutExpired("gh", 60), FileNotFoundError("gh")]
)
def test_review_covers_head_hung_or_missing_gh_fails_closed(
	monkeypatch: pytest.MonkeyPatch, cls_error: Exception
) -> None:
	"""A timeout or a missing ``gh`` binary means "not covered", never a crash."""
	cls_gate = _load_gate()
	monkeypatch.setattr(cls_gate.subprocess, "run", Mock(side_effect=cls_error))
	fn_fingerprint = functools.partial(cls_gate.fetch_patch_fingerprint, "o", "r", "base")
	assert cls_gate.review_covers_head(fn_fingerprint, "a" * 40, "b" * 40, "digest") is False


def test_fetch_patch_fingerprint_bounds_the_compare_call(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""The compare call carries a timeout, so a hung ``gh`` cannot stall the job."""
	cls_gate = _load_gate()
	json_body = '{"files": [{"filename": "a", "status": "modified", "patch": "x"}]}'
	fn_run = Mock(return_value=Mock(returncode=0, stdout=json_body))
	monkeypatch.setattr(cls_gate.subprocess, "run", fn_run)
	cls_gate.fetch_patch_fingerprint("o", "r", "base", "head")
	assert fn_run.call_args.kwargs["timeout"] > 0


def test_reviewed_commits_dismissed_review_is_not_revived() -> None:
	"""A dismissal retracts the review; a later merge must not bring it back."""
	cls_gate = _load_gate()
	dict_dismissed = {**_review("coderabbitai[bot]", "a" * 40), "state": "DISMISSED"}
	assert cls_gate.reviewed_commits([dict_dismissed], {"coderabbitai"}) == []


@pytest.mark.parametrize(
	("str_body", "int_expected"),
	[("0 findings across 3 reviewed files", 0), ("2 findings across 3 reviewed files", 1)],
)
def test_main_carried_review_still_owes_a_later_findings_body(
	tmp_path: Path,
	monkeypatch: pytest.MonkeyPatch,
	str_body: str,
	int_expected: int,
) -> None:
	"""R1 clean on P, R2 with findings on P', the head back at P: R2 is still answered.

	Carry-forward decides only whether SOME review covers the head. The findings of every
	submitted review, thread or body, are audited by the half that runs after it.
	"""
	cls_gate = _load_gate()
	(tmp_path / ".review-bots.yaml").write_text(
		"reviewers:\n  - login: guilhermegor-review-ladder[bot]\n    posts: threads\n",
		encoding="utf-8",
	)
	monkeypatch.chdir(tmp_path)
	monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
	monkeypatch.setenv("PR_NUMBER", "1")
	str_login = "guilhermegor-review-ladder"
	str_attribution = "Fallback review — runtime: claude, model: m (selected by: s)\n"
	dict_pr = {
		"author": {"login": "someone"},
		"headRefOid": _HEAD,
		"baseRefOid": "base",
		"timelineItems": {"nodes": []},
		"comments": {"nodes": [], "pageInfo": {"hasNextPage": False}},
		"reviews": {
			"nodes": [
				{
					**_review(str_login, "a" * 40),
					"state": "COMMENTED",
					"body": str_attribution + "0 findings across 3 reviewed files",
					"submittedAt": "2026-10-01T00:00:00Z",
				},
				{
					**_review(str_login, "b" * 40),
					"state": "COMMENTED",
					"body": str_attribution + str_body,
					"submittedAt": "2026-10-02T00:00:00Z",
				},
			]
		},
		"reviewThreads": {"nodes": []},
		"commits": {"nodes": []},
	}
	monkeypatch.setattr(cls_gate, "fetch_pull_request", lambda *_: dict_pr)
	monkeypatch.setattr(cls_gate, "fetch_patch_fingerprint", lambda *_: "same patch")
	assert cls_gate.main([]) == int_expected


def _carried_main(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, list_argv: list[str]) -> int:
	"""Run ``main`` on a PR whose only review sits at an older commit with the same patch.

	Parameters
	----------
	tmp_path : Path
		Pytest temp dir, where the roster file is written.
	monkeypatch : pytest.MonkeyPatch
		Pytest's patcher.
	list_argv : list of str
		CLI arguments.

	Returns
	-------
	int
		The gate's exit code.
	"""
	cls_gate = _load_gate()
	(tmp_path / ".review-bots.yaml").write_text(
		"reviewers:\n  - login: coderabbitai[bot]\n    posts: threads\n", encoding="utf-8"
	)
	monkeypatch.chdir(tmp_path)
	monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
	monkeypatch.setenv("PR_NUMBER", "1")
	dict_pr = {
		"author": {"login": "someone"},
		"headRefOid": _HEAD,
		"baseRefOid": "base",
		"timelineItems": {"nodes": []},
		"comments": {"nodes": [], "pageInfo": {"hasNextPage": False}},
		"reviews": {
			"nodes": [
				{
					**_review("coderabbitai[bot]", "a" * 40),
					"author": {"login": "coderabbitai[bot]", "__typename": "Bot"},
					"state": "COMMENTED",
				}
			]
		},
		"reviewThreads": {"nodes": []},
		"commits": {"nodes": []},
	}
	monkeypatch.setattr(cls_gate, "fetch_pull_request", lambda *_: dict_pr)
	monkeypatch.setattr(cls_gate, "fetch_patch_fingerprint", lambda *_: "same patch")
	return cls_gate.main(list_argv)


def test_main_carried_review_is_visible_in_the_normal_output(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
	"""A pass that rests on a carried-forward review says so in the verdict, not only on stderr."""
	_carried_main(tmp_path, monkeypatch, [])
	assert "carried forward from aaaaaaa" in capsys.readouterr().out


def test_main_carried_review_is_a_json_field_and_nothing_else_on_stdout(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
	"""Under ``--json`` stdout stays ONE document, which names the carrying commit."""
	_carried_main(tmp_path, monkeypatch, ["--json"])
	assert json.loads(capsys.readouterr().out)["carried_forward_from"] == "a" * 40


def test_find_missing_review_problem_retargeted_pr_stays_superseded(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""An otherwise-equal fingerprint is not enough once the base branch was changed."""
	cls_gate = _load_gate()
	monkeypatch.setattr(cls_gate, "fetch_patch_fingerprint", lambda *_: "same patch")
	str_problem = cls_gate.find_missing_review_problem(
		_three_reviews(),
		{"coderabbitai"},
		str_head_oid=_HEAD,
		fn_fingerprint=cls_gate._compare_fingerprint(_PR_RETARGETED, "o/r"),
	)
	assert "SUPERSEDED" in str_problem


def test_find_missing_review_problem_retargeted_pr_says_why_on_stderr(
	capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""The refusal is diagnosable: the reason names the base change."""
	cls_gate = _load_gate()
	monkeypatch.setattr(cls_gate, "fetch_patch_fingerprint", lambda *_: "same patch")
	cls_gate.find_missing_review_problem(
		_three_reviews(),
		{"coderabbitai"},
		str_head_oid=_HEAD,
		fn_fingerprint=cls_gate._compare_fingerprint(_PR_RETARGETED, "o/r"),
	)
	assert "base branch was changed" in capsys.readouterr().err


def _timed_review(
	str_time: str, str_login: str = "coderabbitai[bot]", str_state: str = "COMMENTED"
) -> dict:
	"""Build a review at ``a * 40`` submitted at ``str_time``.

	Parameters
	----------
	str_time : str
		``submittedAt`` of the review.
	str_login : str
		Review author's login.
	str_state : str
		Review state.

	Returns
	-------
	dict
		A review shaped like the GraphQL response.
	"""
	return {**_review(str_login, "a" * 40), "submittedAt": str_time, "state": str_state}


def _retargeted_pr(list_change_times: list[str], list_reviews: list[dict]) -> dict:
	"""Build a PR node whose base changed at each time.

	Parameters
	----------
	list_change_times : list of str
		``createdAt`` of each base-change event.
	list_reviews : list of dict
		The PR's reviews.

	Returns
	-------
	dict
		A ``pullRequest`` node shaped like the GraphQL response.
	"""
	return {
		"baseRefOid": "base",
		"timelineItems": {
			"nodes": [
				{"__typename": "BaseRefChangedEvent", "createdAt": str_time}
				for str_time in list_change_times
			]
		},
		"reviews": {"nodes": list_reviews},
	}


_T_BEFORE = "2026-10-15T08:00:00Z"
_T_CHANGE = "2026-10-15T09:16:00Z"
_T_MID = "2026-10-15T10:00:00Z"
_T_LATER_CHANGE = "2026-10-15T12:00:00Z"
_T_AFTER = "2026-10-15T15:29:00Z"


@pytest.mark.parametrize(
	("list_change_times", "list_reviews", "bool_carries"),
	[
		([_T_CHANGE], [_timed_review(_T_AFTER)], True),
		([_T_CHANGE], [_timed_review(_T_BEFORE)], False),
		([_T_CHANGE], [_timed_review(_T_CHANGE)], False),
		([_T_CHANGE, _T_LATER_CHANGE], [_timed_review(_T_MID)], False),
		([_T_LATER_CHANGE, _T_CHANGE], [_timed_review(_T_MID)], False),
		([_T_CHANGE, _T_LATER_CHANGE], [_timed_review(_T_AFTER)], True),
		(["not a time"], [_timed_review(_T_AFTER)], False),
		([_T_CHANGE], [_timed_review("")], False),
		([_T_CHANGE], [_timed_review(_T_BEFORE), _timed_review(_T_AFTER)], True),
		([_T_CHANGE], [_timed_review(_T_AFTER), _timed_review(_T_BEFORE)], True),
		(
			[_T_CHANGE],
			[_timed_review(_T_BEFORE), _timed_review(_T_AFTER, "someone-else")],
			False,
		),
		(
			[_T_CHANGE],
			[_timed_review(_T_BEFORE), _timed_review(_T_AFTER, str_state="DISMISSED")],
			False,
		),
	],
)
def test_find_missing_review_problem_carries_only_a_review_newer_than_the_base_change(
	monkeypatch: pytest.MonkeyPatch,
	list_change_times: list[str],
	list_reviews: list[dict],
	bool_carries: bool,
) -> None:
	"""A review carries across a merge-only update only if the latest base change predates it."""
	cls_gate = _load_gate()
	monkeypatch.setattr(cls_gate, "fetch_patch_fingerprint", lambda *_: "same patch")
	dict_pr = _retargeted_pr(list_change_times, list_reviews)
	str_problem = cls_gate.find_missing_review_problem(
		list_reviews,
		{"coderabbitai"},
		str_head_oid=_HEAD,
		fn_fingerprint=cls_gate._compare_fingerprint(dict_pr, "o/r", {"coderabbitai"}),
	)
	assert (str_problem is None) is bool_carries


def test_query_asks_for_the_creation_time_of_both_retarget_events() -> None:
	"""The carry-forward needs ``createdAt`` on the manual and the automatic event alike."""
	str_query = _load_gate()._QUERY
	assert "... on BaseRefChangedEvent { createdAt }" in str_query
	assert "... on AutomaticBaseChangeSucceededEvent { createdAt }" in str_query


def test_review_carried_forward_long_review_list_makes_at_most_cap_plus_one_calls() -> None:
	"""The head once, then at most the cap of reviewed commits, however many reviews exist."""
	cls_gate = _load_gate()
	fn_fingerprint = Mock(side_effect=lambda str_oid: str_oid)
	list_reviews = [_review("coderabbitai[bot]", f"{int_n:040d}") for int_n in range(40)]
	cls_gate.review_carried_forward(fn_fingerprint, list_reviews, {"coderabbitai"}, _HEAD)
	assert fn_fingerprint.call_count == cls_gate._INT_MAX_REVIEWED_COMMITS + 1


def test_review_carried_forward_tries_the_newest_reviewed_commit_first() -> None:
	"""Of two reviews with the head's patch, the more recent one is the one named."""
	cls_gate = _load_gate()
	list_reviews = [_review("coderabbitai[bot]", "a" * 40), _review("coderabbitai[bot]", "b" * 40)]
	str_carried = cls_gate.review_carried_forward(
		lambda str_oid: "same", list_reviews, {"coderabbitai"}, _HEAD
	)
	assert str_carried == "b" * 40


def test_review_carried_forward_computes_the_head_digest_once_without_a_cache() -> None:
	"""The once-only guarantee lives in the caller: a plain, uncached callable sees it once."""
	cls_gate = _load_gate()
	fn_counting = Mock(side_effect=lambda str_oid: str_oid)
	cls_gate.review_carried_forward(fn_counting, _three_reviews(), {"coderabbitai"}, _HEAD)
	assert fn_counting.call_args_list.count(call(_HEAD)) == 1


def test_compare_fingerprint_unknown_retarget_state_fails_closed() -> None:
	"""A PR node without the timeline events is "unknown", and unknown is not "not retargeted"."""
	cls_gate = _load_gate()
	fn_fingerprint = cls_gate._compare_fingerprint({"baseRefOid": "base"}, "o/r")
	with pytest.raises(ValueError, match="retarget state is unknown"):
		fn_fingerprint("a" * 40)


def test_query_reads_the_filtered_nodes_never_the_unfiltered_count() -> None:
	"""``totalCount`` ignores ``itemTypes`` (measured: 6 on a PR with no retarget)."""
	str_query = _load_gate()._QUERY
	assert "totalCount" not in str_query


def test_fetch_pull_request_keeps_timeline_items_across_pages(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Later pages extend the first node in place, so the retarget events survive pagination."""
	cls_gate = _load_gate()
	dict_first = _pr_page([_body_review("LGTM")], True)
	dict_first["timelineItems"] = {"nodes": [{"__typename": "BaseRefChangedEvent"}]}
	list_pages = [dict_first, _pr_page([_body_review("ok")], False)]
	monkeypatch.setattr(cls_gate, "_fetch_page", lambda *list_args: list_pages.pop(0))
	dict_pr = cls_gate.fetch_pull_request("o", "r", 1)
	assert dict_pr["timelineItems"]["nodes"]


def test_query_reads_both_retarget_event_types() -> None:
	"""Manual and automatic retargets both change the base the review was written against."""
	str_query = _load_gate()._QUERY
	assert "BASE_REF_CHANGED_EVENT" in str_query
	assert "AUTOMATIC_BASE_CHANGE_SUCCEEDED_EVENT" in str_query


@pytest.mark.parametrize(
	"json_body", ['{"files": ["x"]}', '{"files": {"a": 1}}', "not json", '{"files": [null]}']
)
def test_review_covers_head_malformed_files_body_fails_closed(
	monkeypatch: pytest.MonkeyPatch, json_body: str
) -> None:
	"""Malformed ``files`` (wrong container, non-dict entries, non-JSON) is "not covered"."""
	cls_gate = _load_gate()
	monkeypatch.setattr(
		cls_gate.subprocess, "run", Mock(return_value=Mock(returncode=0, stdout=json_body))
	)
	fn_fingerprint = functools.partial(cls_gate.fetch_patch_fingerprint, "o", "r", "base")
	assert cls_gate.review_covers_head(fn_fingerprint, "a" * 40, "b" * 40, "digest") is False


def test_patch_fingerprint_pure_renames_of_different_blobs_differ() -> None:
	"""A binary rename also reports ``changes == 0``, so the blob ``sha`` must be hashed."""
	cls_gate = _load_gate()
	dict_rename = {"filename": "b", "previous_filename": "a", "status": "renamed", "changes": 0}
	assert cls_gate.patch_fingerprint([{**dict_rename, "sha": "1"}]) != cls_gate.patch_fingerprint(
		[{**dict_rename, "sha": "2"}]
	)


def test_patch_fingerprint_pure_rename_with_same_blob_matches() -> None:
	"""The same rename of the same blob at two commits is the same fingerprint."""
	cls_gate = _load_gate()
	dict_rename = {
		"filename": "b",
		"previous_filename": "a",
		"status": "renamed",
		"changes": 0,
		"sha": "1",
	}
	assert cls_gate.patch_fingerprint([dict_rename]) == cls_gate.patch_fingerprint([dict_rename])


def test_patch_fingerprint_pure_rename_without_blob_sha_raises() -> None:
	"""No ``sha`` means nothing proves the content, so the entry is not trusted."""
	cls_gate = _load_gate()
	dict_rename = {"filename": "b", "previous_filename": "a", "status": "renamed", "changes": 0}
	with pytest.raises(ValueError, match="no patch text"):
		cls_gate.patch_fingerprint([dict_rename])


def test_patch_fingerprint_renamed_with_changes_but_no_patch_raises() -> None:
	"""A rename that also edits a file too large to show its patch is not a pure rename."""
	cls_gate = _load_gate()
	dict_big = {
		"filename": "b",
		"previous_filename": "a",
		"status": "renamed",
		"changes": 9,
		"sha": "1",
	}
	with pytest.raises(ValueError, match="no patch text"):
		cls_gate.patch_fingerprint([dict_big])


def test_find_missing_review_problem_returns_the_carried_commit_explicitly() -> None:
	"""The carrying commit is a return value, not an out-parameter."""
	cls_gate = _load_gate()
	tuple_result = cls_gate.check_missing_review(
		[_review("coderabbitai[bot]", "a" * 40)],
		{"coderabbitai"},
		str_head_oid=_HEAD,
		fn_fingerprint=lambda str_oid: "same",
	)
	assert tuple_result == (None, "a" * 40)


_INT_SHORTEST_JOB_MINUTES = 10
_PATH_WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/review_threads.yaml"


def test_pinned_job_minutes_do_not_exceed_any_workflow() -> None:
	"""A workflow shortened below the pinned cap fails here instead of timing out in CI.

	A missing workflow raises ``FileNotFoundError``, so the test cannot pass by finding none.
	"""
	list_minutes = [
		int(m) for m in re.findall(r"timeout-minutes:\s*(\d+)", _PATH_WORKFLOW.read_text("utf-8"))
	]
	assert min(list_minutes) >= _INT_SHORTEST_JOB_MINUTES


def test_carry_forward_worst_case_fits_half_the_shortest_job_timeout() -> None:
	"""Pusher lookup, head compare and one compare per reviewed commit, each at its timeout, fit.

	The retarget read is part of the GraphQL fetch and makes no call of its own. Half the job
	is left for checkout, setup and the GraphQL fetch.
	"""
	cls_gate = _load_gate()
	int_calls = 2 + cls_gate._INT_MAX_REVIEWED_COMMITS
	int_worst_s = int_calls * cls_gate._INT_COMPARE_TIMEOUT_S
	assert int_worst_s <= _INT_SHORTEST_JOB_MINUTES * 60 // 2


_BOT_EMAIL = "49699333+dependabot[bot]@users.noreply.github.com"


def _by_dependabot(str_oid: str) -> bool:
	"""Stand in for the actor lookup: Dependabot pushed."""
	return True


_WEB_FLOW_SIG = {"isValid": True, "wasSignedByGitHub": True}


def _dep_commit(
	str_type: str = "minor",
	str_email: str = _BOT_EMAIL,
	dict_signature: dict | None = _WEB_FLOW_SIG,
) -> dict:
	"""Build a commit node carrying Dependabot's ``update-type`` metadata."""
	str_update = f"update-type: version-update:semver-{str_type}"
	str_msg = f"Bump x\n\n---\nupdated-dependencies:\n- dependency-name: x\n  {str_update}\n..."
	return {
		"commit": {
			"message": str_msg,
			"author": {"email": str_email},
			"signature": dict_signature,
		}
	}


def _dep_pr(
	list_commits: list[dict], str_login: str = "dependabot", str_type: str = "Bot"
) -> dict:
	"""Build a ``pullRequest`` node for the exemption."""
	return {
		"author": {"login": str_login, "__typename": str_type},
		"allCommits": {"pageInfo": {"hasNextPage": False}, "nodes": list_commits},
	}


@pytest.mark.parametrize("str_update", ["patch", "minor"])
def test_dependabot_patch_and_minor_are_exempt(str_update: str) -> None:
	"""A pure patch or minor bump needs no review."""
	assert _load_gate().dependabot_review_exempt(
		_dep_pr([_dep_commit(str_update)]), _by_dependabot
	)


def test_dependabot_major_is_not_exempt() -> None:
	"""A major still needs a review."""
	assert not _load_gate().dependabot_review_exempt(
		_dep_pr([_dep_commit("major")]), _by_dependabot
	)


def test_dependabot_group_with_one_major_is_not_exempt() -> None:
	"""One major in a grouped PR makes the whole PR a major."""
	list_commits = [_dep_commit("minor"), _dep_commit("major")]
	assert not _load_gate().dependabot_review_exempt(_dep_pr(list_commits), _by_dependabot)


def test_non_dependabot_author_is_not_exempt() -> None:
	"""Only the Dependabot bot is exempt."""
	assert not _load_gate().dependabot_review_exempt(
		_dep_pr([_dep_commit()], "mallory", "User"), _by_dependabot
	)


def test_user_named_dependabot_is_not_exempt() -> None:
	"""The author must be a ``Bot`` actor, not a user."""
	assert not _load_gate().dependabot_review_exempt(
		_dep_pr([_dep_commit()], "dependabot", "User"), _by_dependabot
	)


def test_human_commit_on_a_dependabot_branch_is_not_exempt() -> None:
	"""A human push voids the exemption."""
	list_commits = [_dep_commit(), _dep_commit(str_email="human@example.com")]
	assert not _load_gate().dependabot_review_exempt(_dep_pr(list_commits), _by_dependabot)


def test_dependabot_without_update_metadata_is_not_exempt() -> None:
	"""No ``update-type`` in the commit means unknown, which is not exempt."""
	dict_commit = {"commit": {"message": "Bump x", "author": {"email": _BOT_EMAIL}}}
	assert not _load_gate().dependabot_review_exempt(_dep_pr([dict_commit]), _by_dependabot)


def test_dependabot_with_more_than_one_page_of_commits_is_not_exempt() -> None:
	"""A truncated commit list cannot prove every commit is Dependabot's."""
	dict_pr = _dep_pr([_dep_commit()])
	dict_pr["allCommits"]["pageInfo"]["hasNextPage"] = True
	assert not _load_gate().dependabot_review_exempt(dict_pr, _by_dependabot)


@pytest.mark.parametrize(
	"dict_signature",
	[
		None,
		{"isValid": False, "wasSignedByGitHub": True},
		{"isValid": True, "wasSignedByGitHub": False},
		{"isValid": True},
	],
)
def test_forged_dependabot_author_without_a_web_flow_signature_is_not_exempt(
	dict_signature: dict | None,
) -> None:
	"""A forgeable author email alone never proves the commit is Dependabot's."""
	dict_commit = _dep_commit(dict_signature=dict_signature)
	assert not _load_gate().dependabot_review_exempt(_dep_pr([dict_commit]), _by_dependabot)


def test_dependabot_group_with_an_entry_lacking_update_type_is_not_exempt() -> None:
	"""A dependency entry without ``update-type`` cannot hide behind the others."""
	dict_commit = _dep_commit()
	dict_commit["commit"]["message"] += "\n- dependency-name: y\n"
	assert not _load_gate().dependabot_review_exempt(_dep_pr([dict_commit]), _by_dependabot)


def test_dependabot_commit_pushed_by_a_human_is_not_exempt() -> None:
	"""A genuine-looking commit pushed by a human (actor lookup says no) gets no exemption."""
	dict_pr = _dep_pr([_dep_commit()])
	dict_pr["headRefOid"] = "abc"
	assert not _load_gate().dependabot_review_exempt(dict_pr, lambda str_oid: False)


def test_dependabot_exemption_without_an_actor_lookup_is_closed() -> None:
	"""No pusher check wired in means no exemption."""
	assert not _load_gate().dependabot_review_exempt(_dep_pr([_dep_commit()]))


def _runs_result(monkeypatch: pytest.MonkeyPatch, str_stdout: str, int_code: int = 0) -> None:
	"""Make ``gh api`` return the given output."""
	cls_done = subprocess.CompletedProcess([], int_code, stdout=str_stdout, stderr="")
	monkeypatch.setattr(subprocess, "run", lambda *a, **k: cls_done)


@pytest.mark.parametrize(
	("str_stdout", "int_code", "bool_want"),
	[
		('{"total_count":1,"workflow_runs":[{"actor":{"login":"dependabot[bot]"}}]}', 0, True),
		('{"total_count":1,"workflow_runs":[{"actor":{"login":"mallory"}}]}', 0, False),
		(
			'{"total_count":2,"workflow_runs":[{"actor":{"login":"dependabot[bot]"}},'
			'{"actor":{"login":"mallory"}}]}',
			0,
			False,
		),
		('{"total_count":0,"workflow_runs":[]}', 0, False),
		('{"total_count":150,"workflow_runs":[{"actor":{"login":"dependabot[bot]"}}]}', 0, False),
		("", 1, False),
		("[]", 0, False),
		("not json", 0, False),
	],
)
def test_dependabot_pushed_head_reads_the_run_actor_and_fails_closed(
	monkeypatch: pytest.MonkeyPatch, str_stdout: str, int_code: int, bool_want: bool
) -> None:
	"""Only a readable, complete run list started solely by Dependabot passes."""
	_runs_result(monkeypatch, str_stdout, int_code)
	assert _load_gate().dependabot_pushed_head("o/r", "abc") is bool_want


def test_dependabot_pushed_head_without_a_head_oid_is_closed() -> None:
	"""An empty head oid cannot be looked up."""
	assert not _load_gate().dependabot_pushed_head("o/r", "")


def test_dependabot_pushed_head_fails_closed_on_a_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A hung ``gh api`` call gives no exemption instead of hanging the gate."""
	cls_hang = Mock(side_effect=subprocess.TimeoutExpired("gh", 20))
	monkeypatch.setattr(subprocess, "run", cls_hang)
	assert not _load_gate().dependabot_pushed_head("o/r", "abc")


def _run_git(path_cwd: Path, dict_env: dict[str, str], *list_args: str) -> None:
	"""Run ``git`` with a fixed identity in ``path_cwd``, raising on failure."""
	list_ident = ["-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
	subprocess.run(  # noqa: S603
		["git", *list_ident, *list_args],  # noqa: S607
		cwd=path_cwd,
		env=dict_env,
		check=True,
		capture_output=True,
	)


def _base_checkout(tmp_path: Path) -> Path:
	"""Build a repo whose ``origin/main`` roster is the base and whose worktree roster differs.

	Returns
	-------
	Path
		The repo root; its working-tree roster additionally lists the PR author as a bot.
	"""
	path_git = tmp_path / ".git"
	dict_env = {
		**os.environ,
		"GIT_DIR": str(path_git),
		"GIT_WORK_TREE": str(tmp_path),
		"GIT_INDEX_FILE": str(path_git / "index"),
	}
	run = functools.partial(_run_git, tmp_path, dict_env)
	run("init", "-q", "-b", "main")
	path_roster = tmp_path / ".review-bots.yaml"
	path_roster.write_text(
		"reviewers:\n  - login: coderabbitai[bot]\n    posts: threads\n", encoding="utf-8"
	)
	run("add", ".review-bots.yaml")
	run("commit", "-q", "-m", "base")
	run("update-ref", "refs/remotes/origin/main", "HEAD")
	path_roster.write_text(
		"reviewers:\n  - login: coderabbitai[bot]\n    posts: threads\n"
		"  - login: mallory\n    posts: threads\n",
		encoding="utf-8",
	)
	return tmp_path


def test_policy_root_pr_edited_roster_cannot_add_its_author_as_a_bot(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""A PR that adds itself to ``.review-bots.yaml`` is still judged by the base roster."""
	cls_gate = _load_gate()
	path_repo = _base_checkout(tmp_path)
	monkeypatch.chdir(path_repo)
	monkeypatch.setenv("GITHUB_BASE_REF", "main")
	cls_gate.policy_root.cache_clear()
	assert set(cls_gate.load_roster(cls_gate.policy_root())) == {
		cls_gate.normalise_login("coderabbitai[bot]")
	}
	cls_gate.policy_root.cache_clear()


def test_policy_root_without_base_ref_reads_the_checkout(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Local and pre-commit runs (no ``GITHUB_BASE_REF``) keep reading the cwd."""
	cls_gate = _load_gate()
	monkeypatch.chdir(tmp_path)
	monkeypatch.delenv("GITHUB_BASE_REF", raising=False)
	cls_gate.policy_root.cache_clear()
	assert cls_gate.policy_root() == tmp_path
	cls_gate.policy_root.cache_clear()


def test_policy_root_unresolvable_base_fails_closed(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""A named but unresolvable base must raise, never fall back to the PR's roster."""
	cls_gate = _load_gate()
	monkeypatch.chdir(tmp_path)
	monkeypatch.setenv("GITHUB_BASE_REF", "nope")
	cls_gate.policy_root.cache_clear()
	with pytest.raises(RuntimeError):
		cls_gate.policy_root()
	cls_gate.policy_root.cache_clear()


def _load_integrity_dispatch() -> dict:
	"""Import ``check_gate_integrity.py`` and return its path-name dispatch table."""
	path_integrity = _find_gate_path().with_name("check_gate_integrity.py")
	cls_spec = importlib.util.spec_from_file_location("_check_gate_integrity", path_integrity)
	assert cls_spec is not None
	assert cls_spec.loader is not None
	cls_module = importlib.util.module_from_spec(cls_spec)
	cls_spec.loader.exec_module(cls_module)
	return cls_module._DICT_DISPATCH


@pytest.mark.parametrize(("str_new", "bool_flagged"), [("a: 2\n", True), ("a: 1\n", False)])
def test_gate_integrity_flags_a_changed_review_roster(str_new: str, bool_flagged: bool) -> None:
	"""A diff touching ``.review-bots.yaml`` is a finding; an identical file is not."""
	fn_check = _load_integrity_dispatch()[".review-bots.yaml"]
	assert bool(fn_check("a: 1\n", str_new, ".review-bots.yaml")) is bool_flagged
