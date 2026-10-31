"""CVM Informe Art. 12 Res. CVM 33 (escriturador) — submission (envio) writer.

Produces the ``urn:prestserv`` XML (``COD_ARQ`` 29) from a validated :class:`PrestDocument`.
Pure logic plus file I/O at the edges — no network.
"""

from pathlib import Path
from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.informe_art12_res33 import (
	PrestAtivo,
	PrestDocument,
	PrestEmissor,
	PrestInform,
)
from filings_cvm._internal.utils.typing import type_checker


_NAMESPACE = "urn:prestserv"
_COD_ARQ = "29"
_ENCODING = "windows-1252"
_DECLARATION = f'<?xml version="1.0" encoding="{_ENCODING}"?>\n'
_INDENT = "    "


@type_checker
def _leaf(parent: ET.Element, tag: str, text: str) -> None:
	"""Append ``<tag>text</tag>`` to ``parent``.

	Parameters
	----------
	parent : ET.Element
		The enclosing block.
	tag : str
		Element name.
	text : str
		Element text.
	"""
	ET.SubElement(parent, tag).text = text


@type_checker
def _ativo(parent: ET.Element, ativo: PrestAtivo) -> None:
	"""Append one ATIVO block (DT_FIM_CONTRATO only when the contract ended).

	Parameters
	----------
	parent : ET.Element
		The enclosing EMISSOR.
	ativo : PrestAtivo
		The asset block.
	"""
	block = ET.SubElement(parent, "ATIVO")
	_leaf(block, "ATIVO_ESCRITURADO", ativo.ativo_escriturado)
	_leaf(block, "DT_INICIO_CONTRATO", ativo.dt_inicio_contrato)
	if ativo.dt_fim_contrato is not None:
		_leaf(block, "DT_FIM_CONTRATO", ativo.dt_fim_contrato)


@type_checker
def _emissor(parent: ET.Element, emissor: PrestEmissor) -> None:
	"""Append one EMISSOR block with its ATIVO children.

	Parameters
	----------
	parent : ET.Element
		The enclosing LISTA_EMISSORES.
	emissor : PrestEmissor
		The issuer block.
	"""
	block = ET.SubElement(parent, "EMISSOR")
	_leaf(block, "CNPJ_EMISSOR", emissor.cnpj_emissor)
	for ativo in emissor.ativos:
		_ativo(block, ativo)


@type_checker
def _inform(parent: ET.Element, inform: PrestInform) -> None:
	"""Append one INFORM_PREST block (DS_PREST + LISTA_EMISSORES).

	Parameters
	----------
	parent : ET.Element
		The enclosing LISTA_PREST.
	inform : PrestInform
		The provider block.
	"""
	block = ET.SubElement(parent, "INFORM_PREST")
	dados = ET.SubElement(block, "DS_PREST")
	_leaf(dados, "CNPJ_ESCRITURADOR", inform.ds_prest.cnpj_escriturador)
	_leaf(dados, "CD_TP_PREST", str(inform.ds_prest.cd_tp_prest))
	emissores = ET.SubElement(block, "LISTA_EMISSORES")
	for emissor in inform.emissores:
		_emissor(emissores, emissor)


class InformeArt12Res33(SubmissionWriter[PrestDocument]):
	"""Serialize a validated Informe Art. 12 Res. CVM 33 document to CVM-compliant XML.

	Methods
	-------
	export(doc, output_path)
		Serialize a validated document to windows-1252 XML.
	"""

	def export(self, doc: PrestDocument, output_path: str | None = None) -> str | None:
		"""Serialize a validated PrestDocument to a CVM-compliant XML string or file.

		The text is encoded and checked for well-formedness **before** the destination is
		opened, so a failure never truncates an existing file.

		Parameters
		----------
		doc : PrestDocument
			Fully validated document model.
		output_path : Optional[str]
			Destination file, written in windows-1252 (``None`` is then returned); otherwise
			the XML string is returned, by default None.

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
		root = ET.Element("DOC_ARQ", {"xmlns": _NAMESPACE})
		_leaf(root, "COD_ARQ", _COD_ARQ)
		header = ET.SubElement(root, "DS_INFORM")
		_leaf(header, "DT_COMPT", doc.ds_inform.dt_compt)
		_leaf(header, "DT_GERAC_ARQ", doc.ds_inform.dt_gerac_arq)
		lista = ET.SubElement(root, "LISTA_PREST")
		for inform in doc.prestadores:
			_inform(lista, inform)
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
