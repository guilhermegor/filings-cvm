"""Tests for ``bin/lib/description_sources.py`` (the description-sync gate's reader)."""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


def _load() -> ModuleType:
	"""Import the ``bin/lib`` script by path (``bin/`` is not a package).

	Returns
	-------
	types.ModuleType
		The loaded ``description_sources`` module.
	"""
	spec = importlib.util.spec_from_file_location(
		"description_sources",
		Path(__file__).resolve().parents[2] / "bin" / "lib" / "description_sources.py",
	)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


@pytest.mark.parametrize("str_raw", [">-", "|", ">"])
def test_a_block_scalar_is_unreadable_not_a_false_mismatch(str_raw: str) -> None:
	"""A folded/literal ``site_description`` is rejected instead of compared as ``>-``."""
	module = _load()
	with pytest.raises(module.UnreadableDescriptionError):
		module.parse_yaml_scalar(str_raw)


def test_a_plain_scalar_with_a_trailing_comment_is_read() -> None:
	"""The ordinary form still parses, comment stripped."""
	assert _load().parse_yaml_scalar("Biblioteca CVM  # nota") == "Biblioteca CVM"
