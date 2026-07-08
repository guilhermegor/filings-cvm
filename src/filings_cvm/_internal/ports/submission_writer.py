"""Submission writer port — the shared contract every *envio* writer (adapter) implements.

Every ``submission`` solution turns a validated schema document into a CVM-compliant
file to send to CVM. This ABC is the **port** (hexagonal ports-and-adapters) pinning that
single operation — :meth:`export` — so callers can treat any writer polymorphically and
every new standard implements the same shape. It is private (``_internal``): consumers
import the concrete writers (the adapters), never this port.

The document type varies per standard, so the port is generic over ``TDoc`` (bound
to :class:`pydantic.BaseModel`): a concrete writer conforms by parameterising it, e.g.
``class InformeDiario(SubmissionWriter[InformeDiarioDocument])``. This narrows the
document type through the type parameter rather than by re-annotating an override, so
the concrete signature stays Liskov-compatible.

CVM's submission standards are all XML today, so :meth:`export` produces XML; the generic
name leaves room for a future non-XML export without changing the contract.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

from filings_cvm._internal.utils.typing import ABCTypeCheckerMeta


TDoc = TypeVar("TDoc", bound=BaseModel)


class SubmissionWriter(Generic[TDoc], metaclass=ABCTypeCheckerMeta):
	"""Contract for a submission (envio) writer: validated document → CVM file.

	Methods
	-------
	export(doc, output_path)
		Serialise a validated document to a CVM-compliant file string, optionally
		writing it to ``output_path``.
	"""

	@abstractmethod
	def export(self, doc: TDoc, output_path: str | None = None) -> str | None:
		"""Serialise ``doc`` to a CVM-compliant file (string, or written to disk).

		Parameters
		----------
		doc : TDoc
			Fully validated document model for the standard.
		output_path : str, optional
			Destination file path. When given, the file is written and ``None`` is
			returned; otherwise the serialised string is returned. By default ``None``.

		Returns
		-------
		str or None
			The serialised content when ``output_path`` is ``None``, else ``None``.
		"""
		raise NotImplementedError
