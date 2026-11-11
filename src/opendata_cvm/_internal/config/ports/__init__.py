"""Ports — the behavioural boundary interfaces of the library (hexagonal, private).

In ports-and-adapters terms these ABCs are the **ports**: the abstract operation each
concrete class (the *adapters*) implements — :class:`IngestionReader.read` (leitura) — so every
standard conforms to the same shape. They ship inside the wheel under ``_internal`` but are
**not** part of the public API: consumers import the concrete readers, never these ports.
"""

from opendata_cvm._internal.config.ports.ingestion_reader import IngestionReader


__all__ = ["IngestionReader"]
