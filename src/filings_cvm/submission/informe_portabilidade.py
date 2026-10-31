"""CVM Informe de Portabilidade — submission (envio) writer.

Produces the Informe de Portabilidade XML (COD_DOC 478, V1.0) from a validated
:class:`InformePortabilidadeDocument`. Pure logic plus file I/O at the edges — no network.
"""

from pathlib import Path
from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.informe_portabilidade import (
	InformePortabilidadeDocument,
)


_NAMESPACE = "urn:portab"
_ENCODING = "windows-1252"
_DECLARATION = f'<?xml version="1.0" encoding="{_ENCODING}"?>\n'
_INDENT = "    "


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
		opened, so a failure never truncates an existing file. Schema fields are declared
		in XML order and named after their tag, so each block is a walk over its fields.

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
			If the document holds text windows-1252 cannot encode or XML cannot carry
			(only possible when validation was bypassed, e.g. ``model_construct``).
		"""
		root = ET.Element("DOC_ARQ", {"xmlns": _NAMESPACE})
		blocks = [("CAB_INFORM", doc.header), *(("INFORM", inform) for inform in doc.informs)]
		for tag, model in blocks:
			element = ET.SubElement(root, tag)
			for name in type(model).model_fields:
				ET.SubElement(element, name.upper()).text = str(getattr(model, name))
		ET.indent(root, space=_INDENT)
		xml_str = _DECLARATION + ET.tostring(root, encoding="unicode") + "\n"
		try:
			payload = xml_str.encode(_ENCODING)
			ET.fromstring(payload)  # noqa: S314  # well-formedness check of our own output
		except (UnicodeEncodeError, ET.ParseError) as exc:
			raise ValueError(f"document cannot be serialised as {_ENCODING} XML: {exc}") from exc
		if output_path is None:
			return xml_str
		Path(output_path).write_bytes(payload)
		return None
