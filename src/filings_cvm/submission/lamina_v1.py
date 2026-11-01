"""CVM Lâmina de Fundos V1 — submission (envio) writer.

Produces the Lâmina V1 XML from a validated :class:`LaminaV1Document`. The serialiser is the V3
one (the schema walks in XML order, named after its tag), reused through its element builder;
only the document root differs. Pure logic plus file I/O at the edges — no network.
"""

from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.lamina_v1 import LaminaV1Document
from filings_cvm._internal.utils.atomic_write import atomic_write_bytes
from filings_cvm._internal.utils.typing import type_checker
from filings_cvm.submission.lamina import _DECLARATION, _ENCODING, _INDENT, _NAMESPACE, _append


@type_checker
def _render(doc: LaminaV1Document) -> str:
	"""Render the document as an indented XML string with its declaration.

	Parameters
	----------
	doc : LaminaV1Document
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
	"""Encode to windows-1252 and prove the bytes are well-formed XML.

	Parameters
	----------
	xml_str : str
		The rendered XML text.

	Returns
	-------
	bytes
		The encoded payload.

	Raises
	------
	ValueError
		If the text cannot be encoded or is not well-formed XML.
	"""
	try:
		payload = xml_str.encode(_ENCODING)
		ET.fromstring(payload)  # noqa: S314  # well-formedness self-check of our own output
	except (UnicodeEncodeError, ET.ParseError) as exc:
		raise ValueError(f"document cannot be serialised as {_ENCODING} XML: {exc}") from exc
	return payload


class LaminaV1(SubmissionWriter[LaminaV1Document]):
	"""Serialize a validated Lâmina V1 document to CVM-compliant XML.

	Concrete :class:`SubmissionWriter` for the Lâmina de Fundos V1 XML standard.

	Methods
	-------
	export(doc, output_path)
		Serialize a validated document to windows-1252 XML.
	"""

	def export(self, doc: LaminaV1Document, output_path: str | None = None) -> str | None:
		"""Serialize a validated LaminaV1Document to a CVM-compliant XML string or file.

		The text is encoded and checked for well-formedness **before** the destination is
		touched, and the file is replaced atomically, so a failure never truncates it.

		Parameters
		----------
		doc : LaminaV1Document
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
			possible when validation was bypassed, e.g. ``model_construct``).
		"""
		xml_str = _render(doc)
		payload = _encode(xml_str)
		if output_path is None:
			return xml_str
		atomic_write_bytes(output_path, payload)
		return None
