"""CVM Informe Trimestral V1 (until 2017-06) — submission (envio) writer.

Produces the Informe Trimestral V1 XML from a validated :class:`InformeTrimestralV1Document`.
The document shape (``DOC_ARQ`` > ``CAB_INFORM`` + ``LISTA_INFORM`` > ``INFORM``) and the
namespace, encoding and element serialiser are the V2 writer's, imported rather than copied;
only the schema differs. Pure logic plus file I/O at the edges — no network.
"""

import os
from pathlib import Path
from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.informe_trimestral_v1 import (
	InformeTrimestralV1Document,
)
from filings_cvm._internal.utils.typing import type_checker
from filings_cvm.submission.informe_quadrimestral import (
	_DECLARATION,
	_ENCODING,
	_INDENT,
	_NAMESPACE,
	_append,
)


@type_checker
def _render(doc: InformeTrimestralV1Document) -> str:
	"""Render the document as XML text, declaration included.

	Parameters
	----------
	doc : InformeTrimestralV1Document
		Fully validated document model.

	Returns
	-------
	str
		The XML text.
	"""
	root = ET.Element("DOC_ARQ", {"xmlns": _NAMESPACE})
	_append(root, "cab_inform", doc.header)
	informs = ET.SubElement(root, "LISTA_INFORM")
	for inform in doc.informs:
		_append(informs, "inform", inform)
	ET.indent(root, space=_INDENT)
	return _DECLARATION + ET.tostring(root, encoding="unicode") + "\n"


@type_checker
def _encode(xml_str: str) -> bytes:
	"""Encode the XML and check it is well-formed, before any destination is opened.

	Parameters
	----------
	xml_str : str
		The XML text.

	Returns
	-------
	bytes
		The windows-1252 payload.

	Raises
	------
	ValueError
		If the text cannot be encoded or is not well-formed XML (only possible when validation
		was bypassed, e.g. ``model_construct``).
	"""
	try:
		payload = xml_str.encode(_ENCODING)
		ET.fromstring(payload)  # noqa: S314  # well-formedness self-check of our own output
	except (UnicodeEncodeError, ET.ParseError) as exc:
		raise ValueError(f"document cannot be serialised as {_ENCODING} XML: {exc}") from exc
	return payload


@type_checker
def _write_replacing(path: Path, payload: bytes) -> None:
	"""Write ``payload`` to a sibling temp file, then swap it over ``path`` in one step.

	A crash mid-write leaves the previous file intact.

	Parameters
	----------
	path : Path
		Destination file.
	payload : bytes
		The bytes to write.
	"""
	# ponytail: #330's atomic_write_bytes replaces this once it lands on main.
	tmp = path.with_name(f".{path.name}.tmp")
	try:
		tmp.write_bytes(payload)
		os.replace(tmp, path)
	finally:
		tmp.unlink(missing_ok=True)


class InformeTrimestralV1(SubmissionWriter[InformeTrimestralV1Document]):
	"""Serialize a validated Informe Trimestral V1 document to CVM-compliant XML.

	Concrete :class:`SubmissionWriter` for the Informe Trimestral V1 XML standard.

	Methods
	-------
	export(doc, output_path)
		Serialize a validated document to windows-1252 XML.
	"""

	def export(
		self, doc: InformeTrimestralV1Document, output_path: str | None = None
	) -> str | None:
		"""Serialize a validated document to a CVM-compliant XML string or file.

		Parameters
		----------
		doc : InformeTrimestralV1Document
			Fully validated document model.
		output_path : Optional[str]
			Destination file. When given the file is written in windows-1252 and ``None`` is
			returned; otherwise the XML string is returned, by default None.

		Returns
		-------
		Optional[str]
			The XML text when ``output_path`` is None, else None.
		"""
		xml_str = _render(doc)
		payload = _encode(xml_str)
		if output_path is None:
			return xml_str
		_write_replacing(Path(output_path), payload)
		return None
