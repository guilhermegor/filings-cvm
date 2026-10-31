"""Unit tests for the four Informe Sintético submission writers.

The expected tag lists are typed from the sample files on the CVM pages
(``PadraoXMLSint{FCCE,FITVM,FIC,Outros}.asp``), not derived from the schema, so a drifting
field name or order fails here.
"""

from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET  # noqa: S405

from pydantic import ValidationError
import pytest

from filings_cvm.submission import (
	InformeSinteticoFcce,
	InformeSinteticoFcceDocument,
	InformeSinteticoFic,
	InformeSinteticoFicDocument,
	InformeSinteticoFitvm,
	InformeSinteticoFitvmDocument,
	InformeSinteticoOutros,
	InformeSinteticoOutrosDocument,
)


_ADM = "00360305000104"
_FUND_A = "11222333000181"
_FUND_B = "11444777000161"
_OUTRAS_TAIL = [
	"NR_TOT_QUOTST_ULT_DIA_MES",
	"VL_QUOTA_ULT_DIA_MES",
	"PATRIM_LIQ",
	"QUOTA_EMITIDA_MES",
	"QUOTA_RESG_MES",
]
_DESC = ["DESC_ADM", "COD_DOC", "CNPJ_ADM", "DT_COMPT", "DT_GERAC_ARQ"]

_FCCE_APLIC = [
	"ACOES",
	"QUOTA_FDO_RENDA_FIXA",
	"TIT_DIVIDA_PUBLIC_FED",
	"OUTRO_VL_MOBILI_EMISS_CIA_ABER",
	"OUTRA_APLIC",
]
_FITVM_APLIC = [
	"ACAO",
	"MERC_A_TERMO",
	"POS_COMPRD",
	"POS_VEND",
	"CONTR_FUTURO",
	"TOT_MARGEM_REQUERIDA",
	"MERC_OPCAO",
	"PREMIO_PAGO",
	"PREMIO_RECEB",
	"DEBT",
	"SIMPLES",
	"CONVERSIVEIS",
	"CERTF_RECIBO_DEPOS_OUTRO_VL_MOBILI",
	"TIT_PUBLIC",
	"TIT_RENDA_FIXA_EMISS_INSTIT_FINANC",
	"COTA_FDO_INVEST_FINANC",
	"OUTRA_APLIC",
]
_FIC_APLIC = [
	"COTAS",
	"TIT_PUBLIC",
	"TIT_RENDA_FIXA_EMISS_INSTIT_FINANC",
	"COTA_FDO_INVEST_FINANC",
	"OUTRA_APLIC",
]
_OUTROS_APLIC = [
	"ACAO",
	"MERC_OPCAO",
	"PREMIO_PAGO",
	"PREMIO_RECEB",
	"MERC_A_TERMO",
	"POS_COMPRD",
	"POS_VEND",
	"CONVERSIVEIS",
	"SIMPLES",
	"TIT_PUBLIC",
	"MOEDA_PRIVAT",
	"OUTRA_APLIC",
]


def _row_tags(aplic: list[str], outras: list[str]) -> list[str]:
	"""Spec preorder of one ROW_INFORME."""
	return [
		"ROW_INFORME",
		"CNPJ_FUNDO",
		"APLICACOES_POS_FINAL",
		"APLICACOES",
		*aplic,
		"OUTRAS",
		*outras,
	]


def _doc_tags(aplic: list[str], outras: list[str], rows: int = 1) -> list[str]:
	"""Spec preorder of a whole file below DOC_ARQ."""
	return [*_DESC, "INFORME_SINTETICO", *_row_tags(aplic, outras) * rows]


def _int_block(n: int) -> dict:
	return dict.fromkeys(range(n), 0)


def _header(cod: int) -> dict:
	return {"cod_doc": cod, "cnpj_adm": _ADM, "dt_compt": "09/2026", "dt_gerac_arq": "05/10/2026"}


def _tail(**extra: object) -> dict:
	base = {
		"nr_tot_quotst_ult_dia_mes": 12,
		"vl_quota_ult_dia_mes": "1.2345",
		"patrim_liq": 5000,
		"quota_emitida_mes": 300,
		"quota_resg_mes": 200,
	}
	return {**extra, **base}


def _fcce_row(cnpj: str = _FUND_A) -> dict:
	return {
		"cnpj_fundo": cnpj,
		"aplicacoes_pos_final": {
			"aplicacoes": {
				"acoes": 1,
				"quota_fdo_renda_fixa": 2,
				"tit_divida_public_fed": 3,
				"outro_vl_mobili_emiss_cia_aber": 4,
				"outra_aplic": 5,
			},
			"outras": _tail(vl_contr_futuro_mantido_aber=6),
		},
	}


def _fitvm_row(cnpj: str = _FUND_A) -> dict:
	return {
		"cnpj_fundo": cnpj,
		"aplicacoes_pos_final": {
			"aplicacoes": {
				"acao": 1,
				"merc_a_termo": {"pos_comprd": 2, "pos_vend": 3},
				"contr_futuro": {"tot_margem_requerida": 4},
				"merc_opcao": {"premio_pago": 5, "premio_receb": 6},
				"debt": {"simples": 7, "conversiveis": 8},
				"certf_recibo_depos_outro_vl_mobili": 9,
				"tit_public": 10,
				"tit_renda_fixa_emiss_instit_financ": 11,
				"cota_fdo_invest_financ": 12,
				"outra_aplic": 13,
			},
			"outras": _tail(),
		},
	}


def _fic_row(cnpj: str = _FUND_A) -> dict:
	return {
		"cnpj_fundo": cnpj,
		"aplicacoes_pos_final": {
			"aplicacoes": {
				"cotas": 1,
				"tit_public": 2,
				"tit_renda_fixa_emiss_instit_financ": 3,
				"cota_fdo_invest_financ": 4,
				"outra_aplic": 5,
			},
			"outras": _tail(),
		},
	}


def _outros_row(cnpj: str = _FUND_A) -> dict:
	return {
		"cnpj_fundo": cnpj,
		"aplicacoes_pos_final": {
			"aplicacoes": {
				"acao": 1,
				"merc_opcao": {"premio_pago": 2, "premio_receb": 3},
				"merc_a_termo": {"pos_comprd": 4, "pos_vend": 5},
				"conversiveis": 6,
				"simples": 7,
				"tit_public": 8,
				"moeda_privat": 9,
				"outra_aplic": 10,
			},
			"outras": _tail(vl_contr_futuro_mantido_aberto=11),
		},
	}


_VARIANTS = {
	"fcce": (
		InformeSinteticoFcce,
		InformeSinteticoFcceDocument,
		5,
		_fcce_row,
		_FCCE_APLIC,
		["VL_CONTR_FUTURO_MANTIDO_ABER", *_OUTRAS_TAIL],
	),
	"fitvm": (
		InformeSinteticoFitvm,
		InformeSinteticoFitvmDocument,
		7,
		_fitvm_row,
		_FITVM_APLIC,
		_OUTRAS_TAIL,
	),
	"fic": (
		InformeSinteticoFic,
		InformeSinteticoFicDocument,
		8,
		_fic_row,
		_FIC_APLIC,
		_OUTRAS_TAIL,
	),
	"outros": (
		InformeSinteticoOutros,
		InformeSinteticoOutrosDocument,
		9,
		_outros_row,
		_OUTROS_APLIC,
		["VL_CONTR_FUTURO_MANTIDO_ABERTO", *_OUTRAS_TAIL],
	),
}


def _build(variant: str, rows: list[dict] | None = None, **header: object) -> tuple:
	writer, doc_cls, cod, row_fn, _, _ = _VARIANTS[variant]
	doc = doc_cls(
		header={**_header(cod), **header},
		informs=rows if rows is not None else [row_fn()],
	)
	return writer(), doc


def _tags(xml: str) -> list[str]:
	root = ET.fromstring(xml.encode("windows-1252"))  # noqa: S314
	return [e.tag for e in root.iter()][1:]


@pytest.mark.parametrize("variant", list(_VARIANTS))
def test_export_tag_order_matches_spec_sample(variant: str) -> None:
	"""Export tag order matches spec sample."""
	writer, doc = _build(variant)
	_, _, _, _, aplic, outras = _VARIANTS[variant]
	assert _tags(writer.export(doc)) == _doc_tags(aplic, outras)


@pytest.mark.parametrize("variant", list(_VARIANTS))
def test_export_repeats_row_per_fund(variant: str) -> None:
	"""Export repeats row per fund."""
	_, _, _, row_fn, aplic, outras = _VARIANTS[variant]
	writer, doc = _build(variant, [row_fn(_FUND_A), row_fn(_FUND_B)])
	assert _tags(writer.export(doc)) == _doc_tags(aplic, outras, rows=2)


@pytest.mark.parametrize("variant", list(_VARIANTS))
def test_export_header_values_and_declaration(variant: str) -> None:
	"""Export header values and declaration."""
	writer, doc = _build(variant)
	xml = writer.export(doc)
	assert xml.startswith('<?xml version="1.0" encoding="windows-1252"?>\n<DOC_ARQ>')
	root = ET.fromstring(xml.encode("windows-1252"))  # noqa: S314
	cod = _VARIANTS[variant][2]
	assert root.findtext("DESC_ADM/COD_DOC") == str(cod)
	# The page asks for no leading zeros on the CNPJ.
	assert root.findtext("DESC_ADM/CNPJ_ADM") == "360305000104"
	assert root.findtext("DESC_ADM/DT_COMPT") == "09/2026"
	assert root.findtext("DESC_ADM/DT_GERAC_ARQ") == "05/10/2026"
	assert root.findtext("INFORME_SINTETICO/ROW_INFORME/CNPJ_FUNDO") == _FUND_A


@pytest.mark.parametrize("variant", list(_VARIANTS))
def test_export_decimal_uses_comma_and_truncates(variant: str) -> None:
	"""Export decimal uses comma and truncates."""
	writer, doc = _build(variant)
	root = ET.fromstring(writer.export(doc).encode("windows-1252"))  # noqa: S314
	# 1.2345 is truncated, never rounded, to 2 places with a comma separator.
	assert root.findtext(".//VL_QUOTA_ULT_DIA_MES") == "1,23"
	assert root.findtext(".//NR_TOT_QUOTST_ULT_DIA_MES") == "12"
	assert root.findtext(".//PATRIM_LIQ") == "5000"


def test_export_values_land_in_their_tags_fitvm() -> None:
	"""Export values land in their tags fitvm."""
	writer, doc = _build("fitvm")
	root = ET.fromstring(writer.export(doc).encode("windows-1252"))  # noqa: S314
	expected = {
		"ACAO": "1",
		"MERC_A_TERMO/POS_COMPRD": "2",
		"MERC_A_TERMO/POS_VEND": "3",
		"CONTR_FUTURO/TOT_MARGEM_REQUERIDA": "4",
		"MERC_OPCAO/PREMIO_PAGO": "5",
		"MERC_OPCAO/PREMIO_RECEB": "6",
		"DEBT/SIMPLES": "7",
		"DEBT/CONVERSIVEIS": "8",
		"CERTF_RECIBO_DEPOS_OUTRO_VL_MOBILI": "9",
		"TIT_PUBLIC": "10",
		"TIT_RENDA_FIXA_EMISS_INSTIT_FINANC": "11",
		"COTA_FDO_INVEST_FINANC": "12",
		"OUTRA_APLIC": "13",
	}
	base = ".//APLICACOES/"
	assert {k: root.findtext(base + k) for k in expected} == expected


def test_export_values_land_in_their_tags_outros() -> None:
	"""Export values land in their tags outros."""
	writer, doc = _build("outros")
	root = ET.fromstring(writer.export(doc).encode("windows-1252"))  # noqa: S314
	expected = {
		"ACAO": "1",
		"MERC_OPCAO/PREMIO_PAGO": "2",
		"MERC_OPCAO/PREMIO_RECEB": "3",
		"MERC_A_TERMO/POS_COMPRD": "4",
		"MERC_A_TERMO/POS_VEND": "5",
		"CONVERSIVEIS": "6",
		"SIMPLES": "7",
		"TIT_PUBLIC": "8",
		"MOEDA_PRIVAT": "9",
		"OUTRA_APLIC": "10",
	}
	assert {k: root.findtext(".//APLICACOES/" + k) for k in expected} == expected
	assert root.findtext(".//OUTRAS/VL_CONTR_FUTURO_MANTIDO_ABERTO") == "11"


def test_export_values_land_in_their_tags_fcce_and_fic() -> None:
	"""Export values land in their tags fcce and fic."""
	writer, doc = _build("fcce")
	root = ET.fromstring(writer.export(doc).encode("windows-1252"))  # noqa: S314
	assert [e.text for e in root.find(".//APLICACOES")] == ["1", "2", "3", "4", "5"]
	assert root.findtext(".//OUTRAS/VL_CONTR_FUTURO_MANTIDO_ABER") == "6"
	writer, doc = _build("fic")
	root = ET.fromstring(writer.export(doc).encode("windows-1252"))  # noqa: S314
	assert [e.text for e in root.find(".//APLICACOES")] == ["1", "2", "3", "4", "5"]


def test_export_negative_equity_allowed() -> None:
	"""Export negative equity allowed."""
	row = _fic_row()
	row["aplicacoes_pos_final"]["outras"]["patrim_liq"] = -10
	writer, doc = _build("fic", [row])
	assert "<PATRIM_LIQ>-10</PATRIM_LIQ>" in writer.export(doc)


def test_export_writes_windows_1252_file_and_returns_none(tmp_path: Path) -> None:
	"""Export writes windows 1252 file and returns none."""
	writer, doc = _build("fcce")
	target = tmp_path / "out.xml"
	assert writer.export(doc, str(target)) is None
	assert target.read_bytes().decode("windows-1252") == writer.export(doc)


def test_export_unencodable_text_keeps_existing_file(tmp_path: Path) -> None:
	"""Export unencodable text keeps existing file."""
	writer, doc = _build("fcce")
	bad = doc.model_construct(
		header=doc.header.model_copy(update={"dt_compt": "中"}), informs=doc.informs
	)
	target = tmp_path / "keep.xml"
	target.write_bytes(b"original")
	with pytest.raises(ValueError, match="windows-1252"):
		writer.export(bad, str(target))
	assert target.read_bytes() == b"original"


# --- validation -------------------------------------------------------------------------------


@pytest.mark.parametrize(
	"bad",
	["13/2026", "00/2026", "9/2026", "09/26", "09/2026\n", "09/١٢٣٤", "09/0001"],
)
def test_invalid_competence_rejected(bad: str) -> None:
	"""Invalid competence rejected."""
	with pytest.raises(ValidationError):
		_build("fic", dt_compt=bad)


@pytest.mark.parametrize("bad", ["31/02/2026", "5/10/2026", "05/10/0001", "05/10/2026\n"])
def test_invalid_generation_date_rejected(bad: str) -> None:
	"""Invalid generation date rejected."""
	with pytest.raises(ValidationError):
		_build("fic", dt_gerac_arq=bad)


@pytest.mark.parametrize(
	"bad", ["", " 00360305000104", "00360305000105", "123", "00360305000104\n"]
)
def test_invalid_administrator_cnpj_rejected(bad: str) -> None:
	"""Invalid administrator cnpj rejected."""
	with pytest.raises(ValidationError):
		_build("fcce", cnpj_adm=bad)


def test_masked_cnpj_accepted_and_written_bare() -> None:
	"""Masked cnpj accepted and written bare."""
	writer, doc = _build("fcce", cnpj_adm="00.360.305/0001-04")
	assert "<CNPJ_ADM>360305000104</CNPJ_ADM>" in writer.export(doc)


def test_wrong_cod_doc_rejected() -> None:
	"""Wrong cod doc rejected."""
	with pytest.raises(ValidationError):
		_build("fitvm", cod_doc=5)


def test_other_variants_block_rejected() -> None:
	"""A FITVM row (with its MERC_A_TERMO block) is not a valid FIC row."""
	with pytest.raises(ValidationError):
		InformeSinteticoFicDocument(header=_header(8), informs=[_fitvm_row()])


def test_missing_block_rejected() -> None:
	"""Missing block rejected."""
	row = _fitvm_row()
	del row["aplicacoes_pos_final"]["aplicacoes"]["debt"]
	with pytest.raises(ValidationError):
		_build("fitvm", [row])


def test_empty_informs_rejected() -> None:
	"""Empty informs rejected."""
	with pytest.raises(ValidationError):
		_build("fcce", [])


def test_duplicate_fund_rejected() -> None:
	"""Duplicate fund rejected."""
	with pytest.raises(ValidationError, match="more than one"):
		_build("fcce", [_fcce_row(), _fcce_row()])


@pytest.mark.parametrize("bad", [-1, 1.5, True, "7", None])
def test_non_negative_integer_fields_strict(bad: object) -> None:
	"""Non negative integer fields strict."""
	row = _fic_row()
	row["aplicacoes_pos_final"]["aplicacoes"]["cotas"] = bad
	with pytest.raises(ValidationError):
		_build("fic", [row])


def test_negative_quotist_count_rejected() -> None:
	"""Negative quotist count rejected."""
	row = _fic_row()
	row["aplicacoes_pos_final"]["outras"]["nr_tot_quotst_ult_dia_mes"] = -1
	with pytest.raises(ValidationError):
		_build("fic", [row])


@pytest.mark.parametrize("bad", [1.5, True, "abc", "NaN", "Infinity", "-0.5", None])
def test_quota_value_rejects_float_nonfinite_and_negative(bad: object) -> None:
	"""Quota value rejects float nonfinite and negative."""
	row = _fic_row()
	row["aplicacoes_pos_final"]["outras"]["vl_quota_ult_dia_mes"] = bad
	with pytest.raises(ValidationError):
		_build("fic", [row])


def test_quota_value_accepts_decimal_and_int() -> None:
	"""Quota value accepts decimal and int."""
	for value in (Decimal("2.999"), 3):
		row = _fic_row()
		row["aplicacoes_pos_final"]["outras"]["vl_quota_ult_dia_mes"] = value
		_build("fic", [row])


def test_unknown_field_rejected() -> None:
	"""Unknown field rejected."""
	row = _fic_row()
	row["extra"] = 1
	with pytest.raises(ValidationError):
		_build("fic", [row])


def test_submission_surface_exports_writers() -> None:
	"""Submission surface exports writers."""
	import filings_cvm.submission as sub

	assert list(sub.__all__) == sorted(sub.__all__)
	for name in (
		"InformeSinteticoFcce",
		"InformeSinteticoFitvm",
		"InformeSinteticoFic",
		"InformeSinteticoOutros",
	):
		assert name in sub.__all__
