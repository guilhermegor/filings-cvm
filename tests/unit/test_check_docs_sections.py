"""Unit tests for ``bin/check_docs_sections.py`` — the docs-structure gate.

Loaded by path (``bin/`` is not an importable package). Synthetic docs trees prove the gate
fails on a bad page (no placebo); one test runs it against the real repo docs.
"""

import importlib.util
from pathlib import Path

import pytest


_ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location("cds", _ROOT / "bin" / "check_docs_sections.py")
assert _SPEC is not None and _SPEC.loader is not None
cds = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cds)

_GOOD = "# T\n\n## Descrição\n\n## Tipagem\n\n## Política de retry\n\n## Exemplos\n"
_NAV = "nav:\n" + "".join(f"  - X: {s}.md\n" for s in cds.CANONICAL_SLUGS)
_NAV += "  - Y:\n      - A: ingestion/a.md\n"
_MKDOCS = _NAV + "\nexclude_docs: |\n  # c\n  backlog/\n  CLAUDE.md\n"


def _tree(tmp_path: Path, a_text: str = _GOOD) -> Path:
	"""Build a minimal clean docs tree and return it."""
	docs = tmp_path / "docs"
	(docs / "ingestion").mkdir(parents=True)
	for slug in cds.CANONICAL_SLUGS:
		(docs / f"{slug}.md").write_text("# x\n", encoding="utf-8")
	(docs / "ingestion" / "a.md").write_text(a_text, encoding="utf-8")
	return docs


def test_check_docs_clean_tree_passes(tmp_path: Path) -> None:
	"""A complete tree has no violations."""
	assert cds.check_docs(_tree(tmp_path), _MKDOCS) == []


def test_check_docs_missing_canonical_page_fails(tmp_path: Path) -> None:
	"""Deleting a canonical page is reported."""
	docs = _tree(tmp_path)
	(docs / "faq.md").unlink()
	assert any("faq.md is missing" in e for e in cds.check_docs(docs, _MKDOCS))


def test_check_docs_page_outside_nav_fails(tmp_path: Path) -> None:
	"""A published page absent from the nav is reported; an excluded one is not."""
	docs = _tree(tmp_path)
	(docs / "orphan.md").write_text("# o\n", encoding="utf-8")
	(docs / "backlog").mkdir()
	(docs / "backlog" / "x.md").write_text("# b\n", encoding="utf-8")
	errs = cds.check_docs(docs, _MKDOCS)
	assert errs == ["docs/orphan.md is published but missing from mkdocs.yml nav"]


def test_check_docs_new_family_page_missing_section_fails(tmp_path: Path) -> None:
	"""A non-allowlisted family page lacking a section is the negative case."""
	docs = _tree(tmp_path, "# T\n\n## Descrição\n")
	errs = cds.check_docs(docs, _MKDOCS)
	assert len(errs) == 1 and "Tipagem" in errs[0] and "Exemplos" in errs[0]


def test_check_docs_allowlisted_page_tolerated_then_stale_fails(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""A legacy page may stay bad, but once compliant it must leave the allowlist."""
	monkeypatch.setattr(cds, "LEGACY_NONCOMPLIANT", frozenset({"ingestion/a.md"}))
	bad = _tree(tmp_path / "bad", "# T\n")
	assert cds.check_docs(bad, _MKDOCS) == []
	good = _tree(tmp_path / "good")
	assert "remove it from LEGACY_NONCOMPLIANT" in cds.check_docs(good, _MKDOCS)[0]


def test_nav_pages_ignores_comments_and_reads_quoted_paths() -> None:
	"""A commented-out entry is not registered; a quoted path is."""
	text = "nav:\n  # - Old: old.md\n  - A: 'a.md'\n  - B: \"b.md\"\n  - C: c.md  # note x.md\n"
	assert cds._nav_pages(text) == {"a.md", "b.md", "c.md"}


def test_check_docs_heading_inside_code_fence_does_not_count(tmp_path: Path) -> None:
	"""A required heading that only appears inside a fenced block is still missing."""
	fenced = (
		"# T\n\n## Descrição\n\n## Tipagem\n\n## Política de retry\n\n```md\n## Exemplos\n```\n"
	)
	errs = cds.check_docs(_tree(tmp_path, fenced), _MKDOCS)
	assert len(errs) == 1 and "Exemplos" in errs[0]


def test_headings_longer_fence_is_not_closed_by_a_shorter_one(tmp_path: Path) -> None:
	"""A three-backtick line inside a four-backtick block leaves the block open."""
	page = tmp_path / "p.md"
	page.write_text("````md\n```\n## Exemplos\n````\n## Real\n", encoding="utf-8")
	assert cds._headings(page) == {"Real"}


def test_headings_longer_fence_is_not_closed_by_a_longer_one(tmp_path: Path) -> None:
	"""The closing fence must match the opener's length exactly, not merely reach it."""
	page = tmp_path / "p.md"
	page.write_text("````md\n`````\n## Exemplos\n````\n## Real\n", encoding="utf-8")
	assert cds._headings(page) == {"Real"}


def test_headings_skips_multiline_html_comment(tmp_path: Path) -> None:
	"""A heading inside an HTML comment does not render, so it does not count."""
	page = tmp_path / "p.md"
	page.write_text("<!--\n## Tipagem\n-->\n## Real\n", encoding="utf-8")
	assert cds._headings(page) == {"Real"}


def test_headings_comment_marker_inside_fence_opens_no_comment(tmp_path: Path) -> None:
	"""A literal ``<!--`` in a fenced block does not swallow the rest of the page."""
	page = tmp_path / "p.md"
	page.write_text("```html\n<!--\n```\n## Real\n", encoding="utf-8")
	assert cds._headings(page) == {"Real"}


def test_excluded_reads_same_line_value() -> None:
	"""``exclude_docs: backlog/`` counts, and the ``|`` block marker is not a pattern."""
	assert cds._excluded("exclude_docs: backlog/\n") == ["backlog/"]
	assert cds._excluded("exclude_docs: |\n  backlog/\n") == ["backlog/"]


def test_check_docs_wildcard_exclude_pattern_fails(tmp_path: Path) -> None:
	"""A wildcard the gate cannot read is named, not silently misread."""
	errs = cds.check_docs(_tree(tmp_path), _MKDOCS + "  drafts/*.md\n")
	assert len(errs) == 1 and "drafts/*.md" in errs[0]


def test_stale_allowlist_names_a_deleted_page(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""An allowlist entry whose page is gone is an error; a present one is not."""
	docs = _tree(tmp_path)
	monkeypatch.setattr(cds, "LEGACY_NONCOMPLIANT", {"ingestion/a.md", "ingestion/gone.md"})
	errs = cds.stale_allowlist(docs)
	assert len(errs) == 1 and "ingestion/gone.md" in errs[0]


def test_is_excluded_negation_and_dotfiles() -> None:
	"""Last match wins, `!` re-includes, and dot-paths are excluded implicitly."""
	assert cds._is_excluded("backlog/x.md", ["backlog/"])
	assert not cds._is_excluded("backlog/x.md", ["backlog/", "!backlog/x.md"])
	assert cds._is_excluded(".hidden/x.md", [])
	assert cds._is_excluded("a/.b.md", [])
	assert not cds._is_excluded("a.md", [])


def test_real_docs_pass() -> None:
	"""The repository's own docs satisfy the gate."""
	text = (_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
	assert cds.check_docs(_ROOT / "docs", text) == []
	assert cds.stale_allowlist(_ROOT / "docs") == []


def test_canonical_slugs_are_the_six_required_pages() -> None:
	"""Pinned literally: the other tests derive from the constant, so they cannot catch a drop."""
	assert set(cds.CANONICAL_SLUGS) == {
		"index",
		"usage",
		"api",
		"faq",
		"contributing",
		"changelog",
	}


def test_headings_strips_a_closing_sequence(tmp_path: Path) -> None:
	"""``## Descrição ##`` renders as ``Descrição``, and ``C#`` keeps its hash."""
	page = tmp_path / "a.md"
	page.write_text("## Descrição ##\n\n## C#\n", encoding="utf-8")
	assert cds._headings(page) == {"Descrição", "C#"}


def test_is_excluded_top_level_templates_only() -> None:
	"""MkDocs drops ``/templates/`` by default, but not a nested folder of that name."""
	assert cds._is_excluded("templates/a.md", [])
	assert not cds._is_excluded("ingestion/templates/a.md", [])
