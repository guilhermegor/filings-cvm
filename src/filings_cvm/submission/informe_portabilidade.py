"""CVM Informe de Portabilidade — submission (envio) writer.

Produces the Informe de Portabilidade XML (COD_DOC 478, V1.0) from a validated
:class:`InformePortabilidadeDocument`. Pure logic plus file I/O at the edges — no network.
"""

from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from pydantic import BaseModel

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.informe_portabilidade import (
	InformePortabilidadeDocument,
)
from filings_cvm._internal.utils.atomic_write import atomic_write_bytes
from filings_cvm._internal.utils.typing import type_checker


_NAMESPACE = "urn:portab"
_ENCODING = "windows-1252"
_DECLARATION = f'<?xml version="1.0" encoding="{_ENCODING}"?>\n'
_INDENT = "    "


@type_checker
def _blocks(doc: InformePortabilidadeDocument) -> list[tuple[str, BaseModel]]:
	"""List the (tag, model) pairs of the document in XML order.

	Parameters
	----------
	doc : InformePortabilidadeDocument
		Fully validated document model.

	Returns
	-------
	list[tuple[str, BaseModel]]
		``CAB_INFORM`` first, then one ``INFORM`` per entry of ``doc.informs``.
	"""
	return [("CAB_INFORM", doc.header), *(("INFORM", inform) for inform in doc.informs)]


@type_checker
def _append_block(root: ET.Element, tag: str, model: BaseModel) -> None:
	"""Append one block whose children are the model fields, named after their tag.

	Parameters
	----------
	root : ET.Element
		Parent element.
	tag : str
		Block tag.
	model : BaseModel
		Model whose fields are declared in XML order.
	"""
	element = ET.SubElement(root, tag)
	for name in type(model).model_fields:
		ET.SubElement(element, name.upper()).text = str(getattr(model, name))


@type_checker
def _build_xml(doc: InformePortabilidadeDocument) -> str:
	"""Render the document as indented XML text with its declaration.

	Parameters
	----------
	doc : InformePortabilidadeDocument
		Fully validated document model.

	Returns
	-------
	str
		The XML text.
	"""
	root = ET.Element("DOC_ARQ", {"xmlns": _NAMESPACE})
	for tag, model in _blocks(doc):
		_append_block(root, tag, model)
	ET.indent(root, space=_INDENT)
	return _DECLARATION + ET.tostring(root, encoding="unicode") + "\n"


@type_checker
def _encode_checked(xml_str: str) -> bytes:
	"""Encode to windows-1252 and prove the bytes are well-formed XML.

	Parameters
	----------
	xml_str : str
		The XML text.

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
		ET.fromstring(payload)  # noqa: S314  # well-formedness check of our own output
	except (UnicodeEncodeError, ET.ParseError) as exc:
		raise ValueError(f"document cannot be serialised as {_ENCODING} XML: {exc}") from exc
	return payload


@type_checker
def _require_informs(doc: InformePortabilidadeDocument) -> None:
	"""Reject a document whose ``informs`` list was emptied after construction.

	The document model does not validate on assignment, so the schema's one-or-more rule
	can be bypassed by ``doc.informs = []``.

	Parameters
	----------
	doc : InformePortabilidadeDocument
		The document about to be serialised.

	Raises
	------
	ValueError
		If ``doc.informs`` is empty.
	"""
	if not doc.informs:
		raise ValueError("document has no INFORM block: at least one is required")


class InformePortabilidade(SubmissionWriter[InformePortabilidadeDocument]):
	"""Serialize a validated Informe de Portabilidade document to CVM-compliant XML.

	Methods
	-------
	export(doc, output_path)
		Serialize a validated document to windows-1252 XML.
	"""

	def export(
		self, doc: InformePortabilidadeDocument, output_path: str | None = None
	) -> str | None:
		"""Serialize a validated document to an XML string or a windows-1252 file.

		The text is encoded and checked for well-formedness before the destination is
		touched, and the file is written atomically, so a failure never truncates an
		existing file. Schema fields are declared in XML order and named after their tag,
		so each block is a walk over its fields.

		Parameters
		----------
		doc : InformePortabilidadeDocument
			Fully validated document model.
		output_path : Optional[str]
			Destination file. When given the file is written and None is returned;
			otherwise the XML string is returned, by default None.

		Returns
		-------
		Optional[str]
			The XML text when ``output_path`` is None, else None.

		Raises
		------
		ValueError
			If ``informs`` is empty (e.g. emptied after construction), or the document holds
			text windows-1252 cannot encode or XML cannot carry (only possible when validation
			was bypassed, e.g. ``model_construct``).
		"""
		_require_informs(doc)
		xml_str = _build_xml(doc)
		payload = _encode_checked(xml_str)
		if output_path is None:
			return xml_str
		atomic_write_bytes(output_path, payload)
		return None
