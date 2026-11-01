"""CVM Extrato das Informações sobre o Fundo — V2 submission (envio) writer.

V2 differs from V3 only in ``VERSAO``, which the V2 header pins, so the serialiser is the V3
one (:func:`_build_payload`) reused as is.
"""

from pathlib import Path

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.extrato_v2 import ExtratoV2Document
from filings_cvm.submission.extrato import _build_payload


class ExtratoV2(SubmissionWriter[ExtratoV2Document]):
	"""Serialize a validated Extrato V2 document to CVM-compliant XML.

	Concrete :class:`SubmissionWriter` for ``PadraoXMLInfExtratoV2.asp``.

	Methods
	-------
	export(doc, output_path)
		Serialize a validated document to windows-1252 XML.
	"""

	def export(self, doc: ExtratoV2Document, output_path: str | None = None) -> str | None:
		"""Serialize a validated ExtratoV2Document to a CVM-compliant XML string or file.

		The text is encoded and checked for well-formedness and size **before** the destination
		is opened, so a failure never truncates an existing file.

		Parameters
		----------
		doc : ExtratoV2Document
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
			If the document cannot be serialised as windows-1252 XML or exceeds the page's 1 MB.
		"""
		xml_str, payload = _build_payload(doc.header, doc.rows)
		if output_path is None:
			return xml_str
		Path(output_path).write_bytes(payload)
		return None
