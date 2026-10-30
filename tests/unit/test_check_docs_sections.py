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


def test_real_docs_pass() -> None:
	"""The repository's own docs satisfy the gate."""
	text = (_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
	assert cds.check_docs(_ROOT / "docs", text) == []
