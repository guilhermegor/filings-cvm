"""``docs/.docs-skeleton.yaml`` must agree with the lists ``check_docs_sections.py`` enforces."""

import importlib.util
from pathlib import Path

import yaml


_ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location(
	"cds_sync", _ROOT / "bin" / "check_docs_sections.py"
)
assert _SPEC is not None and _SPEC.loader is not None
cds = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cds)

_SKELETON = yaml.safe_load((_ROOT / "docs" / ".docs-skeleton.yaml").read_text(encoding="utf-8"))


def test_skeleton_required_pages_match_the_gate_canonical_slugs() -> None:
	"""The yaml names exactly the canonical pages the gate checks."""
	expected = sorted(f"{slug}.md" for slug in cds.CANONICAL_SLUGS)
	assert sorted(_SKELETON["required_pages"]) == expected


def test_skeleton_families_match_the_gate_families() -> None:
	"""The yaml declares exactly the section families the gate checks."""
	declared = {glob: tuple(labels) for glob, labels in _SKELETON["section_families"].items()}
	assert declared == cds.FAMILIES
