"""Ports — the behavioural boundary interfaces of the library (hexagonal, private).

In ports-and-adapters terms these ABCs are the **ports**: the abstract operation each
macro-section's concrete classes (the *adapters*) implement — :class:`SubmissionWriter.export`
(envio) and :class:`IngestionReader.read` (leitura) — so every standard conforms to the same
shape. They ship inside the wheel under ``_internal`` but are **not** part of the public API:
consumers import the concrete writers/readers, never these ports.
"""

from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter


__all__ = ["IngestionReader", "SubmissionWriter"]
