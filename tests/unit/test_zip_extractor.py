"""Unit tests for the zip extraction seam: uniform missing-archive error, member selection."""

from __future__ import annotations

from pathlib import Path

import pytest

from filings_cvm._internal.utils.zip_extractor import extract_all, find_member


def test_extract_all_missing_zip_raises_file_not_found(tmp_path: Path) -> None:
	"""A missing archive fails with ``FileNotFoundError`` naming the path."""
	with pytest.raises(FileNotFoundError, match="Zip not found"):
		extract_all(tmp_path / "absent.zip", tmp_path / "out")


def test_find_member_unknown_name_lists_available_members(tmp_path: Path) -> None:
	"""An unmatched name raises ``ValueError`` listing what the archive does hold."""
	list_members = [tmp_path / "b.csv", tmp_path / "a.csv"]

	with pytest.raises(ValueError, match=r"Available: \['a.csv', 'b.csv'\]"):
		find_member(list_members, "c.csv")


def test_find_member_matches_exact_name_not_prefix(tmp_path: Path) -> None:
	"""Selection is by exact name, so a member that prefixes another is not confused."""
	path_short = tmp_path / "lamina_fi_202504.csv"
	path_long = tmp_path / "lamina_fi_carteira_202504.csv"

	assert find_member([path_long, path_short], "lamina_fi_202504.csv") == path_short
