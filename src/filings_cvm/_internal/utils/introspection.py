"""Enumerate the package's public ingestion readers, grouped by CVM portal root.

Since the readers stopped being re-exported into one flat namespace, "every public reader" is no
longer a single ``__all__`` to read — it is the union of the 22 portal-root packages' own
``__all__``. Several gates need exactly that set (the retry-policy sweep, the META roster, the
contract-drift registry), so it is defined **once** here rather than re-derived in each.

⚠️ **The count must never be allowed to reach zero silently.** These helpers back parametrised
gates, and a discovery that quietly returns nothing turns a suite full of green into a suite that
checks nothing — the failure mode that a flat-``__all__`` walk hit the moment the flat namespace
went away. :func:`iter_public_readers` therefore raises rather than returning an empty mapping.

This is **private** (`_internal`): it is introspection over the package's own layout, not API.
"""

from __future__ import annotations

import importlib
from types import ModuleType

from filings_cvm._internal.utils.typing import type_checker


@type_checker
def iter_root_packages() -> dict[str, ModuleType]:
	"""Import and return every CVM portal-root package, keyed by its root name.

	Returns
	-------
	dict[str, types.ModuleType]
		The imported root packages (``fi``, ``fidc``, ``cia_aberta``, …), keyed by name, as
		declared by ``filings_cvm.ingestion.__all__``.

	Raises
	------
	RuntimeError
		If the ingestion package declares no roots — a silent empty discovery would disarm
		every gate built on it.
	"""
	module_ingestion = importlib.import_module("filings_cvm.ingestion")
	tuple_roots = tuple(module_ingestion.__all__)
	if not tuple_roots:
		raise RuntimeError("filings_cvm.ingestion declares no portal roots — discovery is broken")
	return {
		str_root: importlib.import_module(f"filings_cvm.ingestion.{str_root}")
		for str_root in tuple_roots
	}


@type_checker
def iter_public_readers() -> dict[str, type]:
	"""Return every public ingestion reader class, keyed by its class name.

	Readers are discovered **through the portal-root packages**, which are the public surface —
	never through a flat top-level namespace, which no longer carries them.

	Returns
	-------
	dict[str, type]
		Every name in every root's ``__all__``, mapped to the class it resolves to.

	Raises
	------
	RuntimeError
		If no readers are found, or if two roots export the same name (which would make
		"the reader that owns this name" ambiguous for the drift registry).
	"""
	dict_readers: dict[str, type] = {}
	dict_owner: dict[str, str] = {}
	for str_root, module_root in iter_root_packages().items():
		for str_name in module_root.__all__:
			if str_name in dict_owner:
				raise RuntimeError(
					f"'{str_name}' is exported by both '{dict_owner[str_name]}' and '{str_root}'"
				)
			dict_owner[str_name] = str_root
			dict_readers[str_name] = getattr(module_root, str_name)
	if not dict_readers:
		raise RuntimeError("no public readers discovered — the gates built on this would be inert")
	return dict_readers
