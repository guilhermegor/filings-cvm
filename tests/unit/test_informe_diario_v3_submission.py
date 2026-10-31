"""Unit tests for the Informe Diário V3 submission writer.

Pin the tag order and decimal scales to PadraoXMLInfoDiarioNetV3.asp and cover the
V3-only rules (VERSAO 3.0, CNPJ_FDO only).
"""

from pathlib import Path
import re

from pydantic import ValidationError
import pytest

from filings_cvm.submission import (
	InformeDiarioV3,
	InformeDiarioV3Document,
	InformeDiarioV3Header,
	InformeDiarioV3Inform,
	SignificantShareholder,
)


VALID_CNPJ = "11222333000181"
PAGE_ORDER = [
	"CNPJ_FDO",
	"DATA_PROX_PL",
	"VL_TOTAL",
	"VL_QUOTA",
	"PATRIM_LIQ",
	"CAPTC_DIA",
	"RESG_DIA",
	"VL_TOTAL_SAI",
	"VL_TOTAL_ATV",
	"NR_COTST",
	"LISTA_COTST_SIGNIF",
]


def _inform(**overrides: object) -> InformeDiarioV3Inform:
	fields: dict[str, object] = {
		"cnpj_fdo": VALID_CNPJ,
		"data_prox_pl": "16/01/2025",
		"vl_total": "1.239",
		"vl_quota": "1.1234567890129",
		"patrim_liq": "2",
		"captc_dia": "3",
		"resg_dia": "4",
		"vl_total_sai": "5",
		"vl_total_atv": "6",
		"nr_cotst": 7,
		"lista_cotst_signif": [
			SignificantShareholder(tp_pessoa="PJ", cpf_cnpj_cotst=VALID_CNPJ, pr_cotst="20.12345")
		],
	}
	fields.update(overrides)
	return InformeDiarioV3Inform(**fields)


def _xml(inform: InformeDiarioV3Inform | None = None) -> str:
	header = InformeDiarioV3Header(dt_compt="15/01/2025", dt_gerac_arq="15/01/2025")
	doc = InformeDiarioV3Document(header=header, informs=[inform or _inform()])
	xml = InformeDiarioV3().export(doc)
	assert xml is not None
	return xml


def test_versao_is_3_0() -> None:
	"""Stamp VERSAO 3.0 and COD_DOC 1 in the header."""
	xml = _xml()

	assert "<VERSAO>3.0</VERSAO>" in xml
	assert "<COD_DOC>1</COD_DOC>" in xml


def test_inform_tag_order_matches_page() -> None:
	"""Emit the INFORM children in the order the page template lists them."""
	xml = _xml()
	body = xml.split("<INFORM>")[1].split("</INFORM>")[0]
	top_level = re.findall(r"^ {8}<([A-Z_]+)>", body, flags=re.M)

	assert top_level == PAGE_ORDER


def test_decimal_scales_follow_page() -> None:
	"""Truncate to 2 places (money), 12 (quota) and 4 (participation)."""
	xml = _xml()

	assert "<VL_TOTAL>1,23</VL_TOTAL>" in xml
	assert "<VL_QUOTA>1,123456789012</VL_QUOTA>" in xml
	assert "<PR_COTST>20,1234</PR_COTST>" in xml


def test_no_subclasse_tag_is_emitted() -> None:
	"""Never emit COD_SUBCLASSE, which V3 lacks."""
	assert "COD_SUBCLASSE" not in _xml()


def test_cod_subclasse_is_rejected() -> None:
	"""Reject a subclass code because V3 only knows CNPJ_FDO."""
	with pytest.raises(ValidationError):
		_inform(cod_subclasse="X1")


def test_cnpj_is_required() -> None:
	"""Reject an informe without CNPJ_FDO."""
	with pytest.raises(ValidationError):
		_inform(cnpj_fdo=None)


def test_invalid_cnpj_check_digit_is_rejected() -> None:
	"""Reject a CNPJ whose check digits are wrong."""
	with pytest.raises(ValidationError):
		_inform(cnpj_fdo="11222333000182")


def test_header_rejects_other_versao() -> None:
	"""Reject a header claiming another VERSAO."""
	with pytest.raises(ValidationError):
		InformeDiarioV3Header(dt_compt="15/01/2025", dt_gerac_arq="15/01/2025", versao="4.0")


def test_more_than_100_funds_rejected() -> None:
	"""Reject a document with more than 100 informes."""
	header = InformeDiarioV3Header(dt_compt="15/01/2025", dt_gerac_arq="15/01/2025")
	with pytest.raises(ValidationError):
		InformeDiarioV3Document(header=header, informs=[_inform()] * 101)


def test_export_writes_windows_1252_file(tmp_path: Path) -> None:
	"""Write the file as windows-1252 and return None."""
	header = InformeDiarioV3Header(dt_compt="15/01/2025", dt_gerac_arq="15/01/2025")
	doc = InformeDiarioV3Document(header=header, informs=[_inform()])
	out = tmp_path / "informe.xml"

	assert InformeDiarioV3().export(doc, output_path=str(out)) is None
	assert (
		out.read_bytes()
		.decode("windows-1252")
		.startswith('<?xml version="1.0" encoding="windows-1252"?>')
	)
