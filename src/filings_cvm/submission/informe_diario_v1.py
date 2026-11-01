"""CVM Informe Diário V1 — submission (envio) writer.

Produces the original ``PadraoXMLInfoDiarioNet`` XML (valid until 2012-07-01) from a
validated :class:`InformeDiarioV1Document`. Pure logic plus file I/O at the edges — no network.
"""

from decimal import Decimal
from itertools import chain
import os
from pathlib import Path
import tempfile

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.informe_diario import SignificantShareholder
from filings_cvm._internal.config.schemas.informe_diario_v1 import (
	InformeDiarioV1Document,
	InformeDiarioV1Header,
	InformeDiarioV1Inform,
)
from filings_cvm._internal.utils.typing import type_checker


_ENCODING = "windows-1252"
_INDENT = "    "


@type_checker
def _fmt_decimal(value: Decimal, places: int) -> str:
	"""Format a Decimal with a comma separator and a fixed number of places.

	Parameters
	----------
	value : Decimal
		Numeric value, already scaled by the schema.
	places : int
		Number of decimal places.

	Returns
	-------
	str
		Formatted string (e.g. ``'12,3400'``).
	"""
	return f"{value:.{places}f}".replace(".", ",")


@type_checker
def _tag(depth: int, name: str, text: str) -> str:
	"""Render one ``<NAME>text</NAME>`` line at the given indent depth.

	Parameters
	----------
	depth : int
		Indent level.
	name : str
		XML tag name.
	text : str
		Element text.

	Returns
	-------
	str
		The XML line.
	"""
	return f"{_INDENT * depth}<{name}>{text}</{name}>"


@type_checker
def _header_lines(header: InformeDiarioV1Header) -> list[str]:
	"""Build the CAB_INFORM block (no VERSAO tag in V1).

	Parameters
	----------
	header : InformeDiarioV1Header
		Validated header.

	Returns
	-------
	list[str]
		XML lines.
	"""
	return [
		f"{_INDENT}<CAB_INFORM>",
		_tag(2, "COD_DOC", str(header.cod_doc)),
		_tag(2, "DT_COMPT", header.dt_compt),
		_tag(2, "DT_GERAC_ARQ", header.dt_gerac_arq),
		f"{_INDENT}</CAB_INFORM>",
	]


@type_checker
def _cotst_lines(cotista: SignificantShareholder) -> list[str]:
	"""Build one COTST_SIGNIF block.

	Parameters
	----------
	cotista : SignificantShareholder
		Shareholder holding 20% or more of the net worth.

	Returns
	-------
	list[str]
		XML lines.
	"""
	return [
		f"{_INDENT * 4}<COTST_SIGNIF>",
		_tag(5, "TP_PESSOA", cotista.tp_pessoa),
		_tag(5, "CPF_CNPJ_COTST", cotista.cpf_cnpj_cotst),
		_tag(5, "PR_COTST", _fmt_decimal(cotista.pr_cotst, 4)),
		f"{_INDENT * 4}</COTST_SIGNIF>",
	]


@type_checker
def _cotst_block(cotistas: list[SignificantShareholder] | None) -> list[str]:
	"""Build the optional LISTA_COTST_SIGNIF block.

	Parameters
	----------
	cotistas : Optional[list[SignificantShareholder]]
		Significant shareholders, or None/empty when absent.

	Returns
	-------
	list[str]
		XML lines; empty when there are no shareholders.
	"""
	if not cotistas:
		return []
	return [
		f"{_INDENT * 3}<LISTA_COTST_SIGNIF>",
		*chain.from_iterable(map(_cotst_lines, cotistas)),
		f"{_INDENT * 3}</LISTA_COTST_SIGNIF>",
	]


@type_checker
def _inform_lines(inform: InformeDiarioV1Inform) -> list[str]:
	"""Build one INFORM block in the page's tag order.

	Parameters
	----------
	inform : InformeDiarioV1Inform
		Validated fund informe.

	Returns
	-------
	list[str]
		XML lines.
	"""
	lines = [
		f"{_INDENT * 2}<INFORM>",
		_tag(3, "CNPJ_FDO", inform.cnpj_fdo),
		_tag(3, "VL_TOTAL", _fmt_decimal(inform.vl_total, 2)),
		_tag(3, "VL_QUOTA", _fmt_decimal(inform.vl_quota, 12)),
		_tag(3, "PATRIM_LIQ", _fmt_decimal(inform.patrim_liq, 2)),
		_tag(3, "CAPTC_DIA", _fmt_decimal(inform.captc_dia, 2)),
		_tag(3, "RESG_DIA", _fmt_decimal(inform.resg_dia, 2)),
		_tag(3, "NR_COTST", str(inform.nr_cotst)),
	]
	return [*lines, *_cotst_block(inform.lista_cotst_signif), f"{_INDENT * 2}</INFORM>"]


@type_checker
def _write_atomic(target: Path, payload: bytes) -> None:
	"""Write bytes through a same-directory temp file and ``os.replace``.

	#330 (``atomic_write_bytes``) will migrate this.

	Parameters
	----------
	target : Path
		Destination file.
	payload : bytes
		Encoded content.
	"""
	fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.")
	try:
		with os.fdopen(fd, "wb") as handle:
			handle.write(payload)
		os.replace(tmp, target)
	except BaseException:
		Path(tmp).unlink(missing_ok=True)
		raise


@type_checker
def _document_text(doc: InformeDiarioV1Document) -> str:
	"""Build the full XML text of a document.

	Parameters
	----------
	doc : InformeDiarioV1Document
		Validated document.

	Returns
	-------
	str
		The XML text.
	"""
	return "\n".join(
		[
			f'<?xml version="1.0" encoding="{_ENCODING}"?>',
			'<DOC_ARQ xmlns="urn:infdiario">',
			*_header_lines(doc.header),
			f"{_INDENT}<LISTA_INFORM>",
			*chain.from_iterable(_inform_lines(inform) for inform in doc.informs),
			f"{_INDENT}</LISTA_INFORM>",
			"</DOC_ARQ>",
		]
	)


@type_checker
def _encode(xml_str: str) -> bytes:
	"""Encode the XML text as windows-1252.

	Parameters
	----------
	xml_str : str
		The XML text.

	Returns
	-------
	bytes
		The encoded payload.

	Raises
	------
	ValueError
		If the text holds characters windows-1252 cannot encode.
	"""
	try:
		return xml_str.encode(_ENCODING)
	except UnicodeEncodeError as exc:
		raise ValueError(f"document cannot be encoded as {_ENCODING}: {exc}") from exc


class InformeDiarioV1(SubmissionWriter[InformeDiarioV1Document]):
	"""Serialize a validated Informe Diário V1 document to CVM-compliant XML.

	Concrete :class:`SubmissionWriter` for the Informe Diário V1 XML standard
	(``PadraoXMLInfoDiarioNet.asp``, valid until 2012-07-01).

	Methods
	-------
	export(doc, output_path)
		Serialize a validated document to windows-1252 XML.
	"""

	def export(self, doc: InformeDiarioV1Document, output_path: str | None = None) -> str | None:
		"""Serialize a validated InformeDiarioV1Document to XML text or a file.

		The text is encoded **before** the destination is opened, so a failure never
		truncates an existing file.

		Parameters
		----------
		doc : InformeDiarioV1Document
			Fully validated document model.
		output_path : Optional[str]
			Destination file, written in windows-1252; when given ``None`` is returned,
			by default None.

		Returns
		-------
		Optional[str]
			The XML text when ``output_path`` is None, else None.

		Raises
		------
		ValueError
			If the document holds text windows-1252 cannot encode (only possible when
			validation was bypassed).
		"""
		xml_str = _document_text(doc)
		payload = _encode(xml_str)
		if output_path is None:
			return xml_str
		_write_atomic(Path(output_path), payload)
		return None
