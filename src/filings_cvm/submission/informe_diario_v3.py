"""CVM Informe Diário V3 — submission (envio) writer.

Produces CVM-compliant Daily Report XML (V3, ``VERSAO`` 3.0) from validated schema
models. The V3 and V4 layouts share the tag order and decimal scales, so this writer
delegates to the V4 writer's public ``export`` instead of copying its builder.
"""

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.informe_diario_v3 import InformeDiarioV3Document
from filings_cvm.submission.informe_diario import InformeDiario


class InformeDiarioV3(SubmissionWriter[InformeDiarioV3Document]):
	"""Serialize a validated Informe Diário V3 document to CVM-compliant XML.

	Methods
	-------
	export(doc, output_path)
		Serialize a validated V3 document to a CVM-compliant XML string.
	"""

	def export(
		self,
		doc: InformeDiarioV3Document,
		output_path: str | None = None,
	) -> str | None:
		"""Serialize a validated InformeDiarioV3Document to CVM-compliant XML.

		Parameters
		----------
		doc : InformeDiarioV3Document
			Fully validated V3 document model.
		output_path : Optional[str]
			Destination file path, written atomically as windows-1252. If given, None
			is returned; otherwise the XML string is returned, by default None.

		Returns
		-------
		Optional[str]
			XML string when output_path is None, else None.
		"""
		return InformeDiario().export(doc, output_path, versao=doc.header.versao)
