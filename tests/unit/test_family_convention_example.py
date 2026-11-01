"""Family-wide convention for the public ingestion readers, enforced by introspection.

Every public reader must honour the same shape: an ``IngestionReader`` subclass, exported under
its own class name, ending in ``Reader``, and concrete (no abstract method left unimplemented).
Rather than rely on prose, this test *discovers* the family from the portal roots' ``__all__``
(``iter_public_readers``) and asserts the convention on each member, so a new reader that skips
it fails CI without anyone editing this file.

Two traps avoided:

* **Discover, never hand-list** the members: a hand-listed tuple rots the moment a reader is
  added, the exact failure this test prevents.
* **A meta-test pins the discovery itself**, so the per-member tests can never silently cover
  nothing (a parametrised gate over zero members is green and checks nothing).
"""

import inspect

import pytest

from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.introspection import iter_public_readers, iter_root_packages


_FAMILY = iter_public_readers()


def test_the_discovered_family_is_not_empty() -> None:
	"""Guard the discovery itself: an empty family makes every per-member test vacuous."""
	assert _FAMILY, "the family must not be empty"


def test_discovery_matches_the_declared_surface() -> None:
	"""Every name a portal root declares in ``__all__`` is a discovered member, none extra.

	Split from the non-empty guard above: "found something" and "found exactly what was
	declared" are different failures with different causes.
	"""
	int_declared = sum(len(module_root.__all__) for module_root in iter_root_packages().values())
	assert len(_FAMILY) == int_declared


@pytest.mark.parametrize("str_name", sorted(_FAMILY))
def test_member_is_a_concrete_ingestion_reader_named_after_its_export(str_name: str) -> None:
	"""Assert each member subclasses the port, is exported under its own name, and is concrete.

	Parameters
	----------
	str_name : str
		The exported name of a public reader.
	"""
	cls_member = _FAMILY[str_name]
	assert (
		issubclass(cls_member, IngestionReader)
		and cls_member.__name__ == str_name
		and str_name.endswith("Reader")
		and not inspect.isabstract(cls_member)
	)
