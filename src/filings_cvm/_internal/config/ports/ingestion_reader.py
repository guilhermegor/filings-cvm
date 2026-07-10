"""Ingestion reader port — the shared contract every *leitura* reader (adapter) implements.

Every ``ingestion`` solution turns a file received/downloaded from CVM into typed data.
This ABC is the **port** (hexagonal ports-and-adapters) pinning that single operation —
:meth:`read` — so callers can treat any reader polymorphically and every new standard
implements the same shape. It is private (``_internal``): consumers import the concrete
readers (the adapters), never this port.

Readers vary in what they take to locate their source (a reference month, a file path),
so :meth:`read` declares no required parameters; a concrete reader may add its own with
defaults (Liskov-compatible) and receives the rest of its configuration at construction.
Every reader returns a typed, contract-validated :class:`pandas.DataFrame`.

Constructor convention — ``path_raw``
-------------------------------------
Ports pin behaviour, not construction, so this cannot be enforced in the ABC; it is a
convention every reader in this library (and every sibling ingestion package) follows.
**Each reader accepts an optional ``path_raw: Path | None = None``.** When ``None`` the
source artifact is fetched into a :class:`tempfile.TemporaryDirectory` and destroyed on
exit — nothing *persists*, though the read does transiently touch the filesystem and needs
a writable temp directory. When set, the untouched raw artifact (``.zip``, ``.csv``,
``.html``, ``.xlsx``, …) is written there and **kept**.

Keeping it makes a downstream datalake's bronze layer authoritative: when a source changes
its contract and the transform breaks, the exact bytes that broke it are still on disk,
replayable, rather than lost to a re-fetch of an already-changed source. Readers implement
this through the shared :func:`_internal.utils.raw_workspace.raw_workspace` context manager
rather than branching on the tempdir themselves.
"""

from __future__ import annotations

from abc import abstractmethod

import pandas as pd

from filings_cvm._internal.utils.typing import ABCTypeCheckerMeta


class IngestionReader(metaclass=ABCTypeCheckerMeta):
	"""Contract for an ingestion (leitura) reader: CVM file → typed DataFrame.

	Methods
	-------
	read()
		Read the configured CVM source into a typed, contract-validated DataFrame.
	"""

	@abstractmethod
	def read(self) -> pd.DataFrame:
		"""Read the configured CVM source into a typed, validated DataFrame.

		Returns
		-------
		pd.DataFrame
			The parsed rows, with explicit column types applied.
		"""
		raise NotImplementedError
