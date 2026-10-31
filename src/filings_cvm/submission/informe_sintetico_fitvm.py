"""CVM Informe Sintético (FITVM, FMP-FGTS CL and FIIM) — submission (envio) writer.

Produces the ``PadraoXMLSintFITVM.asp`` XML (``COD_DOC`` 7) from a validated
:class:`InformeSinteticoFitvmDocument`. Pure logic plus file I/O at the edges — no network.
"""

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.informe_sintetico import InformeSinteticoFitvmDocument
from filings_cvm.submission._informe_sintetico_xml import serialise


class InformeSinteticoFitvm(SubmissionWriter[InformeSinteticoFitvmDocument]):
	"""Serialize a validated FITVM, FMP-FGTS CL and FIIM Informe Sintético to CVM-compliant XML.

	Concrete :class:`SubmissionWriter` for ``PadraoXMLSintFITVM.asp``.

	Methods
	-------
	export(doc, output_path)
		Serialize a validated document to windows-1252 XML.
	"""

	def export(
		self, doc: InformeSinteticoFitvmDocument, output_path: str | None = None
	) -> str | None:
		"""Serialize a validated document to a CVM-compliant XML string or file.

		The text is encoded and checked for well-formedness **before** the destination is
		opened, so a failure never truncates an existing file.

		Parameters
		----------
		doc : InformeSinteticoFitvmDocument
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
