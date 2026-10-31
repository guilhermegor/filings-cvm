"""CVM Lâmina de Fundos V2 — submission (envio) writer.

V2 has the same tags, in the same order, as V3 minus ``COD_SUBCLASSE`` (measured against both
pages), so the serialiser is V3's, reused by delegation; the V2 document model is what pins
``VERSAO`` to ``2.0`` and drops the subclass identifier.
"""

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.lamina_v2 import LaminaV2Document
from filings_cvm.submission.lamina import Lamina


class LaminaV2(SubmissionWriter[LaminaV2Document]):
	"""Serialize a validated Lâmina V2 document to CVM-compliant XML.

	Concrete :class:`SubmissionWriter` for the Lâmina de Fundos V2 XML standard
	(``PadraoXMLLaminaV2.asp``).

	Methods
	-------
	export(doc, output_path)
		Serialize a validated V2 document to windows-1252 XML.
	"""

	def export(self, doc: LaminaV2Document, output_path: str | None = None) -> str | None:
		"""Serialize a validated LaminaV2Document to an XML string or file.

		Parameters
		----------
		doc : LaminaV2Document
			Fully validated V2 document model.
		output_path : Optional[str]
			Destination file; when given the file is written and ``None`` is returned,
			by default None.

		Returns
		-------
		Optional[str]
			The XML text when ``output_path`` is None, else None.

		Raises
		------
		ValueError
			If the document cannot be serialised as windows-1252 XML.
		"""
		return Lamina().export(doc, output_path)
