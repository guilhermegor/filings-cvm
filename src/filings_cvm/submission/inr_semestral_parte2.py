"""CVM Informe Semestral de Investidor Nao Residente, Parte II — submission (envio) writer.

Serialises a validated :class:`InrParte2Document` (``COD_DOC`` 70, applications) to the CVM XML.
The asset blocks are emitted in the order the standard requires: ``TIT_PUB``, ``COTAS``,
``SWAP`` (+ ``NOCION_SWAP``), ``DEMAIS_CODIF``, ``DEP_PRAZO_TIT_IF``, ``TIT_AGRO_CRED_PRIV``,
``INV_EXT``, ``DEMAIS_N_CODIF``. Pure logic plus file I/O at the edges, no network.
"""

from collections.abc import Callable, Sequence
from decimal import Decimal
from typing import Any
import xml.etree.ElementTree as ET

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.inr_semestral import (
	InrAtivoExterior,
	InrClassifRisco,
	InrCotas,
	InrDemaisCodif,
	InrDemaisNCodif,
	InrDepPrazoTitIf,
	InrEmissorPfPj,
	InrIndexador,
	InrInform,
	InrInvExt,
	InrParte2Document,
	InrPosFim,
	InrSwap,
	InrTitAgroCredPriv,
	InrTitPub,
)
from filings_cvm._internal.utils.inr_semestral_fields import finish_xml, format_decimal
from filings_cvm._internal.utils.typing import type_checker


_NAMESPACE = "urn:cda"
_QTY_PLACES = 6
_MONEY_PLACES = 2
_RATE_PLACES = 6


@type_checker
def _leaf(parent: ET.Element, tag: str, value: object) -> None:
	"""Append ``<tag>value</tag>``, rendering a ``Decimal`` with the comma separator.

	Parameters
	----------
	parent : ET.Element
		Element to append to.
	tag : str
		Tag name.
	value : object
		A string, integer or already-scaled ``Decimal`` (money scale when it is one).
	"""
	text = format_decimal(value, _MONEY_PLACES) if isinstance(value, Decimal) else str(value)
	ET.SubElement(parent, tag).text = text


@type_checker
def _decimal(parent: ET.Element, tag: str, value: Decimal, places: int) -> None:
	"""Append a decimal leaf at an explicit scale.

	Parameters
	----------
	parent : ET.Element
		Element to append to.
	tag : str
		Tag name.
	value : Decimal
		The value.
	places : int
		Decimal places to render.
	"""
	ET.SubElement(parent, tag).text = format_decimal(value, places)


@type_checker
def _leaf_opt(parent: ET.Element, tag: str, value: object) -> None:
	"""Append ``<tag>value</tag>`` unless ``value`` is ``None``.

	Parameters
	----------
	parent : ET.Element
		Element to append to.
	tag : str
		Tag name.
	value : object
		The optional value.
	"""
	if value is not None:
		_leaf(parent, tag, value)


@type_checker
def _decimal_opt(parent: ET.Element, tag: str, value: Decimal | None, places: int) -> None:
	"""Append a decimal leaf unless ``value`` is ``None``.

	Parameters
	----------
	parent : ET.Element
		Element to append to.
	tag : str
		Tag name.
	value : Decimal or None
		The optional value.
	places : int
		Decimal places to render.
	"""
	if value is not None:
		_decimal(parent, tag, value, places)


@type_checker
def _pos_fim(parent: ET.Element, qtde: Decimal | None, merc: Decimal) -> ET.Element:
	"""Append ``POS_FIM`` with its optional quantity and market value.

	Parameters
	----------
	parent : ET.Element
		The ``APLIC`` element.
	qtde : Decimal or None
		``QTDE_POS_FIM``.
	merc : Decimal
		``MERC_POS_FIM``.

	Returns
	-------
	ET.Element
		The ``POS_FIM`` element, so a caller can add a notional.
	"""
	end = ET.SubElement(parent, "POS_FIM")
	_decimal_opt(end, "QTDE_POS_FIM", qtde, _QTY_PLACES)
	_decimal(end, "MERC_POS_FIM", merc, _MONEY_PLACES)
	return end


@type_checker
def _aplic(parent: ET.Element, cod_tp_aplic: str | None, pos: InrPosFim) -> None:
	"""Append ``APLIC`` with its optional type code and ``POS_FIM``.

	Parameters
	----------
	parent : ET.Element
		The asset block element.
	cod_tp_aplic : str or None
		The application type; ``None`` when the block implies it (197, 74, 189).
	pos : InrPosFim
		The final position (a notional is rendered when the model carries one).
	"""
	node = ET.SubElement(parent, "APLIC")
	_leaf_opt(node, "COD_TP_APLIC", cod_tp_aplic)
	end = _pos_fim(node, pos.qtde_pos_fim, pos.merc_pos_fim)
	_decimal_opt(end, "NOCION_POS_FIM", getattr(pos, "nocion_pos_fim", None), _MONEY_PLACES)


@type_checker
def _rating(parent: ET.Element, st: str, rating: InrClassifRisco | None) -> None:
	"""Append ``ST_CLASSIF_RISCO`` and, when rated, ``CLASSIF_RISCO``.

	Parameters
	----------
	parent : ET.Element
		The asset block element.
	st : str
		``"S"`` or ``"N"``.
	rating : InrClassifRisco or None
		The rating block.
	"""
	_leaf(parent, "ST_CLASSIF_RISCO", st)
	if rating is None:
		return
	node = ET.SubElement(parent, "CLASSIF_RISCO")
	_leaf(node, "AG_CLASSIF_RISCO", rating.ag_classif_risco)
	_leaf(node, "DT_CLASSIF_RISCO", rating.dt_classif_risco)
	_leaf(node, "GRAU_CLASSIF_RISCO", rating.grau_classif_risco)


@type_checker
def _indexation(
	parent: ET.Element, st: str, index: InrIndexador | None, rate: Decimal | None
) -> None:
	"""Append the post-fixed / pre-fixed fields.

	Parameters
	----------
	parent : ET.Element
		The asset block element.
	st : str
		``ST_TIT_POS_FIX`` value.
	index : InrIndexador or None
		The indexer block (post-fixed).
	rate : Decimal or None
		The contracted rate (pre-fixed).
	"""
	_leaf(parent, "ST_TIT_POS_FIX", st)
	if index is not None:
		node = ET.SubElement(parent, "TIT_POS_FIX_INDEX")
		_leaf(node, "TIT_POS_FIX_COD_INDEX", index.tit_pos_fix_cod_index)
		_decimal(node, "TIT_POS_FIX_PR_INDEX", index.tit_pos_fix_pr_index, _RATE_PLACES)
		_decimal(node, "TIT_POS_FIX_CUPOM", index.tit_pos_fix_cupom, _RATE_PLACES)
	_decimal_opt(parent, "TIT_PRE_FIX_TAXA_CONTR", rate, _RATE_PLACES)


@type_checker
def _issuer_pf_pj(parent: ET.Element, issuer: InrEmissorPfPj) -> None:
	"""Append an ``EMIS`` block identified by person type and document.

	Parameters
	----------
	parent : ET.Element
		The asset block element.
	issuer : InrEmissorPfPj
		The issuer model.
	"""
	node = ET.SubElement(parent, "EMIS")
	_leaf(node, "TP_PF_PJ_EMIS", issuer.tp_pf_pj_emis)
	_leaf(node, "NR_PF_PJ_EMIS", issuer.nr_pf_pj_emis)
	_leaf(node, "NM_EMIS", issuer.nm_emis)


@type_checker
def _tit_pub(parent: ET.Element, item: InrTitPub) -> None:
	"""Append one ``TIT_PUB`` block.

	Parameters
	----------
	parent : ET.Element
		``LISTA_ATIV`` element.
	item : InrTitPub
		The block model.
	"""
	node = ET.SubElement(parent, "TIT_PUB")
	_leaf(node, "COD_SELIC", item.cod_selic)
	_leaf(node, "DT_VENC", item.dt_venc)
	_aplic(node, item.cod_tp_aplic, item.pos_fim)


@type_checker
def _cotas(parent: ET.Element, item: InrCotas) -> None:
	"""Append one ``COTAS`` block.

	Parameters
	----------
	parent : ET.Element
		``LISTA_ATIV`` element.
	item : InrCotas
		The block model.
	"""
	node = ET.SubElement(parent, "COTAS")
	_leaf(node, "CNPJ_FDO", item.cnpj_fdo)
	_aplic(node, None, item.pos_fim)


@type_checker
def _swap(parent: ET.Element, item: InrSwap) -> None:
	"""Append one ``SWAP`` block.

	Parameters
	----------
	parent : ET.Element
		``LISTA_ATIV`` element.
	item : InrSwap
		The block model.
	"""
	node = ET.SubElement(parent, "SWAP")
	_leaf(node, "COD_SWAP", item.cod_swap)
	_aplic(node, item.cod_tp_aplic, item.pos_fim)


@type_checker
def _demais_codif(parent: ET.Element, item: InrDemaisCodif) -> None:
	"""Append one ``DEMAIS_CODIF`` block.

	Parameters
	----------
	parent : ET.Element
		``LISTA_ATIV`` element.
	item : InrDemaisCodif
		The block model.
	"""
	node = ET.SubElement(parent, "DEMAIS_CODIF")
	_leaf(node, "COD_ATIV", item.cod_ativ)
	_leaf(node, "COD_TP_ATIV", item.cod_tp_ativ)
	_leaf(node, "DT_INI_VIGEN", item.dt_ini_vigen)
	_aplic(node, item.cod_tp_aplic, item.pos_fim)


@type_checker
def _dep_prazo(parent: ET.Element, item: InrDepPrazoTitIf) -> None:
	"""Append one ``DEP_PRAZO_TIT_IF`` block.

	Parameters
	----------
	parent : ET.Element
		``LISTA_ATIV`` element.
	item : InrDepPrazoTitIf
		The block model.
	"""
	node = ET.SubElement(parent, "DEP_PRAZO_TIT_IF")
	_leaf(node, "COD_TP_ATIV", item.cod_tp_ativ)
	issuer = ET.SubElement(node, "EMIS")
	_leaf(issuer, "CNPJ_EMIS", item.emis.cnpj_emis)
	_leaf(issuer, "NM_EMIS", item.emis.nm_emis)
	_leaf(node, "DT_VENC", item.dt_venc)
	_indexation(node, item.st_tit_pos_fix, item.tit_pos_fix_index, item.tit_pre_fix_taxa_contr)
	_rating(node, item.st_classif_risco, item.classif_risco)
	_aplic(node, None, item.pos_fim)


@type_checker
def _tit_agro(parent: ET.Element, item: InrTitAgroCredPriv) -> None:
	"""Append one ``TIT_AGRO_CRED_PRIV`` block.

	Parameters
	----------
	parent : ET.Element
		``LISTA_ATIV`` element.
	item : InrTitAgroCredPriv
		The block model.
	"""
	node = ET.SubElement(parent, "TIT_AGRO_CRED_PRIV")
	_leaf(node, "COD_TP_ATIV", item.cod_tp_ativ)
	_issuer_pf_pj(node, item.emis)
	_leaf(node, "DT_VENC", item.dt_venc)
	_indexation(node, item.st_tit_pos_fix, item.tit_pos_fix_index, item.tit_pre_fix_taxa_contr)
	_leaf(node, "ST_TIT_REG_CETIP", item.st_tit_reg_cetip)
	_leaf(node, "ST_TIT_GARANT_SEGURO", item.st_tit_garant_seguro)
	_leaf_opt(node, "CNPJ_INSTIT_FINANC", item.cnpj_instit_financ)
	_aplic(node, item.cod_tp_aplic, item.pos_fim)


@type_checker
def _ativo_ext(aplic: ET.Element, asset: InrAtivoExterior | None) -> None:
	"""Append the optional ``ATIVO_EXT`` block.

	Parameters
	----------
	aplic : ET.Element
		The ``APLIC`` element.
	asset : InrAtivoExterior or None
		The foreign-asset model.
	"""
	if asset is None:
		return
	ext = ET.SubElement(aplic, "ATIVO_EXT")
	_leaf(ext, "DESC_AT_EXT", asset.desc_at_ext)
	_leaf(ext, "QTDE_AT_EXT", asset.qtde_at_ext)
	_decimal(ext, "VALOR_AT_EXT", asset.valor_at_ext, _MONEY_PLACES)


@type_checker
def _inv_ext(parent: ET.Element, item: InrInvExt) -> None:
	"""Append one ``INV_EXT`` block.

	Parameters
	----------
	parent : ET.Element
		``LISTA_ATIV`` element.
	item : InrInvExt
		The block model.
	"""
	node = ET.SubElement(parent, "INV_EXT")
	_leaf(node, "COD_TP_ATIV", item.cod_tp_ativ)
	_leaf(node, "INV_COLETIVO", item.inv_coletivo)
	_leaf(node, "GEST_INV_COLETIVO", item.gest_inv_coletivo)
	_leaf(node, "NM_EMIS", item.nm_emis)
	_leaf_opt(node, "DT_VENC", item.dt_venc)
	_leaf(node, "COD_PAIS", item.cod_pais)
	_leaf(node, "COD_BV_MERC", item.cod_bv_merc)
	_leaf(node, "COD_ATIVO_BV_MERC", item.cod_ativo_bv_merc)
	_rating(node, item.st_classif_risco, item.classif_risco)
	aplic = ET.SubElement(node, "APLIC")
	_leaf(aplic, "DT_APLIC", item.dt_aplic)
	_pos_fim(aplic, item.pos_fim.qtde_pos_fim, item.pos_fim.merc_pos_fim)
	_ativo_ext(aplic, item.ativo_ext)


@type_checker
def _demais_n_codif(parent: ET.Element, item: InrDemaisNCodif) -> None:
	"""Append one ``DEMAIS_N_CODIF`` block.

	Parameters
	----------
	parent : ET.Element
		``LISTA_ATIV`` element.
	item : InrDemaisNCodif
		The block model.
	"""
	node = ET.SubElement(parent, "DEMAIS_N_CODIF")
	_leaf(node, "COD_TP_ATIV", item.cod_tp_ativ)
	_leaf(node, "DESC", item.desc)
	_issuer_pf_pj(node, item.emis)
	_aplic(node, item.cod_tp_aplic, item.pos_fim)


@type_checker
def _each(
	parent: ET.Element, items: Sequence[object], emit: Callable[[ET.Element, Any], None]
) -> None:
	"""Emit every item of one asset block with ``emit``.

	Parameters
	----------
	parent : ET.Element
		``LISTA_ATIV`` element.
	items : Sequence[object]
		The block models.
	emit : Callable
		Writer of one item.
	"""
	for item in items:
		emit(parent, item)


@type_checker
def _inform(parent: ET.Element, inform: InrInform) -> None:
	"""Append one ``INFORM`` with its blocks in the order the standard requires.

	Parameters
	----------
	parent : ET.Element
		``LISTA_INFORM`` element.
	inform : InrInform
		The participant model.
	"""
	node = ET.SubElement(parent, "INFORM")
	_leaf(node, "COD_PARTIC", inform.cod_partic)
	assets = ET.SubElement(node, "LISTA_ATIV")
	_each(assets, inform.tit_pub, _tit_pub)
	_each(assets, inform.cotas, _cotas)
	_each(assets, inform.swap, _swap)
	_decimal_opt(assets, "NOCION_SWAP", inform.nocion_swap, _MONEY_PLACES)
	_each(assets, inform.demais_codif, _demais_codif)
	_each(assets, inform.dep_prazo_tit_if, _dep_prazo)
	_each(assets, inform.tit_agro_cred_priv, _tit_agro)
	_each(assets, inform.inv_ext, _inv_ext)
	_each(assets, inform.demais_n_codif, _demais_n_codif)


class InrSemestralParte2(SubmissionWriter[InrParte2Document]):
	"""Serialise a validated Informe Semestral de INR Parte II document to CVM XML.

	Methods
	-------
	export(doc, output_path)
		Return the XML string, or write it (windows-1252) to ``output_path``.
	"""

	def export(self, doc: InrParte2Document, output_path: str | None = None) -> str | None:
		"""Serialise ``doc`` to the CVM Parte II XML.

		Parameters
		----------
		doc : InrParte2Document
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
		_leaf(head, "DT_COMPT", doc.header.dt_compt)
		_leaf(head, "DT_GERAC_ARQ", doc.header.dt_gerac_arq)
		listing = ET.SubElement(root, "LISTA_INFORM")
		for inform in doc.informs:
			_inform(listing, inform)
		return finish_xml(root, output_path)
