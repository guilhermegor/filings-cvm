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

import importlib
import inspect
import pkgutil

import pytest

from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.introspection import iter_public_readers
import filings_cvm.ingestion as pkg_ingestion


_FAMILY = iter_public_readers()


def test_the_discovered_family_is_not_empty() -> None:
	"""Guard the discovery itself: an empty family makes every per-member test vacuous."""
	assert _FAMILY, "the family must not be empty"


def test_discovery_matches_the_readers_defined_on_disk() -> None:
	"""The exported family equals the concrete readers found by walking the modules.

	The walk ignores ``__all__`` entirely (and skips ``_``-prefixed modules, where the private
	bases live), so a reader a root forgot to export shows up as a difference.
	"""
	list_names = [
		info.name
		for info in pkgutil.walk_packages(pkg_ingestion.__path__, f"{pkg_ingestion.__name__}.")
	]
	list_public = list(filter(lambda str_name: "._" not in str_name, list_names))
	list_modules = list(map(importlib.import_module, list_public))
	list_pairs = [
		(str_attr, obj) for module in list_modules for str_attr, obj in vars(module).items()
	]
	set_defined = set(
		str_attr
		for str_attr, obj in filter(
			lambda tuple_pair: (
				inspect.isclass(tuple_pair[1])
				and not tuple_pair[0].startswith(("_", "Base"))
				and issubclass(tuple_pair[1], IngestionReader)
				and not inspect.isabstract(tuple_pair[1])
			),
			list_pairs,
		)
	)
	assert set(_FAMILY) == set_defined


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
