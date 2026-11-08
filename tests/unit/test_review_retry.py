"""Unit tests for the rate-limited-review retry (``bin/retry_rate_limited_review.py``).

The whole design rests on one measurement, so the tests are organised around what that
measurement licenses and what it forbids:

- Licensed: re-ASKING when the reviewer said it was rate limited. Measured upstream over 112
  PRs — 19 hit a rate limit and 18 were reviewed in the end, so the state is a delay.
- Forbidden: letting any of this influence a VERDICT. blueprintx#259 established that a
  reviewer notice's text cannot decide whether a PR was reviewed, because the "already
  reviewed" footnote is appended to every outcome. The rate-limit phrase does discriminate
  (0/25 performed, 0/3 failed, 57/59 not-completed), but this module still only ever asks for a
  review — never passes one.

So the load-bearing test here is the negative one: a PR with **no review at all and no notice**
must not be re-asked into looking healthy, and one whose reviewer merely *reviewed older code*
is not a rate-limit case either.
"""

from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock

import pytest


def _load_retry() -> ModuleType:
	"""Import ``bin/retry_rate_limited_review.py`` as a module.

	Returns
	-------
	ModuleType
		The loaded retry module.
	"""
	path_mod = Path(__file__).resolve().parents[2] / "bin" / "retry_rate_limited_review.py"
	cls_spec = importlib.util.spec_from_file_location("_retry_rate_limited_review", path_mod)
	assert cls_spec is not None
	assert cls_spec.loader is not None
	cls_module = importlib.util.module_from_spec(cls_spec)
	cls_spec.loader.exec_module(cls_module)
	return cls_module


def _find_gate_path() -> Path:
	"""Locate ``check_review_threads.py``, whether run from the template tree or a scaffold.

	The gate's single source is ``templates/common/bin/`` (blueprintx#175 follow-up), a
	SIBLING of ``templates/python-common/`` where this test file lives — but every scaffold
	copies it into the generated project's own flat ``bin/``, alongside
	``retry_rate_limited_review.py``. Both layouts have to resolve from the same test source;
	mirrors the identically-named helper in ``test_review_threads_gate.py``.

	Returns
	-------
	Path
		Whichever candidate exists. ⚠️ No branch here on purpose — ``tests/`` is capped at
		cyclomatic complexity 1; an ``if``/``raise`` pair would violate that ceiling for a
		path lookup that is not itself a test. Defaulting to the template-tree candidate
		when neither exists lets a genuinely missing gate fail naturally in the loader
		below, which already reports an absent file clearly.
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


_DT_NOW = datetime(2026, 8, 24, 23, 55, 0, tzinfo=timezone.utc)


def _comment(str_login: str, str_body: str, int_min_ago: int = 0, str_type: str = "Bot") -> dict:
	"""Build one normalised issue comment.

	Parameters
	----------
	str_login : str
		The comment author's login.
	str_body : str
		The comment body.
	int_min_ago : int
		How many minutes before ``_DT_NOW`` it was posted.
	str_type : str
		The author's account type as REST reports it.

	Returns
	-------
	dict
		A comment with ``login``, ``type``, ``body`` and ``created_at``.
	"""
	dt_at = _DT_NOW - timedelta(minutes=int_min_ago)
	return {
		"login": str_login,
		"type": str_type,
		"body": str_body,
		"created_at": dt_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
	}


def _pr(list_comments: list, list_reviews: list, str_head: str = "cafe123") -> dict:
	"""Build a ``pullRequest`` node with the fields the retry predicate reads.

	Parameters
	----------
	list_comments : list
		Accepted for call-site symmetry; comments are passed to the predicate separately.
	list_reviews : list
		Submitted-review nodes.
	str_head : str
		The head commit oid.

	Returns
	-------
	dict
		A pull-request node.
	"""
	return {"headRefOid": str_head, "reviews": {"nodes": list_reviews}}


_STR_RATE_LIMITED = (
	"⚠️ Action not completed\n\nReview rate limited. Please wait before your next review "
	"request. Note: CodeRabbit is an incremental review system and does not re-review "
	"already reviewed commits."
)
_STR_PERFORMED = (
	"✅ Action performed\n\nReview triggered. Note: CodeRabbit is an incremental review system "
	"and does not re-review already reviewed commits."
)


@pytest.fixture
def cls_retry() -> ModuleType:
	"""Provide the loaded retry module.

	Returns
	-------
	ModuleType
		The retry module.
	"""
	return _load_retry()


@pytest.fixture
def cls_gate() -> ModuleType:
	"""Provide the loaded review gate, whose helpers the retry module reuses.

	Returns
	-------
	ModuleType
		The gate module.
	"""
	path_gate = _find_gate_path()
	cls_spec = importlib.util.spec_from_file_location("_gate_for_retry", path_gate)
	assert cls_spec is not None
	assert cls_spec.loader is not None
	cls_module = importlib.util.module_from_spec(cls_spec)
	cls_spec.loader.exec_module(cls_module)
	return cls_module


def test_a_rate_limited_pr_with_no_review_is_re_asked(
	cls_retry: ModuleType, cls_gate: ModuleType
) -> None:
	"""The case the file exists for: reviewer throttled, nothing reviewed, so ask again.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	cls_gate : types.ModuleType
		The gate module.
	"""
	list_comments = [_comment("coderabbitai", _STR_RATE_LIMITED)]
	dict_pr = _pr(list_comments, [])

	assert (
		cls_retry.pr_needs_retry(
			dict_pr, list_comments, {"coderabbitai"}, cls_gate, "guilhermegor", _DT_NOW
		)
		is True
	)


def test_a_reviewed_head_is_never_re_asked(cls_retry: ModuleType, cls_gate: ModuleType) -> None:
	"""A review on the head commit ends the matter, whatever the notices say.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	cls_gate : types.ModuleType
		The gate module.
	"""
	list_comments = [_comment("coderabbitai", _STR_RATE_LIMITED)]
	dict_pr = _pr(
		list_comments, [{"author": {"login": "coderabbitai"}, "commit": {"oid": "cafe123"}}]
	)

	assert (
		cls_retry.pr_needs_retry(
			dict_pr, list_comments, {"coderabbitai"}, cls_gate, "guilhermegor", _DT_NOW
		)
		is False
	)


def test_a_pr_with_no_notice_at_all_is_not_re_asked(
	cls_retry: ModuleType, cls_gate: ModuleType
) -> None:
	"""Zero reviews and SILENCE is not a rate limit — the load-bearing negative.

	This is the #259 boundary. A PR nobody has looked at and nobody has commented on is the
	state the gate must keep blocking; re-asking is harmless but claiming a cause we cannot
	see is how a text matcher turns into a verdict. The predicate must read silence as
	"not my case", not as "probably throttled".

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	cls_gate : types.ModuleType
		The gate module.
	"""
	list_comments = []
	dict_pr = _pr(list_comments, [])

	assert (
		cls_retry.pr_needs_retry(
			dict_pr, list_comments, {"coderabbitai"}, cls_gate, "guilhermegor", _DT_NOW
		)
		is False
	)


def test_a_successful_trigger_notice_is_not_a_rate_limit(
	cls_retry: ModuleType, cls_gate: ModuleType
) -> None:
	"""``Action performed`` must not be read as throttled, though it shares the footnote.

	Both notices end with the same "does not re-review already reviewed commits" sentence —
	the footnote #259 proved worthless as a signal. Only the rate-limit wording may fire, so
	this test pins the discrimination the measurement claims.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	cls_gate : types.ModuleType
		The gate module.
	"""
	list_comments = [_comment("coderabbitai", _STR_PERFORMED)]
	dict_pr = _pr(list_comments, [])

	assert (
		cls_retry.pr_needs_retry(
			dict_pr, list_comments, {"coderabbitai"}, cls_gate, "guilhermegor", _DT_NOW
		)
		is False
	)


def test_only_the_newest_notice_decides(cls_retry: ModuleType, cls_gate: ModuleType) -> None:
	"""A rate limit the reviewer has since superseded must not trigger a re-ask.

	Same rule the gate already applies to its quoted notice: an older sentence describes a
	state that no longer holds. Comments arrive oldest-first, so the scan runs backwards.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	cls_gate : types.ModuleType
		The gate module.
	"""
	list_comments = [
		_comment("coderabbitai", _STR_RATE_LIMITED),
		_comment("coderabbitai", _STR_PERFORMED),
	]
	dict_pr = _pr(list_comments, [])

	assert (
		cls_retry.pr_needs_retry(
			dict_pr, list_comments, {"coderabbitai"}, cls_gate, "guilhermegor", _DT_NOW
		)
		is False
	)


def test_the_marker_makes_a_scheduled_run_ask_once_per_window(
	cls_retry: ModuleType, cls_gate: ModuleType
) -> None:
	"""Our own recent request stops the next tick asking again.

	Without this the workflow would comment every 10 minutes for the whole window. The check is
	the marker's AGE, not its position: ``_comment`` defaults to ``int_min_ago=0``, so the
	marker here sits inside the 30-minute cooldown. Position was the first implementation and
	it shipped a loop — see the block above ``asked_recently`` and the acknowledgement test
	below.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	cls_gate : types.ModuleType
		The gate module.
	"""
	list_comments = [
		_comment("coderabbitai", _STR_RATE_LIMITED),
		_comment("guilhermegor", cls_retry._STR_REQUEST),
	]
	dict_pr = _pr(list_comments, [])

	assert (
		cls_retry.pr_needs_retry(
			dict_pr, list_comments, {"coderabbitai"}, cls_gate, "guilhermegor", _DT_NOW
		)
		is False
	)


def test_the_reviewers_own_acknowledgement_does_not_trigger_another_ask(
	cls_retry: ModuleType, cls_gate: ModuleType
) -> None:
	"""🔴 The loop this file shipped once: the ack to our request is NOT a new window.

	Measured live on blueprintx#270 — the reviewer acknowledges a request within ~13 seconds,
	and that acknowledgement is a roster comment NEWER than our marker, carrying the
	rate-limit wording. The first implementation asked "is our marker newer than the newest
	roster notice?", so it met the ack, concluded "not asked yet", and asked again every tick,
	for ever.

	⚠️ The test this one replaced asserted the DEFECT — it was written from the same mental
	model as the code, so it agreed with it rather than checking it. A cooldown cannot be
	fooled this way: we asked recently or we did not.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	cls_gate : types.ModuleType
		The gate module.
	"""
	list_comments = [
		_comment("coderabbitai", _STR_RATE_LIMITED, int_min_ago=6),
		_comment("guilhermegor", cls_retry._STR_REQUEST, int_min_ago=5),
		_comment("coderabbitai", _STR_RATE_LIMITED, int_min_ago=4),
	]
	dict_pr = _pr(list_comments, [])

	assert (
		cls_retry.pr_needs_retry(
			dict_pr, list_comments, {"coderabbitai"}, cls_gate, "guilhermegor", _DT_NOW
		)
		is False
	)


def test_the_cooldown_expires_so_a_stuck_pr_is_asked_again(
	cls_retry: ModuleType, cls_gate: ModuleType
) -> None:
	"""The other half: once the window has genuinely passed, ask again.

	Without this the cooldown would be a permanent silence after one request — the failure
	mode the marker-authorship guard exists to prevent, reintroduced by its replacement.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	cls_gate : types.ModuleType
		The gate module.
	"""
	list_comments = [
		_comment("guilhermegor", cls_retry._STR_REQUEST, int_min_ago=45),
		_comment("coderabbitai", _STR_RATE_LIMITED, int_min_ago=44),
	]
	dict_pr = _pr(list_comments, [])

	assert (
		cls_retry.pr_needs_retry(
			dict_pr, list_comments, {"coderabbitai"}, cls_gate, "guilhermegor", _DT_NOW
		)
		is True
	)


def test_a_review_on_older_code_is_not_a_rate_limit_case(
	cls_retry: ModuleType, cls_gate: ModuleType
) -> None:
	"""A review pinned to a superseded commit, with no throttle notice, is left alone.

	The gate reports this state with its own distinct message (#208), and it calls for a
	different action. Re-asking on it would be harmless, but treating "reviewed older code"
	as "throttled" would blur two states the gate deliberately separated.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	cls_gate : types.ModuleType
		The gate module.
	"""
	list_comments = [_comment("coderabbitai", _STR_PERFORMED)]
	dict_pr = _pr(
		list_comments, [{"author": {"login": "coderabbitai"}, "commit": {"oid": "0ldc0de"}}]
	)

	assert (
		cls_retry.pr_needs_retry(
			dict_pr, list_comments, {"coderabbitai"}, cls_gate, "guilhermegor", _DT_NOW
		)
		is False
	)


def test_the_request_names_a_full_review_not_a_plain_one(cls_retry: ModuleType) -> None:
	"""The posted command must be the FULL form, which ignores what was already reviewed.

	Pinned to the exact command a user could type, never a noun phrase: the module's own
	docstring contains the words "full review" in prose, and an assertion satisfied by that
	prose would pass while the command was downgraded — the over-available-needle trap
	measured in blueprintx#264.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	"""
	assert "@coderabbitai full review" in cls_retry._STR_REQUEST


def test_the_request_carries_the_idempotence_marker(cls_retry: ModuleType) -> None:
	"""The posted body must contain the marker, or every tick re-asks.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	"""
	assert cls_retry._STR_MARKER in cls_retry._STR_REQUEST


def test_a_marker_from_another_author_does_not_suppress_the_retry(
	cls_retry: ModuleType, cls_gate: ModuleType
) -> None:
	"""🔴 The security case: anyone who can comment can post the marker text.

	A marker is an HTML comment in a comment body, so it is not a capability — it is a string
	any PR commenter can type. Trusting the text alone let a single comment silence the retry
	for that PR permanently: the newest-first scan stops at the marker before it ever reaches
	the reviewer's notice, and nothing says so. Only a marker authored by the identity the
	retry posts as may count.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	cls_gate : types.ModuleType
		The gate module.
	"""
	list_comments = [
		_comment("coderabbitai", _STR_RATE_LIMITED),
		_comment("a-passer-by", cls_retry._STR_REQUEST),
	]
	dict_pr = _pr(list_comments, [])

	assert (
		cls_retry.pr_needs_retry(
			dict_pr, list_comments, {"coderabbitai"}, cls_gate, "guilhermegor", _DT_NOW
		)
		is True
	)


def test_an_unresolvable_identity_trusts_no_marker(
	cls_retry: ModuleType, cls_gate: ModuleType
) -> None:
	"""With no known self-login, even our own marker is ignored — ask twice, never fall silent.

	The failure direction is the point. Trusting every marker when the identity is unknown
	restores the hole above; trusting none costs a duplicate request. Noise is recoverable,
	silence is not.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	cls_gate : types.ModuleType
		The gate module.
	"""
	list_comments = [
		_comment("coderabbitai", _STR_RATE_LIMITED),
		_comment("guilhermegor", cls_retry._STR_REQUEST),
	]
	dict_pr = _pr(list_comments, [])

	assert (
		cls_retry.pr_needs_retry(dict_pr, list_comments, {"coderabbitai"}, cls_gate, "", _DT_NOW)
		is True
	)


def test_every_page_of_open_prs_is_examined(cls_retry: ModuleType) -> None:
	"""A rate-limited PR on page two must be reachable, not silently dropped.

	``--paginate --slurp`` returns a list of PAGES, so the flattening is one level deeper than
	it looks. The obvious one-level comprehension iterates pages and yields nothing, and a
	janitor that examines nothing reports "checked 0" rather than failing — a silent partial
	pass, which is the failure this family of scripts exists to prevent.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	"""
	list_pages = [
		[{"number": 1, "created_at": "2026-08-24T10:00:00Z"}],
		[{"number": 2, "created_at": "2026-08-24T09:00:00Z"}],
	]

	assert [dict_pr["number"] for dict_pr in cls_retry.flatten_open_prs(list_pages)] == [2, 1]


def test_a_malformed_page_cannot_crash_the_sweep(cls_retry: ModuleType) -> None:
	"""A page that is not a list, or an entry without a number, is skipped rather than fatal.

	This runs unattended every ten minutes, so one odd payload must not stop the PRs behind it
	from being examined.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	"""
	list_pages = [[{"number": 1}], "not-a-page", [{"no_number": True}, {"number": 4}]]

	assert [dict_pr["number"] for dict_pr in cls_retry.flatten_open_prs(list_pages)] == [1, 4]


def test_flatten_open_prs_sorts_oldest_created_at_first(cls_retry: ModuleType) -> None:
	"""``created_at`` is the FIFO ordering key (blueprintx#280) — sorted here, not left implicit.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	"""
	list_pages = [
		[
			{"number": 9, "created_at": "2026-08-26T00:00:00Z"},
			{"number": 3, "created_at": "2026-08-20T00:00:00Z"},
		]
	]

	assert [dict_pr["number"] for dict_pr in cls_retry.flatten_open_prs(list_pages)] == [3, 9]


def test_an_author_less_marker_cannot_match_an_unknown_identity(
	cls_retry: ModuleType, cls_gate: ModuleType
) -> None:
	"""An empty author must not equal an empty self-login — found by a SURVIVING mutant.

	Deleting the ``if not str_self`` guard changed nothing red, which is a gap report rather
	than proof the guard is redundant. Probing it showed the guard is load-bearing in exactly
	one shape: when our identity is unknown (``""``) and a comment carries an empty author
	(``""``), the author comparison MATCHES and an author-less marker suppresses the retry —
	the silent failure this file has now hit twice, in a third disguise.

	Two empty strings comparing equal is the kind of accident no reading catches and every
	mutation does, provided the suite contains the shape.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	cls_gate : types.ModuleType
		The gate module.
	"""
	list_comments = [
		_comment("coderabbitai", _STR_RATE_LIMITED, int_min_ago=6),
		_comment("", cls_retry._STR_REQUEST, int_min_ago=1),
	]
	dict_pr = _pr(list_comments, [])

	assert (
		cls_retry.pr_needs_retry(dict_pr, list_comments, {"coderabbitai"}, cls_gate, "", _DT_NOW)
		is True
	)


def test_one_unreadable_pr_does_not_end_the_sweep(
	cls_retry: ModuleType, cls_gate: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""A PR whose fetch raises is skipped with a warning; the sweep continues.

	``fetch_pull_request`` raises on an API failure and indexes a node that can be null, so a
	single deleted, transferred or transiently-failing PR would abort the loop and leave every
	PR behind it unexamined — silently, because the run would simply end. This job runs
	unattended every ten minutes, so it must degrade per PR, never per sweep.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	cls_gate : types.ModuleType
		The gate module.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to make the fetch raise.
	"""
	monkeypatch.setattr(
		cls_gate,
		"fetch_pull_request",
		Mock(side_effect=RuntimeError("GraphQL query failed: boom")),
	)

	assert (
		cls_retry.build_candidate(
			"acme/widget", 7, "2026-08-24T00:00:00Z", {"coderabbitai"}, cls_gate
		)
		is None
	)


_STR_RATE_LIMITED_35 = (
	"⚠️ Action not completed\n\nReview rate limited.\n\nYour included review limit is currently "
	"reached under our Fair Usage Limits Policy. This review may still proceed through "
	"usage-based billing if eligible. Your next included review will be available in 35 minutes."
)


def test_the_declared_wait_is_read_from_the_reviewers_own_words(cls_retry: ModuleType) -> None:
	"""The number in the refusal is the number used — not a local constant.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	"""
	assert cls_retry.parse_declared_wait(_STR_RATE_LIMITED_35) == 35


def test_a_refusal_that_declares_no_wait_yields_no_number(cls_retry: ModuleType) -> None:
	"""No declared number means no opinion, so the marker cooldown decides alone.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	"""
	assert cls_retry.parse_declared_wait(_STR_RATE_LIMITED) is None


def test_a_pr_inside_the_declared_window_is_not_re_asked(
	cls_retry: ModuleType, cls_gate: ModuleType
) -> None:
	"""⚠️ The defect this issue exists for: asking inside the window burns a request.

	A refused request is not free — it still counts as traffic and pushes the window further
	out, so a too-early retry makes the very wait it is impatient about longer. Measured three
	times on this repo (31, 34 and 35 minutes) against a constant of 30, which is below all of
	them: the guess was wrong in the one direction that costs something.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	cls_gate : types.ModuleType
		The gate module.
	"""
	list_comments = [_comment("coderabbitai", _STR_RATE_LIMITED_35, int_min_ago=20)]
	dict_pr = _pr(list_comments, [])

	assert (
		cls_retry.pr_needs_retry(
			dict_pr, list_comments, {"coderabbitai"}, cls_gate, "guilhermegor", _DT_NOW
		)
		is False
	)


def test_a_pr_past_the_declared_window_is_re_asked(
	cls_retry: ModuleType, cls_gate: ModuleType
) -> None:
	"""The other half of the pair: once the declared wait elapses, the retry fires.

	Without this, a gate that simply never asks would satisfy the test above — the two together
	are what pin the behaviour to the declared number rather than to silence.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	cls_gate : types.ModuleType
		The gate module.
	"""
	list_comments = [_comment("coderabbitai", _STR_RATE_LIMITED_35, int_min_ago=36)]
	dict_pr = _pr(list_comments, [])

	assert (
		cls_retry.pr_needs_retry(
			dict_pr, list_comments, {"coderabbitai"}, cls_gate, "guilhermegor", _DT_NOW
		)
		is True
	)


def test_an_old_marker_does_not_override_a_refusal_inside_the_declared_window(
	cls_retry: ModuleType, cls_gate: ModuleType
) -> None:
	"""Our marker is past the cooldown, but the reviewer's 35-minute wait is still open.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	cls_gate : types.ModuleType
		The gate module.
	"""
	list_comments = [
		_comment("guilhermegor", cls_retry._STR_REQUEST, int_min_ago=45),
		_comment("coderabbitai", _STR_RATE_LIMITED_35, int_min_ago=20),
	]
	dict_pr = _pr(list_comments, [])

	assert (
		cls_retry.pr_needs_retry(
			dict_pr, list_comments, {"coderabbitai"}, cls_gate, "guilhermegor", _DT_NOW
		)
		is False
	)


def test_the_declared_window_is_measured_from_the_notice_not_from_our_marker(
	cls_retry: ModuleType,
) -> None:
	"""⚠️ The clock starts when the REVIEWER spoke, never when we last asked.

	Anchoring on our own request would restart the window every time we asked — the same
	self-referential mistake the ordering-vs-cooldown block documents one layer up, where a
	predicate read our own traffic as evidence about someone else's state.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	"""
	dict_notice = _comment("coderabbitai", _STR_RATE_LIMITED_35, int_min_ago=36)

	assert cls_retry.declared_wait_still_open(dict_notice, _DT_NOW) is False


def test_a_declared_wait_with_an_unreadable_timestamp_defers_to_the_cooldown(
	cls_retry: ModuleType,
) -> None:
	"""An undateable refusal must not stall the retry for ever.

	Returning ``True`` on a timestamp we cannot parse would suppress every future request on
	one malformed field — a permanent silence produced by a formatting accident.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	"""
	dict_notice = {
		"login": "coderabbitai",
		"body": _STR_RATE_LIMITED_35,
		"created_at": "not-a-date",
	}

	assert cls_retry.declared_wait_still_open(dict_notice, _DT_NOW) is False


def test_an_oversized_declared_wait_is_rejected_instead_of_crashing(
	cls_retry: ModuleType,
) -> None:
	"""⚠️ The number comes from an EXTERNAL service, so it is untrusted input.

	The digit pattern is unbounded and ``timedelta(minutes=10**100)`` raises
	``OverflowError``. The only caller sits outside ``build_candidate``'s try/except — which
	wraps just the fetch — so one absurd
	value would abort the entire unattended sweep and leave every later PR unexamined. That is
	the per-PR degradation rule this module already states for a deleted or transferred PR,
	reached through the parser instead of the network.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	"""
	str_absurd = f"Your next included review will be available in {'9' * 5000} minutes."

	assert cls_retry.parse_declared_wait(str_absurd) is None


def test_a_representable_but_oversized_wait_is_also_rejected(cls_retry: ModuleType) -> None:
	"""The OTHER limit: converts fine, but ``timedelta`` cannot hold it.

	Two different exceptions guard this path at different depths — ``ValueError`` during the
	conversion, ``OverflowError`` during the ``timedelta``. One test each, because a single
	fixture cannot reach both and a guard covering only one reads as covering both.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	"""
	str_absurd = f"Your next included review will be available in {'9' * 100} minutes."

	assert cls_retry.parse_declared_wait(str_absurd) is None


def _candidate(int_number: int, str_created_at: str, list_comments: list, dict_pr: dict) -> dict:
	"""Build one ``build_candidate``-shaped record for the selection tests.

	Parameters
	----------
	int_number : int
		The PR number.
	str_created_at : str
		The PR's ``created_at``.
	list_comments : list
		Normalised comments for this PR.
	dict_pr : dict
		The ``pullRequest`` node (``headRefOid``/``reviews``).

	Returns
	-------
	dict
		A record shaped like :func:`build_candidate`'s return value.
	"""
	return {
		"number": int_number,
		"created_at": str_created_at,
		"pr": dict_pr,
		"comments": list_comments,
		"notice": list_comments[-1] if list_comments else None,
	}


def test_account_blocked_until_reads_the_newest_refusal_across_all_waiting_prs(
	cls_retry: ModuleType,
) -> None:
	"""⚠️ The core fix: one PR's declared wait binds every other PR too (shared account quota).

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	"""
	list_notices = [
		_comment("coderabbitai", _STR_RATE_LIMITED_35, int_min_ago=20),
		_comment("coderabbitai", _STR_RATE_LIMITED_35, int_min_ago=5),
	]

	assert cls_retry.account_blocked_until(list_notices, _DT_NOW) == _DT_NOW + timedelta(
		minutes=30
	)


def test_account_blocked_until_takes_the_LATEST_deadline_not_the_latest_notice(
	cls_retry: ModuleType,
) -> None:
	"""A newer refusal naming NO number must not erase an older PR's open window.

	⚠️ The regression this pins: ``_RE_RATE_LIMIT`` matches refusals with no number too, so
	``notice_deadline`` returns ``None`` for them. Picking ``max(created_at)`` and reading only
	that notice therefore reported "account free" while another PR's declared window was still
	open, and the run asked inside it -- pushing the window further out.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	"""
	list_notices = [
		_comment("coderabbitai", _STR_RATE_LIMITED_35, int_min_ago=20),
		_comment("coderabbitai", _STR_RATE_LIMITED, int_min_ago=5),
	]

	assert cls_retry.account_blocked_until(list_notices, _DT_NOW) is not None


def test_account_blocked_until_is_free_once_the_newest_refusal_elapses(
	cls_retry: ModuleType,
) -> None:
	"""The other half: once the newest declared window has passed, nothing blocks.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	"""
	list_notices = [_comment("coderabbitai", _STR_RATE_LIMITED_35, int_min_ago=36)]

	assert cls_retry.account_blocked_until(list_notices, _DT_NOW) is None


def test_select_pr_for_retry_picks_the_oldest_of_several_waiting_prs(
	cls_retry: ModuleType, cls_gate: ModuleType
) -> None:
	"""The should-fail witness's core claim: exactly ONE PR, and it is the oldest waiting one.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	cls_gate : types.ModuleType
		The gate module.
	"""
	list_comments = [_comment("coderabbitai", _STR_RATE_LIMITED)]
	dict_pr = _pr(list_comments, [])
	list_candidates = [
		_candidate(20, "2026-08-25T00:00:00Z", list_comments, dict_pr),
		_candidate(11, "2026-08-20T00:00:00Z", list_comments, dict_pr),
	]

	assert (
		cls_retry.select_pr_for_retry(
			list_candidates, {"coderabbitai"}, cls_gate, "guilhermegor", _DT_NOW
		)
		== 11
	)


def test_select_pr_for_retry_picks_none_while_the_only_candidate_is_cooling_down(
	cls_retry: ModuleType, cls_gate: ModuleType
) -> None:
	"""A second invocation while our own ask is outstanding must pick nobody.

	``pr_needs_retry`` already refuses a PR we asked within the cooldown; this pins that the
	selector propagates ``None`` rather than falling through to a different candidate.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	cls_gate : types.ModuleType
		The gate module.
	"""
	list_comments = [
		_comment("coderabbitai", _STR_RATE_LIMITED),
		_comment("guilhermegor", cls_retry._STR_REQUEST),
	]
	dict_pr = _pr(list_comments, [])
	list_candidates = [_candidate(11, "2026-08-20T00:00:00Z", list_comments, dict_pr)]

	assert (
		cls_retry.select_pr_for_retry(
			list_candidates, {"coderabbitai"}, cls_gate, "guilhermegor", _DT_NOW
		)
		is None
	)


def test_select_pr_for_retry_skips_a_pr_past_the_attempt_cap(
	cls_retry: ModuleType, cls_gate: ModuleType
) -> None:
	"""A permanently-stuck oldest PR must not starve every younger PR forever (design Q2).

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	cls_gate : types.ModuleType
		The gate module.
	"""
	list_comments_stuck = [
		_comment("guilhermegor", cls_retry._STR_REQUEST, int_min_ago=250),
		_comment("guilhermegor", cls_retry._STR_REQUEST, int_min_ago=200),
		_comment("guilhermegor", cls_retry._STR_REQUEST, int_min_ago=150),
		_comment("guilhermegor", cls_retry._STR_REQUEST, int_min_ago=100),
		_comment("guilhermegor", cls_retry._STR_REQUEST, int_min_ago=60),
		_comment("coderabbitai", _STR_RATE_LIMITED, int_min_ago=50),
	]
	dict_pr_stuck = _pr(list_comments_stuck, [])
	list_comments_next = [_comment("coderabbitai", _STR_RATE_LIMITED, int_min_ago=50)]
	dict_pr_next = _pr(list_comments_next, [])
	list_candidates = [
		_candidate(11, "2026-08-20T00:00:00Z", list_comments_stuck, dict_pr_stuck),
		_candidate(22, "2026-08-21T00:00:00Z", list_comments_next, dict_pr_next),
	]

	assert (
		cls_retry.select_pr_for_retry(
			list_candidates,
			{"coderabbitai"},
			cls_gate,
			"guilhermegor",
			_DT_NOW,
			int_max_attempts=5,
		)
		== 22
	)


def test_count_self_asks_counts_only_our_own_marker(
	cls_retry: ModuleType, cls_gate: ModuleType
) -> None:
	"""The attempt cap must count OUR asks, not a passer-by's copy of the marker text.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	cls_gate : types.ModuleType
		The gate module.
	"""
	list_comments = [
		_comment("guilhermegor", cls_retry._STR_REQUEST),
		_comment("a-passer-by", cls_retry._STR_REQUEST),
	]

	assert cls_retry.count_self_asks(list_comments, "guilhermegor", cls_gate.normalise_login) == 1


def test_newest_roster_comment_ignores_a_user_typed_borrower(cls_retry: ModuleType) -> None:
	"""A User named like the roster App is not the reviewer speaking.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	"""
	list_comments = [_comment("coderabbitai", _STR_RATE_LIMITED, str_type="User")]
	assert cls_retry.newest_roster_comment(list_comments, {"coderabbitai"}, str) is None


def test_build_candidate_passes_the_roster_to_the_fetch(
	cls_retry: ModuleType, cls_gate: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""The retry reads the PR through the gate's roster-aware fetch, so no caller skips it.

	Parameters
	----------
	cls_retry : types.ModuleType
		The retry module.
	cls_gate : types.ModuleType
		The gate module.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to record the fetch call.
	"""
	cls_fetch = Mock(side_effect=RuntimeError("stop"))
	monkeypatch.setattr(cls_gate, "fetch_pull_request", cls_fetch)
	cls_retry.build_candidate("acme/widget", 7, "2026-08-24T00:00:00Z", {"coderabbitai"}, cls_gate)
	assert cls_fetch.call_args.args[3] == frozenset({"coderabbitai"})
