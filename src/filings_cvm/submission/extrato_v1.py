"""CVM Extrato das Informações sobre o Fundo V1 (ICVM 450) — submission (envio) writer.

Produces the V1 XML from a validated :class:`ExtratoV1Document`. The document layout, the
namespace (``urn:extr``), the encoding and the 1 MB limit are the ones the V3 writer already
implements, so its serialiser (one recursive walk over ``model_fields``) is reused; only the
schema differs. Pure logic plus file I/O at the edges — no network.
"""

import os
from pathlib import Path
import tempfile
from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.extrato_v1 import ExtratoV1Document
from filings_cvm._internal.utils.typing import type_checker
from filings_cvm.submission.extrato import (
	_DECLARATION,
	_ENCODING,
	_INDENT,
	_MAX_BYTES,
	_NAMESPACE,
	_append,
)


@type_checker
def _build(doc: ExtratoV1Document) -> str:
	"""Render the document as an indented XML string with the windows-1252 prolog.

	Parameters
	----------
	doc : ExtratoV1Document
		Fully validated document model.

	Returns
	-------
	str
		The XML text.
	"""
	root = ET.Element("DOC_ARQ", {"xmlns": _NAMESPACE})
	_append(root, "cab_inform", doc.header)
	funds = ET.SubElement(root, "EXTRATO_FUNDO")
	for row in doc.rows:
		_append(funds, "row_extrato", row)
	ET.indent(root, space=_INDENT)
	return _DECLARATION + ET.tostring(root, encoding="unicode") + "\n"


@type_checker
def _encode(xml_str: str) -> bytes:
	"""Encode the XML and check it is well formed, before any file is opened.

	Parameters
	----------
	xml_str : str
		The rendered XML.

	Returns
	-------
	bytes
		The windows-1252 payload.

	Raises
	------
	ValueError
		If the text is not windows-1252 encodable or not well-formed XML.
	"""
	try:
		payload = xml_str.encode(_ENCODING)
		ET.fromstring(payload)  # noqa: S314  # well-formedness self-check of our own output
	except (UnicodeEncodeError, ET.ParseError) as exc:
		raise ValueError(f"document cannot be serialised as {_ENCODING} XML: {exc}") from exc
	return payload


@type_checker
def _write_atomic(payload: bytes, destination: str) -> None:
	"""Write ``payload`` to a temp file beside ``destination`` and ``os.replace`` it into place.

	A crash mid-write leaves the previous file untouched. Issue #330 will move this onto the
	shared ``atomic_write_bytes``.

	Parameters
	----------
	payload : bytes
		The encoded file.
	destination : str
		Final path.
	"""
	target = Path(destination)
	handle, temp_name = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.")
	try:
		with os.fdopen(handle, "wb") as stream:
			stream.write(payload)
		os.replace(temp_name, target)
	finally:
		Path(temp_name).unlink(missing_ok=True)


@type_checker
def _check_size(payload: bytes) -> None:
	"""Refuse a file above the page's 1 MB limit.

	Parameters
	----------
	payload : bytes
		The encoded file.

	Raises
	------
	ValueError
		If the file exceeds 1 MB.
	"""
	if len(payload) > _MAX_BYTES:
		raise ValueError(f"file is {len(payload)} bytes; the page allows at most 1 MB")


class ExtratoV1(SubmissionWriter[ExtratoV1Document]):
	"""Serialize a validated Extrato V1 document to CVM-compliant XML.

	Concrete :class:`SubmissionWriter` for the Extrato das Informações sobre o Fundo V1
	(ICVM 450) XML standard.

	Methods
	-------
	export(doc, output_path)
		Serialize a validated document to windows-1252 XML.
	"""

	def export(self, doc: ExtratoV1Document, output_path: str | None = None) -> str | None:
		"""Serialize a validated ExtratoV1Document to a CVM-compliant XML string or file.

		The text is encoded and checked for well-formedness and size **before** the destination
		is opened, so a failure never truncates an existing file.

		Parameters
		----------
		doc : ExtratoV1Document
			Fully validated document model.
		output_path : Optional[str]
			Destination file. When given the file is written in windows-1252 and ``None`` is
			returned; otherwise the XML string is returned, by default None.

		Returns
		-------
		Optional[str]
			The XML text when ``output_path`` is None, else None.

		Raises
		------
		ValueError
			If the document holds text windows-1252 cannot encode or XML cannot carry (only
			possible when validation was bypassed, e.g. ``model_construct``), or the encoded
			file exceeds the page's 1 MB limit.
		"""
		xml_str = _build(doc)
		payload = _encode(xml_str)
		_check_size(payload)
		if output_path is None:
			return xml_str
		_write_atomic(payload, output_path)
		return None
