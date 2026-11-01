"""CVM Informe Diário V2 — submission (envio) writer.

Produces the V2 Daily Report XML (in force 2012-07-01 to 2015-09-30) from validated
schema models. Shared formatting and the shareholder block are reused from the V4 writer.
"""

from filings_cvm._internal.config.schemas.informe_diario_v2 import (
	InformeDiarioV2Document,
	InformeDiarioV2Inform,
)
from filings_cvm._internal.utils.atomic_write import atomic_write_bytes
from filings_cvm.submission.informe_diario import InformeDiario


class InformeDiarioV2(InformeDiario):
	"""Serialize a validated Informe Diário V2 document to CVM-compliant XML.

	Methods
	-------
	export(doc, output_path)
		Serialize a validated document to a CVM-compliant XML string.
	"""

	def export(  # type: ignore[override]
		self,
		doc: InformeDiarioV2Document,
		output_path: str | None = None,
	) -> str | None:
		"""Serialize a validated InformeDiarioV2Document to XML.

		Parameters
		----------
		doc : InformeDiarioV2Document
			Fully validated document model.
		output_path : Optional[str]
			Destination file, written as windows-1252. If given, None is returned;
			otherwise the XML string is returned, by default None.

		Returns
		-------
		Optional[str]
			XML string when output_path is None, else None.
		"""
		xml_str = self._build_v2_xml(doc)
		if output_path is None:
			return xml_str
		atomic_write_bytes(output_path, xml_str.encode("windows-1252"))
		return None

	def _build_v2_xml(self, doc: InformeDiarioV2Document) -> str:
		"""Build the full V2 XML string.

		Parameters
		----------
		doc : InformeDiarioV2Document
			Validated document model.

		Returns
		-------
		str
			CVM-compliant XML string (UTF-8 in memory).
		"""
		header = doc.header
		lines = [
			'<?xml version="1.0" encoding="windows-1252"?>',
			'<DOC_ARQ xmlns="urn:infdiario">',
			"    <CAB_INFORM>",
			f"        <COD_DOC>{header.cod_doc}</COD_DOC>",
			f"        <DT_COMPT>{header.dt_compt}</DT_COMPT>",
			f"        <DT_GERAC_ARQ>{header.dt_gerac_arq}</DT_GERAC_ARQ>",
			f"        <VERSAO>{header.versao}</VERSAO>",
			"    </CAB_INFORM>",
		]
		for inform in doc.informs:
			lines.extend(self._build_v2_inform_lines(inform))
		lines.append("</DOC_ARQ>")
		return "\n".join(lines)

	def _build_v2_inform_lines(self, inform: InformeDiarioV2Inform) -> list[str]:
		"""Build the XML lines for one V2 INFORM block.

		Parameters
		----------
		inform : InformeDiarioV2Inform
			Validated fund-informe model.

		Returns
		-------
		list[str]
			Ordered XML lines for this informe.
		"""
		ind = "    "
		inner = f"{ind}    "
		lines = [f"{ind}<INFORM>", f"{inner}<CNPJ_FDO>{inform.cnpj_fdo}</CNPJ_FDO>"]
		for tag, value, places in [
			("VL_TOTAL", inform.vl_total, 2),
			("VL_QUOTA", inform.vl_quota, 12),
			("PATRIM_LIQ", inform.patrim_liq, 2),
			("CAPTC_DIA", inform.captc_dia, 2),
			("RESG_DIA", inform.resg_dia, 2),
			("VL_TOTAL_SAI", inform.vl_total_sai, 2),
			("VL_TOTAL_ATV", inform.vl_total_atv, 2),
		]:
			lines.append(f"{inner}<{tag}>{self._fmt_decimal(value, places)}</{tag}>")
		lines.append(f"{inner}<NR_COTST>{inform.nr_cotst}</NR_COTST>")
		lines.extend(self._build_cotst_lines(inform.lista_cotst_signif, ind))
		lines.append(f"{ind}</INFORM>")
		return lines
