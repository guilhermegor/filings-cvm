"""The BlueprintX docs skeleton and the docs-structure gate must name the same pages."""

import importlib.util
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location("cds", _ROOT / "bin" / "check_docs_sections.py")
assert _SPEC is not None and _SPEC.loader is not None
cds = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cds)


def _skeleton_pages() -> set[str]:
	"""Return the ``required_pages`` entries of ``docs/.docs-skeleton.yaml``."""
	text = (_ROOT / "docs" / ".docs-skeleton.yaml").read_text(encoding="utf-8")
	return {line.strip()[2:] for line in text.splitlines() if line.strip().startswith("- ")}


def test_skeleton_matches_canonical_slugs() -> None:
	"""The skeleton and ``CANONICAL_SLUGS`` list exactly the same pages."""
	assert _skeleton_pages() == {f"{slug}.md" for slug in cds.CANONICAL_SLUGS}


def test_skeleton_pages_exist() -> None:
	"""Every page the skeleton requires is on disk."""
	assert all((_ROOT / "docs" / page).is_file() for page in _skeleton_pages())


def test_api_reference_is_a_directory() -> None:
	"""The API reference never reverts to a single ``api.md`` (deep links would rot)."""
	assert not (_ROOT / "docs" / "api.md").exists()
