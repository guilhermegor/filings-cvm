"""Unit tests for ``bin/check_portal_completeness.py`` — the portal-completeness detector.

Loaded by path (``bin/`` is not an importable package), the same way the other ``check_*`` tests
load their target. The pure logic (the gap, the issue body, the dedupe) carries the behaviour and
takes no network.
"""

import importlib.util
from pathlib import Path
import re


_PATH = Path(__file__).resolve().parents[2] / "bin" / "check_portal_completeness.py"
_SPEC = importlib.util.spec_from_file_location("check_portal_completeness", _PATH)
assert _SPEC is not None and _SPEC.loader is not None
cpc = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cpc)


# ---- missing_packages: the gap ----------------------------------------------------------------


def test_missing_is_published_minus_implemented_sorted() -> None:
	"""The gap is exactly ``published − implemented``, sorted."""
	published = frozenset({"b", "a", "c"})
	implemented = frozenset({"a"})

	assert cpc.missing_packages(published, implemented) == ["b", "c"]


def test_no_gap_when_everything_is_implemented() -> None:
	"""Nothing published beyond what we implement → empty gap."""
	published = frozenset({"a", "b"})

	assert cpc.missing_packages(published, frozenset({"a", "b", "c"})) == []


def test_an_implemented_package_no_longer_published_is_not_a_gap() -> None:
	"""A slug we implement that the portal dropped simply doesn't appear — never a false gap."""
	assert cpc.missing_packages(frozenset({"a"}), frozenset({"a", "gone"})) == []


# ---- issue body --------------------------------------------------------------------------------


def test_body_carries_the_marker_and_counts() -> None:
	"""The body carries the dedupe marker and both counts (published, implemented, missing)."""
	str_body = cpc.build_issue_body(["x", "y"], int_published=10)

	assert cpc._ISSUE_MARKER in str_body
	assert "**10**" in str_body  # published
	assert "**8**" in str_body  # implemented = 10 - 2
	assert "**2**" in str_body  # missing
	assert "`x`" in str_body


# ---- issue dedupe ------------------------------------------------------------------------------


def test_find_open_tracking_issue_matches_the_marker() -> None:
	"""The tracking issue is recognised by its hidden body marker."""
	list_issues = [
		{"number": 1, "body": "unrelated"},
		{"number": 2, "body": f"{cpc._ISSUE_MARKER}\nstuff"},
	]

	assert cpc.find_open_tracking_issue(list_issues) == 2


def test_find_open_tracking_issue_returns_none_without_the_marker() -> None:
	"""No marker anywhere → nothing to update (a fresh issue will be opened)."""
	assert cpc.find_open_tracking_issue([{"number": 1, "body": "x"}]) is None


# ---- structural: the declared implemented-set is well-formed ----------------------------------

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:[_-][a-z0-9]+)*$")


def test_every_implemented_slug_is_a_well_formed_ckan_slug() -> None:
	"""Each declared slug is lowercase CKAN form (a typo like an uppercase root is caught here)."""
	for str_slug in cpc._IMPLEMENTED_PACKAGES:
		assert _SLUG_RE.match(str_slug), str_slug


def test_implemented_set_is_non_empty_and_deduped() -> None:
	"""A frozenset can't hold duplicates; assert it's populated so the gap isn't the portal."""
	assert len(cpc._IMPLEMENTED_PACKAGES) >= 20
