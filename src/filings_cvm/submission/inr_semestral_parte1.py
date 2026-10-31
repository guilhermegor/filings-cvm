"""CVM Informe Semestral de Investidor Nao Residente, Parte I — submission (envio) writer.

Serialises a validated :class:`InrParte1Document` (``COD_DOC`` 69, resource flows) to the CVM XML.
Parte II is a separate file of the same standard, sent together with this one; see
:class:`~filings_cvm.submission.inr_semestral_parte2.InrSemestralParte2`. Pure logic plus file
I/O at the edges, no network.
"""

import xml.etree.ElementTree as ET

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.inr_semestral import (
	InrParte1Document,
	InrParticipante,
	InrRecursosEntreInvestidores,
)
from filings_cvm._internal.utils.inr_semestral_fields import write_xml_file
from filings_cvm._internal.utils.typing import type_checker


_XML_DECLARATION = '<?xml version="1.0" encoding="windows-1252"?>\n'
# The page states "urn:infmensal" for this file as well; kept verbatim from the spec.
_NAMESPACE = "urn:infmensal"


@type_checker
def _leaf(parent: ET.Element, tag: str, value: object) -> None:
	"""Append ``<tag>value</tag>`` to ``parent``.

	Parameters
	----------
	parent : ET.Element
		Element to append to.
	tag : str
		Tag name.
	value : object
		Value rendered with ``str``.
	"""
	ET.SubElement(parent, tag).text = str(value)


@type_checker
def _exchange(parent: ET.Element, tag: str, block: InrRecursosEntreInvestidores | None) -> None:
	"""Append an optional ``RECURSOS_*_INVEST`` block, omitted when it carries nothing.

	Parameters
	----------
	parent : ET.Element
		``MOV_RECURSOS`` element.
	tag : str
		``RECURSOS_MESMO_INVEST`` or ``RECURSOS_OUTRO_INVEST``.
	block : InrRecursosEntreInvestidores or None
		The block model.
	"""
	if block is None or not (block.recebidos or block.enviados):
		return
	suffix = tag.removeprefix("RECURSOS_")
	root = ET.SubElement(parent, tag)
	for item in block.recebidos:
		node = ET.SubElement(root, f"RECURSOS_RECEB_{suffix}")
		_leaf(node, "CD_PARTIC_ORIGEM", item.cd_partic_origem)
		_leaf(node, "VL_RECEBIDO", item.vl_recebido)
	for sent in block.enviados:
		node = ET.SubElement(root, f"RECURSOS_ENV_{suffix}")
		_leaf(node, "CD_PARTIC_DEST", sent.cd_partic_dest)
		_leaf(node, "VL_ENVIADO", sent.vl_enviado)


@type_checker
def _participant(parent: ET.Element, part: InrParticipante) -> None:
	"""Append one ``PARTICIPANTE`` block.

	Parameters
	----------
	parent : ET.Element
		``LISTA_PARTICIPANTES`` element.
	part : InrParticipante
		The participant model.
	"""
	node = ET.SubElement(parent, "PARTICIPANTE")
	_leaf(node, "COD_PARTIC", part.cod_partic)
	flow = ET.SubElement(node, "ENTRADA_SAIDA")
	_leaf(flow, "VL_ENTR", part.entrada_saida.vl_entr)
	_leaf(flow, "VL_SAIDA", part.entrada_saida.vl_saida)
	moves = ET.SubElement(node, "MOV_RECURSOS")
	transfers = ET.SubElement(moves, "TRANSF_RECURSOS")
	for tag, value in (
		("VL_INVEST_CARTEIRA_HAVER_NRES", part.transf_recursos.vl_invest_carteira_haver_nres),
		("VL_HAVER_NRES_INVEST_CARTEIRA", part.transf_recursos.vl_haver_nres_invest_carteira),
		("VL_INVEST_CARTEIRA_ADR", part.transf_recursos.vl_invest_carteira_adr),
		("VL_ADR_INVEST_CARTEIRA", part.transf_recursos.vl_adr_invest_carteira),
		(
			"VL_INVEST_CARTEIRA_ESTRANG_DIRETA",
			part.transf_recursos.vl_invest_carteira_estrang_direta,
		),
		(
			"VL_ESTRANG_DIRETA_INVEST_CARTEIRA",
			part.transf_recursos.vl_estrang_direta_invest_carteira,
		),
	):
		_leaf(transfers, tag, value)
	_exchange(moves, "RECURSOS_MESMO_INVEST", part.recursos_mesmo_invest)
	_exchange(moves, "RECURSOS_OUTRO_INVEST", part.recursos_outro_invest)
	_leaf(node, "PATRIM_LIQ", part.patrim_liq)


class InrSemestralParte1(SubmissionWriter[InrParte1Document]):
	"""Serialise a validated Informe Semestral de INR Parte I document to CVM XML.

	Methods
	-------
	export(doc, output_path)
		Return the XML string, or write it (windows-1252) to ``output_path``.
	"""

	def export(self, doc: InrParte1Document, output_path: str | None = None) -> str | None:
		"""Serialise ``doc`` to the CVM Parte I XML.

		Parameters
		----------
		doc : InrParte1Document
			Fully validated document.
		output_path : str, optional
			Destination file. The text is encoded before the file is opened, so a failure
			never truncates an existing file. By default ``None``.

		Returns
		-------
		str or None
			The XML when ``output_path`` is ``None``, else ``None``.
		"""
		root = ET.Element("DOC_ARQ", {"xmlns": _NAMESPACE})
		head = ET.SubElement(root, "CAB_INFORM")
		_leaf(head, "COD_DOC", doc.header.cod_doc)
		_leaf(head, "VERSAO", doc.header.versao)
		_leaf(head, "CD_CVM", doc.header.cd_cvm)
		_leaf(head, "DT_COMPT", doc.header.dt_compt)
		_leaf(head, "DT_GERAC_ARQ", doc.header.dt_gerac_arq)
		listing = ET.SubElement(root, "LISTA_PARTICIPANTES")
		for part in doc.participantes:
			_participant(listing, part)
		ET.indent(root, space="    ")
		xml_str = _XML_DECLARATION + ET.tostring(
			root, encoding="unicode", short_empty_elements=False
		)
		if output_path is None:
			return xml_str
		write_xml_file(output_path, xml_str)
		return None
