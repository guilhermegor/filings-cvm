"""CVM FAR (Demonstrativo de Fontes e Aplicações de Recursos) — submission (envio) writer.

Produces the FAR XML from a validated :class:`FarDocument`. Pure logic plus file I/O at the
edges — no network.
"""

from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.far import FarDocument, FarFund
from filings_cvm._internal.utils.typing import type_checker


_ENCODING = "windows-1252"
_DECLARATION = f'<?xml version="1.0" encoding="{_ENCODING}"?>\n'
_INDENT = "    "


@type_checker
def _add(parent: ET.Element, tag: str, value: Decimal | int | str | None) -> None:
	"""Append ``<tag>value</tag>`` unless the value is ``None``.

	Decimals use the comma separator and keep their 10 places; the page forbids only leading
	zero fillers, which a ``Decimal`` never carries.

	Parameters
	----------
	parent : ET.Element
		The enclosing block.
	tag : str
		The XML tag.
	value : Decimal | int | str | None
		The field value, already validated by the schema.
	"""
	if value is None:
		return
	text = format(value, "f").replace(".", ",") if isinstance(value, Decimal) else str(value)
	ET.SubElement(parent, tag).text = text


@type_checker
def _cnpj_text(value: str) -> str:
	"""Render a validated bare CNPJ as the page states it: digits, no leading zeros.

	Parameters
	----------
	value : str
		The 14-digit CNPJ held by the schema.

	Returns
	-------
	str
		The digits with leading zeros stripped.
	"""
	return value.lstrip("0")


@type_checker
def _append_fund(parent: ET.Element, fund: FarFund) -> None:
	"""Append one ``ROW_REGISTRO_MOVIMENTO`` block.

	Parameters
	----------
	parent : ET.Element
		The ``FAR`` element.
	fund : FarFund
		The fund's report.
	"""
	row = ET.SubElement(parent, "ROW_REGISTRO_MOVIMENTO")
	_add(row, "CNPJ_FUNDO", _cnpj_text(fund.cnpj_fundo))
	_add(row, "NR_QUOTA_CIRCUL_ULT_DIA_MES", fund.nr_quota_circul_ult_dia_mes)
	_add(row, "VL_QUOTA_ULT_DIA_MES", fund.vl_quota_ult_dia_mes)
	_add(row, "NR_TOTAL_QUOTST_ULT_DIA_MES", fund.nr_total_quotst_ult_dia_mes)
	_add(row, "VL_ULT_DISTR_QUOTA", fund.vl_ult_distr_quota)
	_add(row, "DT_DISTR", fund.dt_distr)
	_add(row, "VL_QUOTA_DT_ULT_DISTR", fund.vl_quota_dt_ult_distr)
	movements = ET.SubElement(row, "DOC_MOV_MES")
	for movement in fund.movements:
		line = ET.SubElement(movements, "ROW_MOV_POR_FUNDO")
		_add(line, "CD_MOV", movement.cd_mov)
		_add(line, "VL_ENTR", movement.vl_entr)
		_add(line, "VL_SAIDA", movement.vl_saida)


class Far(SubmissionWriter[FarDocument]):
	"""Serialize a validated FAR document to CVM-compliant XML.

	Concrete :class:`SubmissionWriter` for the FAR XML standard.

	Methods
	-------
	export(doc, output_path)
		Serialize a validated document to windows-1252 XML.
	"""

	def export(self, doc: FarDocument, output_path: str | None = None) -> str | None:
		"""Serialize a validated FarDocument to a CVM-compliant XML string or file.

		The text is encoded and checked for well-formedness **before** the destination is
		opened, so a failure never truncates an existing file.

		Parameters
		----------
		doc : FarDocument
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
			If the document cannot be encoded as windows-1252 XML (only possible when
			validation was bypassed, e.g. ``model_construct``).
		"""
		root = ET.Element("DOC_ARQ")
		header = ET.SubElement(root, "DESC_ADM")
		_add(header, "COD_DOC", doc.header.cod_doc)
		_add(header, "CNPJ_ADM", _cnpj_text(doc.header.cnpj_adm))
		_add(header, "DT_COMPT", doc.header.dt_compt)
		_add(header, "DT_GERAC_ARQ", doc.header.dt_gerac_arq)
		far = ET.SubElement(root, "FAR")
		for fund in doc.funds:
			_append_fund(far, fund)
		ET.indent(root, space=_INDENT)
		xml_str = _DECLARATION + ET.tostring(root, encoding="unicode") + "\n"
		try:
			payload = xml_str.encode(_ENCODING)
			ET.fromstring(payload)  # noqa: S314  # well-formedness self-check of our own output
		except (UnicodeEncodeError, ET.ParseError) as exc:
			raise ValueError(f"document cannot be serialised as {_ENCODING} XML: {exc}") from exc
		if output_path is None:
			return xml_str
		Path(output_path).write_bytes(payload)
		return None
