"""CVM Informe Diário — submission (envio) writer.

Produces CVM-compliant Daily Report XML (V4) from validated schema models. This is
the *sending* half of the standard; parsing CVM files back into models lives in the
``ingestion`` section. Pure logic plus file I/O at the edges — no network.
"""

from decimal import Decimal
from pathlib import Path

from filings_cvm._internal.schemas.informe_diario import (
	InformeDiarioDocument,
	InformeDiarioInform,
	SignificantShareholder,
)
from filings_cvm._internal.utils.typing import TypeChecker


class InformeDiario(metaclass=TypeChecker):
	"""Serialize a validated Informe Diário document to CVM-compliant XML.

	Methods
	-------
	to_xml(doc, output_path, versao)
		Serialize a validated document to a CVM-compliant XML string.
	"""

	def to_xml(
		self,
		doc: InformeDiarioDocument,
		output_path: str | None = None,
		versao: str = "4.0",
	) -> str | None:
		"""Serialize a validated InformeDiarioDocument to a CVM-compliant XML string.

		Produces UTF-8 text internally; when output_path is given the file is
		written with windows-1252 encoding as required by CVM.

		Parameters
		----------
		doc : InformeDiarioDocument
			Fully validated document model.
		output_path : Optional[str]
			Destination file path. If provided, the file is written and None is
			returned; otherwise the XML string is returned, by default None.
		versao : str
			CVM document format version placed in the VERSAO tag, by default "4.0".

		Returns
		-------
		Optional[str]
			XML string when output_path is None, else None.
		"""
		xml_str = self._build_xml_str(doc, versao=versao)
		if output_path is not None:
			Path(output_path).write_text(xml_str, encoding="windows-1252")
			return None
		return xml_str

	# XML building helpers, defined in top-down call order.

	def _build_xml_str(self, doc: InformeDiarioDocument, versao: str = "4.0") -> str:
		"""Build the full CVM XML string from an InformeDiarioDocument.

		Parameters
		----------
		doc : InformeDiarioDocument
			Validated document model.
		versao : str
			CVM document format version, by default "4.0".

		Returns
		-------
		str
			CVM-compliant XML string (UTF-8 in memory).
		"""
		lines: list[str] = []
		lines.append('<?xml version="1.0" encoding="windows-1252"?>')
		lines.append('<DOC_ARQ xmlns="urn:infdiario">')
		lines.append("    <CAB_INFORM>")
		lines.append(f"        <COD_DOC>{doc.header.cod_doc}</COD_DOC>")
		lines.append(f"        <DT_COMPT>{doc.header.dt_compt}</DT_COMPT>")
		lines.append(f"        <DT_GERAC_ARQ>{doc.header.dt_gerac_arq}</DT_GERAC_ARQ>")
		lines.append(f"        <VERSAO>{versao}</VERSAO>")
		lines.append("    </CAB_INFORM>")
		for inform in doc.informs:
			lines.extend(self._build_inform_lines(inform))
		lines.append("</DOC_ARQ>")
		return "\n".join(lines)

	def _build_inform_lines(self, inform: InformeDiarioInform) -> list[str]:
		"""Build the XML lines for one INFORM block.

		Parameters
		----------
		inform : InformeDiarioInform
			Validated fund-informe model.

		Returns
		-------
		list[str]
			Ordered XML lines for this informe.
		"""
		ind = "    "  # 4-space base indent inside DOC_ARQ
		inner = f"{ind}    "
		lines: list[str] = [f"{ind}<INFORM>"]
		# Exactly one identifier is present, enforced by the schema.
		if inform.cnpj_fdo is not None:
			lines.append(f"{inner}<CNPJ_FDO>{inform.cnpj_fdo}</CNPJ_FDO>")
		else:
			lines.append(f"{inner}<COD_SUBCLASSE>{inform.cod_subclasse}</COD_SUBCLASSE>")
		lines.append(f"{inner}<DATA_PROX_PL>{inform.data_prox_pl}</DATA_PROX_PL>")
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

	def _build_cotst_lines(
		self, cotistas: list[SignificantShareholder] | None, ind: str
	) -> list[str]:
		"""Build XML lines for the optional LISTA_COTST_SIGNIF block.

		Parameters
		----------
		cotistas : Optional[list[SignificantShareholder]]
			Significant shareholders (>= 20% of PL), or None/empty if absent.
		ind : str
			Base indentation string.

		Returns
		-------
		list[str]
			XML lines, empty if there are no significant shareholders.
		"""
		if not cotistas:
			return []
		lines: list[str] = [f"{ind}    <LISTA_COTST_SIGNIF>"]
		for cotista in cotistas:
			lines += [
				f"{ind}        <COTST_SIGNIF>",
				f"{ind}            <TP_PESSOA>{cotista.tp_pessoa}</TP_PESSOA>",
				f"{ind}            <CPF_CNPJ_COTST>{cotista.cpf_cnpj_cotst}</CPF_CNPJ_COTST>",
				f"{ind}            <PR_COTST>{self._fmt_decimal(cotista.pr_cotst, 4)}</PR_COTST>",
				f"{ind}        </COTST_SIGNIF>",
			]
		lines.append(f"{ind}    </LISTA_COTST_SIGNIF>")
		return lines

	@staticmethod
	def _fmt_decimal(value: Decimal, places: int) -> str:
		"""Format a Decimal for CVM XML output (comma as decimal separator).

		Parameters
		----------
		value : Decimal
			Numeric value.
		places : int
			Number of decimal places.

		Returns
		-------
		str
			Formatted string (e.g. '12,3400').
		"""
		return f"{value:.{places}f}".replace(".", ",")
