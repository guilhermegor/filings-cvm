"""CVM Informe Sintético (FICE, FMP-FGTS and FMAI) — submission (envio) writer.

Produces the ``PadraoXMLSintOutros.asp`` XML (``COD_DOC`` 9) from a validated
:class:`InformeSinteticoOutrosDocument`. Pure logic plus file I/O at the edges — no network.
"""

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.informe_sintetico import InformeSinteticoOutrosDocument
from filings_cvm.submission._informe_sintetico_xml import serialise


class InformeSinteticoOutros(SubmissionWriter[InformeSinteticoOutrosDocument]):
	"""Serialize a validated FICE, FMP-FGTS and FMAI Informe Sintético to CVM-compliant XML.

	Concrete :class:`SubmissionWriter` for ``PadraoXMLSintOutros.asp``.

	Methods
	-------
	export(doc, output_path)
		Serialize a validated document to windows-1252 XML.
	"""

	def export(
		self, doc: InformeSinteticoOutrosDocument, output_path: str | None = None
	) -> str | None:
		"""Serialize a validated document to a CVM-compliant XML string or file.

		The text is encoded and checked for well-formedness **before** the destination is
		opened, so a failure never truncates an existing file.

		Parameters
		----------
		doc : InformeSinteticoOutrosDocument
			Fully validated document model.
		output_path : Optional[str]
			Destination file, written in windows-1252 (``None`` is then returned); by default
			None, which returns the XML string.

		Returns
		-------
		Optional[str]
			The XML text when ``output_path`` is None, else None.

		Raises
		------
		ValueError
			If the document holds text windows-1252 cannot encode (validation bypassed).
		"""
		return serialise(doc, output_path)
