"""Unit tests for the FAR submission writer.

Expected tag lists and Table A are typed from the CVM page, not derived from the models.
"""

from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET

from pydantic import ValidationError
import pytest

from filings_cvm.submission import Far, FarDocument, FarFund, FarHeader, FarMovement


VALID_CNPJ = "11222333000181"
OTHER_CNPJ = "11444777000161"
LEADING_ZERO_CNPJ = "00000000000191"  # valid check digits (Banco do Brasil)

HEADER_TAGS = ["COD_DOC", "CNPJ_ADM", "DT_COMPT", "DT_GERAC_ARQ"]
ROW_TAGS = [
	"CNPJ_FUNDO",
	"NR_QUOTA_CIRCUL_ULT_DIA_MES",
	"VL_QUOTA_ULT_DIA_MES",
	"NR_TOTAL_QUOTST_ULT_DIA_MES",
	"VL_ULT_DISTR_QUOTA",
	"DT_DISTR",
	"VL_QUOTA_DT_ULT_DISTR",
	"DOC_MOV_MES",
]
# Table A as typed from the page: code -> (Entrada, Saída), True where "S".
TABLE_A = {
	37: (True, True),
	48: (True, True),
	53: (True, False),
	54: (False, True),
	55: (True, True),
	56: (True, False),
	57: (True, False),
	58: (True, False),
	60: (True, False),
	61: (False, True),
	62: (False, True),
	63: (False, True),
	64: (False, True),
	65: (False, True),
	66: (False, True),
	67: (True, False),
	68: (False, True),
	69: (False, True),
	70: (True, True),
	71: (True, False),
	72: (False, True),
	73: (False, True),
	74: (True, True),
	75: (True, True),
	77: (True, True),
	78: (True, True),
	144: (True, False),
	145: (True, True),
	150: (False, True),
}


def movements() -> list[dict]:
	"""Build a full, rule-respecting Table A movement list.

	Returns
	-------
	list[dict]
		One entry per Table A code, filled only where the table allows.
	"""
	return [
		{
			"cd_mov": code,
			"vl_entr": 10 if entr else None,
			"vl_saida": 20 if saida else None,
		}
		for code, (entr, saida) in TABLE_A.items()
	]


def fund(**overrides: object) -> dict:
	"""Build one valid fund dict (no distribution).

	Parameters
	----------
	**overrides : object
		Fields to replace.

	Returns
	-------
	dict
		The fund fields.
	"""
	base = {
		"cnpj_fundo": VALID_CNPJ,
		"nr_quota_circul_ult_dia_mes": "1000.5",
		"vl_quota_ult_dia_mes": Decimal("12.1234567890123"),
		"nr_total_quotst_ult_dia_mes": 42,
		"movements": movements(),
	}
	return base | overrides


def document(funds: list[dict] | None = None, **header: object) -> FarDocument:
	"""Build a valid document.

	Parameters
	----------
	funds : list[dict] | None
		Fund dicts; one default fund when omitted.
	**header : object
		Header fields to replace.

	Returns
	-------
	FarDocument
		The validated document.
	"""
	head = {"cnpj_adm": OTHER_CNPJ, "dt_compt": "09/2026", "dt_gerac_arq": "10/10/2026"} | header
	return FarDocument(header=head, funds=funds or [fund()])


def parse(doc: FarDocument) -> ET.Element:
	"""Export and parse a document.

	Parameters
	----------
	doc : FarDocument
		The document.

	Returns
	-------
	ET.Element
		The root element.
	"""
	return ET.fromstring(Far().export(doc).encode("windows-1252"))  # noqa: S314


def tags(element: ET.Element) -> list[str]:
	"""List the child tags of an element in order.

	Parameters
	----------
	element : ET.Element
		The parent.

	Returns
	-------
	list[str]
		Child tags.
	"""
	return [child.tag for child in element]


def test_export_header_block_matches_spec_tags_and_values() -> None:
	"""Export header block matches spec tags and values."""
	root = parse(document())
	assert root.tag == "DOC_ARQ"
	assert tags(root) == ["DESC_ADM", "FAR"]
	adm = root.find("DESC_ADM")
	assert tags(adm) == HEADER_TAGS
	assert [child.text for child in adm] == ["4", OTHER_CNPJ, "09/2026", "10/10/2026"]


def test_export_declares_windows_1252() -> None:
	"""Export declares windows 1252."""
	assert Far().export(document()).startswith('<?xml version="1.0" encoding="windows-1252"?>')


def test_export_fund_without_distribution_omits_the_three_conditional_tags() -> None:
	"""Export fund without distribution omits the three conditional tags."""
	row = parse(document()).find("FAR/ROW_REGISTRO_MOVIMENTO")
	assert tags(row) == [
		t for t in ROW_TAGS if t not in ("VL_ULT_DISTR_QUOTA", "DT_DISTR", "VL_QUOTA_DT_ULT_DISTR")
	]


def test_export_fund_with_distribution_emits_all_tags_in_spec_order() -> None:
	"""Export fund with distribution emits all tags in spec order."""
	doc = document(
		[fund(vl_ult_distr_quota="0.5", dt_distr="05/09/2026", vl_quota_dt_ult_distr=2)]
	)
	row = parse(doc).find("FAR/ROW_REGISTRO_MOVIMENTO")
	assert tags(row) == ROW_TAGS
	assert row.find("DT_DISTR").text == "05/09/2026"
	assert row.find("VL_ULT_DISTR_QUOTA").text == "0,5000000000"


def test_export_quota_decimals_use_comma_ten_places_truncated() -> None:
	"""Export quota decimals use comma ten places truncated."""
	row = parse(document()).find("FAR/ROW_REGISTRO_MOVIMENTO")
	assert row.find("NR_QUOTA_CIRCUL_ULT_DIA_MES").text == "1000,5000000000"
	assert row.find("VL_QUOTA_ULT_DIA_MES").text == "12,1234567890"
	assert row.find("NR_TOTAL_QUOTST_ULT_DIA_MES").text == "42"


def test_export_cnpj_has_no_leading_zeros() -> None:
	"""Export cnpj has no leading zeros."""
	root = parse(document([fund(cnpj_fundo=LEADING_ZERO_CNPJ)], cnpj_adm="00.000.000/0001-91"))
	assert root.find("DESC_ADM/CNPJ_ADM").text == "191"
	assert root.find("FAR/ROW_REGISTRO_MOVIMENTO/CNPJ_FUNDO").text == "191"


def test_export_movement_block_covers_table_a_with_fillable_columns_only() -> None:
	"""Export movement block covers table a with fillable columns only."""
	block = parse(document()).find("FAR/ROW_REGISTRO_MOVIMENTO/DOC_MOV_MES")
	rows = list(block)
	assert {r.tag for r in rows} == {"ROW_MOV_POR_FUNDO"}
	assert [int(r.find("CD_MOV").text) for r in rows] == list(TABLE_A)
	for row in rows:
		entr, saida = TABLE_A[int(row.find("CD_MOV").text)]
		assert (row.find("VL_ENTR") is not None) is entr
		assert (row.find("VL_SAIDA") is not None) is saida
		assert tags(row) == ["CD_MOV"] + ["VL_ENTR"] * entr + ["VL_SAIDA"] * saida


def test_export_multiple_funds_repeat_the_row_block() -> None:
	"""Export multiple funds repeat the row block."""
	doc = document([fund(), fund(cnpj_fundo=OTHER_CNPJ)])
	assert tags(parse(doc).find("FAR")) == ["ROW_REGISTRO_MOVIMENTO"] * 2


def test_export_writes_file_in_windows_1252(tmp_path: Path) -> None:
	"""Export writes file in windows 1252."""
	target = tmp_path / "far.xml"
	assert Far().export(document(), output_path=str(target)) is None
	assert target.read_bytes().startswith(b'<?xml version="1.0" encoding="windows-1252"?>')


def test_export_failure_leaves_existing_file_untouched(tmp_path: Path) -> None:
	"""Export failure leaves existing file untouched."""
	target = tmp_path / "far.xml"
	target.write_bytes(b"keep")
	bad = document().model_copy(
		update={
			"header": FarHeader.model_construct(
				cod_doc=4, cnpj_adm="中", dt_compt="09/2026", dt_gerac_arq="10/10/2026"
			)
		}
	)
	with pytest.raises(ValueError, match="windows-1252"):
		Far().export(bad, output_path=str(target))
	assert target.read_bytes() == b"keep"


def test_header_cod_doc_is_fixed_at_4() -> None:
	"""Header cod doc is fixed at 4."""
	with pytest.raises(ValidationError):
		FarHeader(cod_doc=5, cnpj_adm=VALID_CNPJ, dt_compt="09/2026", dt_gerac_arq="10/10/2026")


@pytest.mark.parametrize(
	"cnpj", ["11222333000180", " 11222333000181", "11222333000181\n", "1234", "11.222.333/0001-8"]
)
def test_header_rejects_bad_cnpj(cnpj: str) -> None:
	"""Header rejects bad cnpj."""
	with pytest.raises(ValidationError):
		document(cnpj_adm=cnpj)


def test_header_rejects_alphanumeric_cnpj() -> None:
	"""Header rejects alphanumeric cnpj."""
	with pytest.raises(ValidationError):
		document(cnpj_adm="12ABC34501DE35")


@pytest.mark.parametrize(
	"compt", ["13/2026", "00/2026", "9/2026", "09/26", "09/1800", "09/2026\n"]
)
def test_header_rejects_bad_competence(compt: str) -> None:
	"""Header rejects bad competence."""
	with pytest.raises(ValidationError):
		document(dt_compt=compt)


@pytest.mark.parametrize("day", ["31/02/2026", "2026-10-10", "10/10/0001", "10/10/2026\n"])
def test_header_rejects_impossible_or_misshaped_dates(day: str) -> None:
	"""Header rejects impossible or misshaped dates."""
	with pytest.raises(ValidationError):
		document(dt_gerac_arq=day)


@pytest.mark.parametrize("value", [1.5, float("nan"), True, "abc", -1, Decimal("Infinity")])
def test_fund_quota_decimals_refuse_float_bool_junk_and_negatives(value: object) -> None:
	"""Fund quota decimals refuse float bool junk and negatives."""
	with pytest.raises(ValidationError):
		fund_model(nr_quota_circul_ult_dia_mes=value)


def fund_model(**overrides: object) -> FarFund:
	"""Validate a fund dict.

	Parameters
	----------
	**overrides : object
		Fields to replace.

	Returns
	-------
	FarFund
		The validated fund.
	"""
	return FarFund(**fund(**overrides))


@pytest.mark.parametrize("value", [-1, 1.0, "5", True])
def test_fund_quotista_count_is_a_strict_non_negative_integer(value: object) -> None:
	"""Fund quotista count is a strict non negative integer."""
	with pytest.raises(ValidationError):
		fund_model(nr_total_quotst_ult_dia_mes=value)


@pytest.mark.parametrize(
	"partial",
	[
		{"vl_ult_distr_quota": "1"},
		{"dt_distr": "05/09/2026"},
		{"vl_quota_dt_ult_distr": "1"},
		{"vl_ult_distr_quota": "1", "dt_distr": "05/09/2026"},
	],
)
def test_fund_distribution_fields_are_all_or_nothing(partial: dict) -> None:
	"""Fund distribution fields are all or nothing."""
	with pytest.raises(ValidationError, match="all be given or all omitted"):
		fund_model(**partial)


def test_fund_rejects_impossible_distribution_date() -> None:
	"""Fund rejects impossible distribution date."""
	with pytest.raises(ValidationError):
		fund_model(vl_ult_distr_quota="1", dt_distr="31/04/2026", vl_quota_dt_ult_distr="1")


def test_fund_requires_every_table_a_code() -> None:
	"""Fund requires every table a code."""
	with pytest.raises(ValidationError, match="missing=\\[150\\]"):
		fund_model(movements=movements()[:-1])


def test_fund_rejects_repeated_table_a_code() -> None:
	"""Fund rejects repeated table a code."""
	with pytest.raises(ValidationError, match="repeated=\\[48\\]"):
		fund_model(movements=[*movements()[1:], *movements()[:2]])


def test_movement_rejects_code_outside_table_a() -> None:
	"""Movement rejects code outside table a."""
	with pytest.raises(ValidationError, match="not in Table A"):
		FarMovement(cd_mov=99, vl_entr=1, vl_saida=1)


@pytest.mark.parametrize("code", [c for c, (entr, saida) in TABLE_A.items() if not entr])
def test_movement_rejects_entrada_where_table_a_marks_n(code: int) -> None:
	"""Movement rejects entrada where table a marks n."""
	with pytest.raises(ValidationError, match="VL_ENTR must not be filled"):
		FarMovement(cd_mov=code, vl_entr=1, vl_saida=1)


@pytest.mark.parametrize("code", [c for c, (entr, saida) in TABLE_A.items() if not saida])
def test_movement_rejects_saida_where_table_a_marks_n(code: int) -> None:
	"""Movement rejects saida where table a marks n."""
	with pytest.raises(ValidationError, match="VL_SAIDA must not be filled"):
		FarMovement(cd_mov=code, vl_entr=1, vl_saida=1)


@pytest.mark.parametrize("code", [c for c, (entr, saida) in TABLE_A.items() if entr and saida])
def test_movement_requires_both_columns_where_table_a_marks_s_s(code: int) -> None:
	"""Movement requires both columns where table a marks s s."""
	with pytest.raises(ValidationError, match="is required"):
		FarMovement(cd_mov=code, vl_entr=1)


@pytest.mark.parametrize("value", [-1, 1.5, "7", True])
def test_movement_amounts_are_strict_non_negative_integers(value: object) -> None:
	"""Movement amounts are strict non negative integers."""
	with pytest.raises(ValidationError):
		FarMovement(cd_mov=37, vl_entr=value, vl_saida=1)


def test_document_requires_at_least_one_fund() -> None:
	"""Document requires at least one fund."""
	with pytest.raises(ValidationError):
		FarDocument(header=document().header, funds=[])


def test_document_rejects_duplicate_fund_cnpj() -> None:
	"""Document rejects duplicate fund cnpj."""
	with pytest.raises(ValidationError, match="unique"):
		document([fund(), fund(cnpj_fundo="11.222.333/0001-81")])


def test_models_are_closed_and_frozen() -> None:
	"""Models are closed and frozen."""
	with pytest.raises(ValidationError):
		FarMovement(cd_mov=53, vl_entr=1, extra=1)
	with pytest.raises(ValidationError):
		document().header.cod_doc = 5
