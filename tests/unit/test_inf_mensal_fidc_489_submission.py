"""Unit tests for the Informe Mensal FIDC (ICVM 489) submission writer.

Expected tags, order, scales and rules come from the CVM page
``PadraoXMLMensalFIDC489.asp``, not from the code under test: the tag sequence is pinned in
``tests/fixtures/inf_mensal_fidc_489/page_tag_sequence.txt`` and ``zero_payload.json`` is an
all-zero document carrying every block the page's template shows.
"""

import copy
import json
from pathlib import Path
import re
from typing import Any

from pydantic import ValidationError
import pytest

from filings_cvm.submission import InfMensalFidc489, InfMensalFidc489Document


FIXTURES = Path(__file__).parents[1] / "fixtures" / "inf_mensal_fidc_489"


def _payload() -> dict[str, Any]:
	"""Load a fresh all-zero payload with every optional block of the template."""
	return json.loads((FIXTURES / "zero_payload.json").read_text())


def _doc(data: dict[str, Any]) -> InfMensalFidc489Document:
	"""Validate a raw payload."""
	return InfMensalFidc489Document.model_validate(data)


def _xml(data: dict[str, Any]) -> str:
	"""Validate a payload and export it to a string."""
	return str(InfMensalFidc489().export(_doc(data)))


def _outras(data: dict[str, Any]) -> dict[str, Any]:
	"""Return the raw OUTRAS_INFORM payload."""
	return data["lista_inform"]["outras_inform"]


def test_full_document_tag_sequence_matches_the_page_template() -> None:
	"""Every tag, in order and flattened, is the page's template sequence."""
	body = _xml(_payload()).split('xmlns="urn:fidc">')[1]
	assert re.findall(r"<(\w+)>", body) == (FIXTURES / "page_tag_sequence.txt").read_text().split()


def test_export_declares_windows_1252_and_the_fidc_namespace() -> None:
	"""The envelope is the page's: encoding declaration and root namespace."""
	assert _xml(_payload()).startswith(
		'<?xml version="1.0" encoding="windows-1252"?>\n<DOC_ARQ xmlns="urn:fidc">'
	)


def test_export_header_has_no_open_fund_redemption_terms() -> None:
	"""CAB_INFORM of this layout carries six tags; PR_ENTRE_* does not exist."""
	assert "PR_ENTRE_RESGATE" not in _xml(_payload())


def test_export_money_uses_comma_and_two_places() -> None:
	"""Monetary fields carry exactly two decimal places."""
	assert "<VL_DISPONIB>0,00</VL_DISPONIB>" in _xml(_payload())


def test_export_quota_quantity_keeps_eight_places_truncated() -> None:
	"""QT_COTAS takes up to 8 places; excess is truncated, not rounded."""
	data = _payload()
	_outras(data)["desc_serie_classe_senior_serie"][0]["qt_cotas"] = "1234.123456789"
	assert "<QT_COTAS>1234,12345678</QT_COTAS>" in _xml(data)


def test_export_captured_total_keeps_two_places_truncated() -> None:
	"""CAPT_MES VL_COTAS is a total: 2 places, 10,99 not rounded to 11,00."""
	data = _payload()
	_outras(data)["capt_mes_senior_serie"][0]["vl_cotas"] = "10.999"
	assert "<VL_COTAS>10,99</VL_COTAS>" in _xml(data)


def test_export_amortised_unit_value_keeps_eight_places() -> None:
	"""AMORT VL_COTA is a unit value: up to 8 places."""
	data = _payload()
	_outras(data)["amort_senior_serie"][0]["vl_cota"] = "0.123456789"
	assert "<VL_COTA>0,12345678</VL_COTA>" in _xml(data)


def test_export_repeats_senior_series_blocks() -> None:
	"""A second senior series repeats the wrapper tag once more."""
	data = _payload()
	series = _outras(data)["desc_serie_classe_senior_serie"]
	series.append(copy.deepcopy(series[0]))
	assert _xml(data).count("<DESC_SERIE_CLASSE_SENIOR_SERIE>") == 2


def test_export_to_file_writes_windows_1252_bytes(tmp_path: Path) -> None:
	"""The file on disk is the string, encoded windows-1252."""
	target = tmp_path / "informe.xml"
	InfMensalFidc489().export(_doc(_payload()), str(target))
	assert target.read_bytes() == _xml(_payload()).encode("windows-1252")


def test_export_to_file_leaves_no_temp_file(tmp_path: Path) -> None:
	"""The atomic write renames its temp file away."""
	InfMensalFidc489().export(_doc(_payload()), str(tmp_path / "informe.xml"))
	assert [p.name for p in tmp_path.iterdir()] == ["informe.xml"]


def test_export_to_file_returns_none(tmp_path: Path) -> None:
	"""Writing to a path returns None, per the port."""
	assert InfMensalFidc489().export(_doc(_payload()), str(tmp_path / "x.xml")) is None


def test_header_rejects_open_fund_redemption_tag() -> None:
	"""PR_ENTRE_RESGATE is a 576 tag; this layout forbids unknown tags."""
	data = _payload()
	data["cab_inform"]["pr_entre_resgate"] = 1
	with pytest.raises(ValidationError):
		_doc(data)


def test_header_rejects_malformed_competence() -> None:
	"""DT_COMPT is MM/AAAA."""
	data = _payload()
	data["cab_inform"]["dt_compt"] = "13/2020"
	with pytest.raises(ValidationError):
		_doc(data)


def test_header_rejects_invalid_fund_cnpj() -> None:
	"""NR_CNPJ_FUNDO must pass the check digits."""
	data = _payload()
	data["cab_inform"]["nr_cnpj_fundo"] = "11222333000182"
	with pytest.raises(ValidationError):
		_doc(data)


def test_item_2_rejects_wrong_carteira_total() -> None:
	"""VL_CARTEIRA must equal the item 2 sum."""
	data = _payload()
	data["lista_inform"]["aplic_ativo"]["vl_carteira"] = "1"
	with pytest.raises(ValidationError, match="item 2"):
		_doc(data)


def test_item_1_rejects_wrong_ativos_total() -> None:
	"""VL_SOM_APLIC_ATIVO must equal the item 1 sum."""
	data = _payload()
	data["lista_inform"]["aplic_ativo"]["vl_som_aplic_ativo"] = "1"
	with pytest.raises(ValidationError, match="item 1"):
		_doc(data)


def test_item_30_rejects_wrong_holders_total() -> None:
	"""QT_TOTAL_COTISTAS must be senior + subordinate."""
	data = _payload()
	_outras(data)["num_cotistas"]["qt_total_cotistas"] = 1
	with pytest.raises(ValidationError, match="item 30"):
		_doc(data)


def test_item_31_rejects_subordinate_total_not_matching_classes() -> None:
	"""QT_TOTAL_COTISTAS_SUBORD must be the sum of the QT_COTISTAS_SUBORD tags."""
	data = _payload()
	_outras(data)["num_cotistas"].update(qt_total_cotistas_subord=5, qt_total_cotistas=5)
	with pytest.raises(ValidationError, match="item 31"):
		_doc(data)


def test_maturity_total_rejects_mismatch_with_portfolio() -> None:
	"""VL_SOM_PRAZO_VENC must match the CRED_EXISTE items the page names."""
	data = _payload()
	data["lista_inform"]["compmt_dicred_aquis"]["vl_som_prazo_venc"] = "1"
	with pytest.raises(ValidationError, match="PRAZO_VENC"):
		_doc(data)


def test_senior_class_is_mandatory() -> None:
	"""Every fund has at least a senior quota, so its series cannot be empty."""
	data = _payload()
	_outras(data)["desc_serie_classe_senior_serie"] = []
	with pytest.raises(ValidationError):
		_doc(data)


def test_open_fund_without_liquidity_is_rejected() -> None:
	"""For an open fund at least one LIQUIDEZ tag must be filled."""
	data = _payload()
	data["cab_inform"]["tp_condominio"] = "ABERTO"
	del _outras(data)["liquidez"]
	with pytest.raises(ValidationError, match="LIQUIDEZ"):
		_doc(data)


def test_open_fund_with_liquidity_is_accepted() -> None:
	"""One filled LIQUIDEZ tag satisfies the open-fund rule."""
	data = _payload()
	data["cab_inform"]["tp_condominio"] = "ABERTO"
	assert _doc(data).cab_inform.tp_condominio == "ABERTO"


def test_closed_fund_may_omit_liquidity() -> None:
	"""LIQUIDEZ is optional for closed funds."""
	data = _payload()
	del _outras(data)["liquidez"]
	assert _doc(data).lista_inform.outras_inform.liquidez is None
