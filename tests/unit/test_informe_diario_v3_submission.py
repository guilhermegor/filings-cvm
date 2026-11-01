"""Unit tests for the Informe Diário V3 submission writer.

Pin the tag order and decimal scales to PadraoXMLInfoDiarioNetV3.asp and cover the
V3-only rules (VERSAO 3.0, CNPJ_FDO only).
"""

from pathlib import Path
import re

from pydantic import ValidationError
import pytest

from filings_cvm.submission import (
	InformeDiario,
	InformeDiarioDocument,
	InformeDiarioHeader,
	InformeDiarioInform,
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


@pytest.mark.parametrize("tag", ["<VERSAO>3.0</VERSAO>", "<COD_DOC>1</COD_DOC>"])
def test_header_stamps_v3_version_and_doc_code(tag: str) -> None:
	"""Stamp VERSAO 3.0 and COD_DOC 1 in the header."""
	assert tag in _xml()


def test_inform_tag_order_matches_page() -> None:
	"""Emit the INFORM children in the order the page template lists them."""
	xml = _xml()
	body = xml.split("<INFORM>")[1].split("</INFORM>")[0]
	top_level = re.findall(r"^ {8}<([A-Z_]+)>", body, flags=re.M)

	assert top_level == PAGE_ORDER


@pytest.mark.parametrize(
	"tag",
	[
		"<VL_TOTAL>1,23</VL_TOTAL>",
		"<VL_QUOTA>1,123456789012</VL_QUOTA>",
		"<PR_COTST>20,1234</PR_COTST>",
	],
)
def test_decimal_scales_follow_page(tag: str) -> None:
	"""Truncate to 2 places (money), 12 (quota) and 4 (participation)."""
	assert tag in _xml()


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


def test_header_rejects_other_cod_doc() -> None:
	"""Reject a header claiming another COD_DOC."""
	with pytest.raises(ValidationError):
		InformeDiarioV3Header(dt_compt="15/01/2025", dt_gerac_arq="15/01/2025", cod_doc=2)


def test_more_than_100_funds_rejected() -> None:
	"""Reject a document with more than 100 informes."""
	header = InformeDiarioV3Header(dt_compt="15/01/2025", dt_gerac_arq="15/01/2025")
	with pytest.raises(ValidationError):
		InformeDiarioV3Document(header=header, informs=[_inform()] * 101)


def _doc() -> InformeDiarioV3Document:
	header = InformeDiarioV3Header(dt_compt="15/01/2025", dt_gerac_arq="15/01/2025")
	return InformeDiarioV3Document(header=header, informs=[_inform()])


def test_export_to_file_returns_none(tmp_path: Path) -> None:
	"""Return None when an output path is given."""
	assert InformeDiarioV3().export(_doc(), output_path=str(tmp_path / "informe.xml")) is None


def test_export_writes_windows_1252_file(tmp_path: Path) -> None:
	"""Write the file as windows-1252."""
	out = tmp_path / "informe.xml"
	InformeDiarioV3().export(_doc(), output_path=str(out))
	assert (
		out.read_bytes()
		.decode("windows-1252")
		.startswith('<?xml version="1.0" encoding="windows-1252"?>')
	)


def test_export_pins_versao_even_if_header_is_mutated() -> None:
	"""Emit VERSAO 3.0 even when the header was mutated to 4.0 after validation."""
	doc = _doc()
	doc.header.versao = "4.0"  # type: ignore[assignment]
	assert "<VERSAO>3.0</VERSAO>" in str(InformeDiarioV3().export(doc))


def test_v3_writer_rejects_a_v4_document() -> None:
	"""Refuse a V4 document: the V3 writer is its own port adapter, not a V4 subclass."""
	header = InformeDiarioHeader(dt_compt="15/01/2025", dt_gerac_arq="15/01/2025")
	v4_doc = InformeDiarioDocument(
		header=header, informs=[InformeDiarioInform(**_inform().model_dump())]
	)
	with pytest.raises(TypeError):
		InformeDiarioV3().export(v4_doc)


def test_v4_writer_stamps_its_own_versao_on_a_v3_document() -> None:
	"""Pin that the V4 writer emits VERSAO 4.0 for a V3 model (V3 fields are a V4 subset)."""
	assert "<VERSAO>4.0</VERSAO>" in str(InformeDiario().export(_doc()))
