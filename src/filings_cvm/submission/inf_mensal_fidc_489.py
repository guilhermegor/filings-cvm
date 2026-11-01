"""CVM Informe Mensal FIDC — submission (envio) writer (ICVM 489, until 2019-11-01).

Produces the CVM-compliant ``urn:fidc`` XML for the predecessor layout of
``submission/inf_mensal_fidc.py``. The element walker is that module's, reused through
composition: it reads tags and scales from the schema, so it is document-type agnostic and
the 489 layout needs no per-field code here. Pure logic plus file I/O at the edges.
"""

import os
from pathlib import Path

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.inf_mensal_fidc_489 import InfMensalFidc489Document
from filings_cvm._internal.utils.typing import type_checker
from filings_cvm.submission.inf_mensal_fidc import InfMensalFidc


_ENCODING = "windows-1252"


@type_checker
def _write_atomic(path: Path, data: bytes) -> None:
	"""Write ``data`` to ``path`` so a reader never sees a half-written file.

	Parameters
	----------
	path : Path
		Destination file.
	data : bytes
		Already-encoded content; encoding first means a failure leaves no file behind.

	Notes
	-----
	# ponytail: stands in for ``atomic_write_bytes`` (PR #330), which migrates this.
	"""
	tmp = path.with_name(f".{path.name}.tmp")
	tmp.write_bytes(data)
	os.replace(tmp, path)


class InfMensalFidc489(SubmissionWriter[InfMensalFidc489Document]):
	"""Serialize a validated ICVM 489 Informe Mensal FIDC document to CVM-compliant XML.

	Methods
	-------
	export(doc, output_path)
		Serialize a validated document to a CVM-compliant XML string.
	"""

	def export(self, doc: InfMensalFidc489Document, output_path: str | None = None) -> str | None:
		"""Serialize a validated InfMensalFidc489Document to a CVM-compliant XML string.

		Parameters
		----------
		doc : InfMensalFidc489Document
			Fully validated document model.
		output_path : Optional[str]
			Destination file path, written in windows-1252 as CVM requires. If provided,
			None is returned; otherwise the XML string is returned, by default None.

		Returns
		-------
		Optional[str]
			XML string when output_path is None, else None.
		"""
		lines = ['<?xml version="1.0" encoding="windows-1252"?>', '<DOC_ARQ xmlns="urn:fidc">']
		lines.extend(InfMensalFidc()._block_lines(doc, 1))  # noqa: SLF001
		lines.append("</DOC_ARQ>")
		xml_str = "\n".join(lines)
		if output_path is not None:
			_write_atomic(Path(output_path), xml_str.encode(_ENCODING))
			return None
		return xml_str
