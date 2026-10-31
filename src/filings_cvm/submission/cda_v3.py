"""CVM CDA V3 (Composição e Diversificação das Aplicações) — submission (envio) writer.

Produces CVM-compliant CDA V3 XML (namespace ``urn:cda``, ``VERSAO=3.0``). Tag order, decimal
scales and encoding are identical to V4, so serialisation is inherited from :class:`Cda`; the
V3-specific layout lives in the schema.
"""

from filings_cvm._internal.config.schemas.cda_v3 import CdaV3Document
from filings_cvm.submission.cda import Cda


class CdaV3(Cda):
	"""Serialize a validated CDA V3 document to CVM-compliant XML.

	Methods
	-------
	export(doc, output_path)
		Serialize a validated V3 document to a CVM-compliant XML string.
	"""

	def export(self, doc: CdaV3Document, output_path: str | None = None) -> str | None:  # type: ignore[override]
		"""Serialize a validated CdaV3Document to a CVM-compliant XML string.

		Parameters
		----------
		doc : CdaV3Document
			Fully validated V3 document model (a V4 ``CdaDocument`` is refused).
		output_path : Optional[str]
			Destination file path (written as windows-1252). If given, None is
			returned; otherwise the XML string is returned, by default None.

		Returns
		-------
		Optional[str]
			XML string when output_path is None, else None.
		"""
		return super().export(doc, output_path)
