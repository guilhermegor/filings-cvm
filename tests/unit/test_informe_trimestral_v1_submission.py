"""Unit tests for the Informe Trimestral V1 submission writer.

The expected tag lists and scales are typed from the CVM page's sample file and field notes
(``PadraoXMLInfoTrim.asp``), not derived from the models, so a field declared out of order or at
the wrong scale fails here. Every test holds one assertion site.
"""

from contextlib import suppress
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET

from pydantic import ValidationError
import pytest

from filings_cvm.submission import (
	InformeTrimestralV1,
	InformeTrimestralV1Document,
	InformeTrimestralV1Header,
)


NS = "{urn:inftrim}"
VALID_CNPJ = "11222333000181"
OTHER_CNPJ = "11444777000161"
HEADER = {"dt_compt": "06/2017", "dt_gerac_arq": "15/07/2017"}


def _inform(cnpj: str = VALID_CNPJ, **over: object) -> dict:
	base = {
		"cnpj_fdo": cnpj,
		"patrim_liq": "1000.5",
		"qt_cotistas": 12,
		"qt_quota": 3400,
		"vl_patrim_quota": "12.123456789012",
	}
	base.update(over)
	return base


def _doc(*informs: dict, header: dict | None = None) -> InformeTrimestralV1Document:
	funds = list(informs) or [_inform()]
	return InformeTrimestralV1Document(header=header or HEADER, informs=funds)


def _xml(doc: InformeTrimestralV1Document) -> ET.Element:
	text = InformeTrimestralV1().export(doc)
	return ET.fromstring(text.encode("windows-1252"))  # noqa: S314


def _local(el: ET.Element) -> str:
	return el.tag.removeprefix(NS)


def _tags(el: ET.Element) -> list[str]:
	return list(map(_local, el))


def _texts(el: ET.Element) -> list[str | None]:
	return [c.text for c in el]


def test_export_starts_with_windows_1252_declaration() -> None:
	"""Export starts with the windows-1252 declaration."""
	assert (
		InformeTrimestralV1()
		.export(_doc())
		.startswith('<?xml version="1.0" encoding="windows-1252"?>\n')
	)


def test_root_is_doc_arq_in_the_page_namespace() -> None:
	"""Root is DOC_ARQ in the urn:inftrim namespace."""
	assert _xml(_doc()).tag == f"{NS}DOC_ARQ"


def test_root_children_in_page_order() -> None:
	"""Root children in page order."""
	assert _tags(_xml(_doc())) == ["CAB_INFORM", "LISTA_INFORM"]


def test_header_tags_in_page_order() -> None:
	"""Header tags in page order."""
	assert _tags(_xml(_doc())[0]) == ["COD_DOC", "DT_COMPT", "DT_GERAC_ARQ", "VERSAO"]


def test_header_values_are_code_51_and_version_1() -> None:
	"""Header values are code 51 and version 1.0."""
	assert _texts(_xml(_doc())[0]) == ["51", "06/2017", "15/07/2017", "1.0"]


def test_inform_tags_in_page_order() -> None:
	"""Inform tags in page order."""
	assert _tags(_xml(_doc())[1][0]) == [
		"CNPJ_FDO",
		"PATRIM_LIQ",
		"QT_COTISTAS",
		"QT_QUOTA",
		"VL_PATRIM_QUOTA",
	]


def test_inform_values_use_page_scales_and_decimal_comma() -> None:
	"""Inform values use the page scales (2 and 12 places) and a decimal comma."""
	assert _texts(_xml(_doc())[1][0]) == [
		VALID_CNPJ,
		"1000,50",
		"12",
		"3400",
		"12,123456789012",
	]


def test_whole_number_still_carries_the_full_scale() -> None:
	"""A whole number is written at the full scale, not as an integer."""
	assert _texts(_xml(_doc(_inform(vl_patrim_quota="1")))[1][0])[4] == "1,000000000000"


def test_multiple_funds_are_repeated_informs() -> None:
	"""Multiple funds are repeated informs."""
	assert _tags(_xml(_doc(_inform(), _inform(OTHER_CNPJ)))[1]) == ["INFORM", "INFORM"]


def test_masked_cnpj_is_written_bare() -> None:
	"""Masked cnpj is written bare."""
	assert _xml(_doc(_inform("11.222.333/0001-81")))[1][0][0].text == VALID_CNPJ


def test_net_worth_truncates_beyond_two_places() -> None:
	"""Net worth truncates beyond two places, never rounds."""
	assert _doc(_inform(patrim_liq="1.999")).informs[0].patrim_liq == Decimal("1.99")


def test_quota_value_truncates_beyond_twelve_places() -> None:
	"""Quota value truncates beyond twelve places, never rounds."""
	doc = _doc(_inform(vl_patrim_quota="1.9999999999999"))
	assert doc.informs[0].vl_patrim_quota == Decimal("1.999999999999")


def test_negative_net_worth_allowed() -> None:
	"""Negative net worth allowed."""
	assert _doc(_inform(patrim_liq="-5")).informs[0].patrim_liq == Decimal(-5)


@pytest.mark.parametrize("field", ["patrim_liq", "vl_patrim_quota"])
def test_float_decimal_is_refused(field: str) -> None:
	"""Float decimal is refused."""
	with pytest.raises(ValidationError):
		_doc(_inform(**{field: 1.5}))


@pytest.mark.parametrize(
	("field", "bad"),
	[
		("patrim_liq", "NaN"),
		("patrim_liq", "1" + "0" * 18),
		("vl_patrim_quota", "Infinity"),
		("qt_cotistas", -1),
		("qt_cotistas", 1.0),
		("qt_cotistas", True),
		("qt_cotistas", "3"),
		("qt_quota", -1),
		("qt_quota", 2.5),
		("qt_quota", 10**12),
		("cnpj_fdo", "11222333000182"),
		("cnpj_fdo", " 11222333000181"),
		("cnpj_fdo", "11222333000181\n"),
	],
)
def test_invalid_inform_values_rejected(field: str, bad: object) -> None:
	"""Invalid inform values rejected."""
	with pytest.raises(ValidationError):
		_doc(_inform(**{field: bad}))


@pytest.mark.parametrize(
	"missing", ["cnpj_fdo", "patrim_liq", "qt_cotistas", "qt_quota", "vl_patrim_quota"]
)
def test_every_inform_field_is_required(missing: str) -> None:
	"""Every inform field is required."""
	data = _inform()
	del data[missing]
	with pytest.raises(ValidationError):
		_doc(data)


def test_unknown_inform_field_rejected() -> None:
	"""Unknown inform field rejected."""
	with pytest.raises(ValidationError):
		_doc(_inform(extra="x"))


@pytest.mark.parametrize("month", ["03", "06", "09", "12"])
def test_competence_closing_a_quarter_accepted(month: str) -> None:
	"""Competence closing a quarter accepted."""
	assert _doc(header={**HEADER, "dt_compt": f"{month}/2017"}).header.dt_compt == f"{month}/2017"


@pytest.mark.parametrize(
	"bad", ["01/2017", "04/2017", "13/2017", "6/2017", "06/17", "00/2017", "06/1899", "06/2017\n"]
)
def test_competence_rejected(bad: str) -> None:
	"""Competence rejected."""
	with pytest.raises(ValidationError):
		_doc(header={**HEADER, "dt_compt": bad})


@pytest.mark.parametrize("bad", ["31/02/2017", "00/01/2017", "1/1/2017", "01/01/0001", "x"])
def test_generation_date_must_be_a_real_date(bad: str) -> None:
	"""Generation date must be a real date."""
	with pytest.raises(ValidationError):
		InformeTrimestralV1Header(dt_compt="06/2017", dt_gerac_arq=bad)


def test_document_code_is_fixed_at_51() -> None:
	"""The document code is fixed at 51."""
	with pytest.raises(ValidationError):
		InformeTrimestralV1Header(cod_doc=50, **HEADER)


def test_version_is_fixed_at_1_0() -> None:
	"""The version is fixed at 1.0 (V2's 2.0 is refused)."""
	with pytest.raises(ValidationError):
		InformeTrimestralV1Header(versao="2.0", **HEADER)


def test_document_needs_at_least_one_fund() -> None:
	"""A document needs at least one fund."""
	with pytest.raises(ValidationError):
		InformeTrimestralV1Document(header=HEADER, informs=[])


def test_document_rejects_a_repeated_fund() -> None:
	"""A document rejects a repeated fund."""
	with pytest.raises(ValidationError):
		_doc(_inform(), _inform())


def test_document_rejects_more_than_100_funds() -> None:
	"""A document rejects more than 100 funds."""
	with pytest.raises(ValidationError):
		_doc(*map(_inform, (f"{n:08d}000100" for n in range(101))))


def test_export_to_file_returns_none(tmp_path: Path) -> None:
	"""Export to a file returns None."""
	assert InformeTrimestralV1().export(_doc(), str(tmp_path / "it.xml")) is None


def test_exported_file_is_windows_1252_xml(tmp_path: Path) -> None:
	"""The exported file is windows-1252 XML."""
	out = tmp_path / "it.xml"
	InformeTrimestralV1().export(_doc(), str(out))
	assert out.read_bytes().startswith(b'<?xml version="1.0" encoding="windows-1252"?>')


def test_export_leaves_no_temp_file(tmp_path: Path) -> None:
	"""Export leaves no temp file behind."""
	InformeTrimestralV1().export(_doc(), str(tmp_path / "it.xml"))
	assert [p.name for p in tmp_path.iterdir()] == ["it.xml"]


def _unencodable_doc() -> InformeTrimestralV1Document:
	doc = _doc()
	object.__setattr__(doc.informs[0], "cnpj_fdo", "中")
	return doc


def test_unencodable_text_raises_value_error(tmp_path: Path) -> None:
	"""Unencodable text raises a ValueError naming the encoding."""
	with pytest.raises(ValueError, match="windows-1252"):
		InformeTrimestralV1().export(_unencodable_doc(), str(tmp_path / "it.xml"))


def test_unencodable_text_never_wipes_existing_file(tmp_path: Path) -> None:
	"""Unencodable text never wipes an existing file."""
	out = tmp_path / "it.xml"
	out.write_bytes(b"keep me")
	with suppress(ValueError):
		InformeTrimestralV1().export(_unencodable_doc(), str(out))
	assert out.read_bytes() == b"keep me"


def test_informs_list_input_is_coerced_to_an_immutable_tuple() -> None:
	"""List input is stored as a tuple, so a caller cannot append after validation."""
	doc = _doc(_inform())
	assert isinstance(doc.informs, tuple)
